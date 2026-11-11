from collections.abc import Callable
from dataclasses import dataclass

from autoprogen.domain.model.stage import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student import Student
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.student_stage_path_result import StudentStagePathResult
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.student import StudentRepository
from autoprogen.infra.repository.student_stage_path_result import StudentStagePathResultRepository
from autoprogen.service.stage_path import StagePathListSubService
from autoprogen.service.student_mark import StudentMarkGetSubService
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
    StudentErrorCellDataTextEntry,
    StudentIDCellData,
    StudentNameCellData,
    StudentStageStateCellData,
    StudentStageStateCellDataStageState,
)


@dataclass(frozen=True, slots=True)
class StudentTableRowSnapshot:
    """Qtオブジェクトを含まない、学生テーブル一行分の表示用データ。"""

    student_id: StudentID  # 表示行と変更通知を対応付ける学生ID。
    id_cell: StudentIDCellData  # 学籍番号と提出フォルダへのリンク状態。
    name_cell: StudentNameCellData  # 学生名の表示内容。
    stage_cells: dict[type[AbstractStage], StudentStageStateCellData]  # 4種類のステージ表示状態。
    error_cell: StudentErrorCellData  # エラー欄の本文とツールチップの元データ。
    mark: StudentMark  # 点数欄の表示内容。未採点なら点数はNone。


class StudentTableLoadUseCase:
    """学生テーブルの全件または一行の表示データを共通処理で取得する。"""

    _STAGE_TYPES = (BuildStage, CompileStage, ExecuteStage, TestStage)

    def __init__(
            self,
            *,
            student_repo: StudentRepository,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_repo: StudentStagePathResultRepository,
            student_mark_get_sub_service: StudentMarkGetSubService,
    ) -> None:
        """名簿、ステージ構成、実行結果、採点結果の取得先を受け取る。"""
        self._student_repo = student_repo
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_path_result_repo = student_stage_path_result_repo
        self._student_mark_get_sub_service = student_mark_get_sub_service

    def _load_row(
            self,
            student: Student,
            stage_paths: list[StagePath],
    ) -> StudentTableRowSnapshot:
        """学生一人分を取得し、各列でステージ結果を再利用する。"""
        student_id = student.student_id
        states_by_type = {stage_type: {} for stage_type in self._STAGE_TYPES}
        error_entries: list[StudentErrorCellDataTextEntry] = []

        # 各パスを一度だけ読み、4つのステージ欄とエラー欄の両方へ反映する。
        for stage_path in stage_paths:
            stage_result: StudentStagePathResult = self._student_stage_path_result_repo.get(
                student_id, stage_path,
            )
            for stage_type in self._STAGE_TYPES:
                result = stage_result.get_result_by_stage_type(stage_type)
                if result is None:
                    state = StudentStageStateCellDataStageState.UNFINISHED
                elif result.is_success:
                    state = StudentStageStateCellDataStageState.FINISHED_SUCCESS
                else:
                    state = StudentStageStateCellDataStageState.FINISHED_FAILURE
                states_by_type[stage_type][stage_path] = state

            summary = stage_result.last_stage_main_reason or ""
            detail = stage_result.last_stage_detailed_reason or ""
            if summary or detail:
                error_entries.append(StudentErrorCellDataTextEntry(summary, detail))

        return StudentTableRowSnapshot(
            student_id=student_id,
            id_cell=StudentIDCellData(
                student_id=student_id,
                student_number=str(student_id),
                is_submission_folder_link_alive=student.is_submitted,
            ),
            name_cell=StudentNameCellData(student_id=student_id, student_name=student.name),
            stage_cells={
                stage_type: StudentStageStateCellData(
                    student_id=student_id,
                    stage_type=stage_type,
                    states=states_by_type[stage_type],
                )
                for stage_type in self._STAGE_TYPES
            },
            error_cell=StudentErrorCellData(student_id=student_id, text_entries=error_entries),
            mark=self._student_mark_get_sub_service.execute(student_id),
        )

    def execute(
            self,
            *,
            progress_callback: Callable[[str], None],
    ) -> list[StudentTableRowSnapshot]:
        """全学生の表示用データを読み込み、進捗をメッセージで通知する。"""
        students = self._student_repo.list()
        stage_paths = self._stage_path_list_sub_service.execute()
        total = len(students)
        rows = []
        progress_callback(f"学生の表示データを読み込み中... 0/{total}")

        for index, student in enumerate(students, start=1):
            rows.append(self._load_row(student, stage_paths))
            if index == total or index % 10 == 0:
                progress_callback(f"学生の表示データを読み込み中... {index}/{total}")

        return rows

    def execute_row(self, student_id: StudentID) -> StudentTableRowSnapshot:
        """変更された学生一人の表示データを全件ロードと同じ方法で取得する。"""
        student = self._student_repo.get(student_id)
        stage_paths = self._stage_path_list_sub_service.execute()
        return self._load_row(student, stage_paths)
