from collections.abc import Callable
from dataclasses import dataclass

from autoprogen.domain.error import StopTask
from autoprogen.domain.model.stage import (
    AbstractStage,
    BuildStage,
    CompileStage,
    ExecuteStage,
    TestStage,
)
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student import Student
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.student_stage_path_result import StudentStagePathResult
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.io.resource_usage import ResourceUsageIO
from autoprogen.infra.io.student_folder_show_in_explorer import (
    StudentFolderShowInExplorerIO,
)
from autoprogen.infra.repository.app_version import AppVersionRepository
from autoprogen.infra.repository.current_project import CurrentProjectRepository
from autoprogen.infra.repository.student import StudentRepository
from autoprogen.infra.repository.student_stage_path_result import (
    StudentStagePathResultRepository,
)
from autoprogen.infra.task.manager import TaskManager
from autoprogen.service.stage_error_text import StageErrorTextFormatter
from autoprogen.service.stage_path import StagePathListSubService
from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.service.student_mark import StudentMarkGetSubService
from autoprogen.service.student_stage_path_result import StudentStageResultClearService
from autoprogen.usecase.dto.project import NormalProjectSummary
from autoprogen.usecase.dto.resource_usage import ResourceUsageGetResult
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
    StudentErrorCellDataTextEntry,
    StudentIDCellData,
    StudentNameCellData,
    StudentStageStateCellData,
    StudentStageStateCellDataStageState,
)
from autoprogen.usecase.student import StudentListIDUseCase
from autoprogen.usecase.student_mark import StudentMarkGetUseCase, StudentMarkPutUseCase
from autoprogen.usecase.student_run_next_stage import StudentRunNextStageUseCase


@dataclass(frozen=True, slots=True)
class StudentTableRowSnapshot:
    """Qtオブジェクトを含まない、学生テーブル一行分の表示用データ。"""

    student_id: StudentID  # 表示行と変更通知を対応付ける学生ID。
    id_cell: StudentIDCellData  # 学籍番号と提出フォルダへのリンク状態。
    name_cell: StudentNameCellData  # 学生名の表示内容。
    stage_cells: dict[type[AbstractStage], StudentStageStateCellData]  # ステージ表示状態。
    error_cell: StudentErrorCellData  # エラー欄の本文とツールチップの元データ。
    mark: StudentMark  # 点数欄の表示内容。未採点なら点数はNone。


class MainWindowFacade:
    """メイン画面と配下Widgetが必要とする操作を一つの窓口にまとめる。"""

    _STAGE_TYPES = (BuildStage, CompileStage, ExecuteStage, TestStage)

    def __init__(
            self,
            *,
            current_project_repository: CurrentProjectRepository,
            student_folder_show_in_explorer_io: StudentFolderShowInExplorerIO,
            student_repository: StudentRepository,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_repository: StudentStagePathResultRepository,
            student_mark_get_sub_service: StudentMarkGetSubService,
            stage_error_text_formatter: StageErrorTextFormatter,
            student_mark_get_usecase: StudentMarkGetUseCase,
            student_mark_put_usecase: StudentMarkPutUseCase,
            student_list_id_usecase: StudentListIDUseCase,
            student_run_next_stage_usecase: StudentRunNextStageUseCase,
            student_stage_result_clear_service: StudentStageResultClearService,
            app_version_repository: AppVersionRepository,
            resource_usage_io: ResourceUsageIO,
            student_change_event_bus: StudentChangeEventBus,
            task_manager: TaskManager,
    ) -> None:
        """メイン画面専用処理の依存先と共有UseCaseを受け取る。"""
        self._current_project_repository = current_project_repository
        self._student_folder_show_in_explorer_io = student_folder_show_in_explorer_io
        self._student_repository = student_repository
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_path_result_repository = (
            student_stage_path_result_repository
        )
        self._student_mark_get_sub_service = student_mark_get_sub_service
        self._stage_error_text_formatter = stage_error_text_formatter
        self._student_mark_get_usecase = student_mark_get_usecase
        self._student_mark_put_usecase = student_mark_put_usecase
        self._student_list_id_usecase = student_list_id_usecase
        self._student_run_next_stage_usecase = student_run_next_stage_usecase
        self._student_stage_result_clear_service = student_stage_result_clear_service
        self._app_version_repository = app_version_repository
        self._resource_usage_io = resource_usage_io
        self._student_change_event_bus = student_change_event_bus
        self._task_manager = task_manager

    @property
    def student_change_event_bus(self) -> StudentChangeEventBus:
        """学生テーブルの差分更新に使用する変更通知を返す。"""
        return self._student_change_event_bus

    @property
    def task_manager(self) -> TaskManager:
        """メイン画面で実行する学生タスクの管理オブジェクトを返す。"""
        return self._task_manager

    def get_project_summary(self) -> NormalProjectSummary:
        """現在のプロジェクトをメイン画面用の概要へ変換して返す。"""
        project = self._current_project_repository.get()
        return NormalProjectSummary(
            project_id=project.project_id,
            target_number=int(project.target_id),
            zip_name=project.zip_name,
            open_at=project.open_at,
        )

    def _load_student_table_row(
            self,
            student: Student,
            stage_paths: list[StagePath],
    ) -> StudentTableRowSnapshot:
        """学生一人分を取得し、各列でステージ結果を再利用する。"""
        student_id = student.student_id
        states_by_type = {stage_type: {} for stage_type in self._STAGE_TYPES}
        error_entries: list[StudentErrorCellDataTextEntry] = []

        # 各パスを一度だけ読み、ステージ欄とエラー欄の両方へ反映する。
        for stage_path in stage_paths:
            stage_result: StudentStagePathResult = (
                self._student_stage_path_result_repository.get(
                    student_id,
                    stage_path,
                )
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

            last_result = stage_result.last_stage_result
            if last_result is not None and not last_result.is_success:
                # 失敗結果がエラーを持つモデル契約としてOptionalの型を絞り込む。
                assert last_result.error is not None
                error_entries.append(StudentErrorCellDataTextEntry(
                    summary_text=self._stage_error_text_formatter.format_summary(
                        last_result.error,
                    ),
                    detailed_text=self._stage_error_text_formatter.format_detail(
                        last_result,
                    ),
                    error=last_result.error,
                ))

        return StudentTableRowSnapshot(
            student_id=student_id,
            id_cell=StudentIDCellData(
                student_id=student_id,
                student_number=str(student_id),
                is_submission_folder_link_alive=student.is_submitted,
            ),
            name_cell=StudentNameCellData(
                student_id=student_id,
                student_name=student.name,
            ),
            stage_cells={
                stage_type: StudentStageStateCellData(
                    student_id=student_id,
                    stage_type=stage_type,
                    states=states_by_type[stage_type],
                )
                for stage_type in self._STAGE_TYPES
            },
            error_cell=StudentErrorCellData(
                student_id=student_id,
                text_entries=error_entries,
            ),
            mark=self._student_mark_get_sub_service.execute(student_id),
        )

    def load_student_table(
            self,
            *,
            progress_callback: Callable[[str], None],
    ) -> list[StudentTableRowSnapshot]:
        """全学生の表示データを読み込み、進捗を通知する。"""
        students = self._student_repository.list()
        stage_paths = self._stage_path_list_sub_service.execute()
        total = len(students)
        rows = []
        progress_callback(f"学生の表示データを読み込み中... 0/{total}")

        for index, student in enumerate(students, start=1):
            rows.append(self._load_student_table_row(student, stage_paths))
            if index == total or index % 10 == 0:
                progress_callback(
                    f"学生の表示データを読み込み中... {index}/{total}"
                )
        return rows

    def load_student_table_row(
            self,
            student_id: StudentID,
    ) -> StudentTableRowSnapshot:
        """変更された学生一人の表示データを読み込む。"""
        student = self._student_repository.get(student_id)
        stage_paths = self._stage_path_list_sub_service.execute()
        return self._load_student_table_row(student, stage_paths)

    def open_student_submission_folder(self, student_id: StudentID) -> None:
        """選択学生の提出フォルダをエクスプローラーで開く。"""
        self._student_folder_show_in_explorer_io.show_submission_folder(student_id)

    def get_student_mark(self, student_id: StudentID) -> StudentMark:
        """共有UseCaseを利用して学生の採点結果を返す。"""
        return self._student_mark_get_usecase.execute(student_id)

    def set_student_mark_confirmation(
            self,
            student_id: StudentID,
            confirmed: bool,
    ) -> None:
        """点数を維持したまま学生の確定状態を保存する。"""
        student_mark = self._student_mark_get_usecase.execute(student_id)
        student_mark.confirmed = confirmed
        self._student_mark_put_usecase.execute(student_mark)

    def clear_student_mark(self, student_id: StudentID) -> None:
        """学生の点数をクリアし、未確定の状態として保存する。"""
        student_mark = self._student_mark_get_usecase.execute(student_id)
        student_mark.score = None
        self._student_mark_put_usecase.execute(student_mark)

    def list_student_ids(self) -> list[StudentID]:
        """共有UseCaseを利用して表示順の学生IDを返す。"""
        return self._student_list_id_usecase.execute()

    def run_student_next_stage(
            self,
            *,
            student_id: StudentID,
            stop_producer: Callable[[], bool],
    ) -> None:
        """共有UseCaseを利用して学生の未完了ステージを実行する。"""
        self._student_run_next_stage_usecase.execute(
            student_id=student_id,
            stop_producer=stop_producer,
        )

    def clear_student_stage_results(
            self,
            *,
            student_id: StudentID,
            stop_producer: Callable[[], bool],
    ) -> None:
        """停止要求を確認して学生の全ステージ結果を削除する。"""
        if stop_producer():
            raise StopTask()
        self._student_stage_result_clear_service.execute(student_id=student_id)

    def is_app_version_stable(self) -> bool:
        """現在のアプリケーションが正式版かどうかを返す。"""
        return self._app_version_repository.get().is_stable

    def get_resource_usage(self) -> ResourceUsageGetResult:
        """現在のプロセスリソース使用量を表示用DTOとして返す。"""
        usage = self._resource_usage_io.get_stat()
        return ResourceUsageGetResult(
            disk_read_count=usage.disk_read_count,
            disk_write_count=usage.disk_write_count,
            cpu_percent=usage.cpu_percent,
            memory_mega_bytes=usage.memory // (1 << 20),
        )
