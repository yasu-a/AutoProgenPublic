from unittest.mock import Mock

import pytest

from autoprogen.domain.model.stage import BuildStage, CompileStage
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student import Student
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID, TestCaseID as CaseID
from autoprogen.usecase.student_table_load import StudentTableLoadUseCase
from autoprogen.usecase.dto.student_table_cell_data import StudentStageStateCellDataStageState


def test_load_reuses_each_stage_path_result_for_all_columns() -> None:
    """各パスの結果は学生一人につき一度だけ読み、複数列へ再利用する。"""
    student_id = StudentID("21D5109047B")
    student = Student(
        student_id=student_id,
        name="試験 太郎",
        name_en="Test Taro",
        email_address="test@example.com",
        submitted_at=None,
        num_submissions=1,
        submission_folder_name="submitted",
    )
    paths = StagePath.list_paths([CaseID("case1"), CaseID("case2")])
    student_repo = Mock()
    student_repo.list.return_value = [student]
    path_service = Mock()
    path_service.execute.return_value = paths
    result_repo = Mock()
    stage_results = [Mock(), Mock()]
    for result in stage_results:
        result.get_result_by_stage_type.side_effect = lambda stage_type: (
            Mock(is_success=True) if stage_type is BuildStage else None
        )
        result.last_stage_main_reason = None
        result.last_stage_detailed_reason = None
    result_repo.get.side_effect = stage_results
    mark_service = Mock()
    mark_service.execute.return_value = StudentMark(student_id=student_id, score=75)
    progress: list[str] = []
    usecase = StudentTableLoadUseCase(
        student_repo=student_repo,
        stage_path_list_sub_service=path_service,
        student_stage_path_result_repo=result_repo,
        student_mark_get_sub_service=mark_service,
    )

    rows = usecase.execute(progress_callback=progress.append)

    assert len(rows) == 1
    assert rows[0].id_cell.is_submission_folder_link_alive
    assert rows[0].name_cell.student_name == "試験 太郎"
    assert rows[0].mark.score == 75
    assert list(rows[0].stage_cells[BuildStage].states.values()) == [
        StudentStageStateCellDataStageState.FINISHED_SUCCESS,
        StudentStageStateCellDataStageState.FINISHED_SUCCESS,
    ]
    assert list(rows[0].stage_cells[CompileStage].states.values()) == [
        StudentStageStateCellDataStageState.UNFINISHED,
        StudentStageStateCellDataStageState.UNFINISHED,
    ]
    assert result_repo.get.call_count == len(paths)
    mark_service.execute.assert_called_once_with(student_id)
    assert progress == [
        "学生の表示データを読み込み中... 0/1",
        "学生の表示データを読み込み中... 1/1",
    ]


def test_load_empty_student_list() -> None:
    """学生がいないプロジェクトでも空のロード結果を返す。"""
    student_repo = Mock()
    student_repo.list.return_value = []
    usecase = StudentTableLoadUseCase(
        student_repo=student_repo,
        stage_path_list_sub_service=Mock(),
        student_stage_path_result_repo=Mock(),
        student_mark_get_sub_service=Mock(),
    )
    progress: list[str] = []

    assert usecase.execute(progress_callback=progress.append) == []
    assert progress == ["学生の表示データを読み込み中... 0/0"]


def test_load_one_student_reuses_row_builder_without_listing_students() -> None:
    """変更通知時は学生一人を取得し、全件ロードと同じ行データを作る。"""
    student_id = StudentID("21D5109047B")
    student = Student(
        student_id=student_id,
        name="試験 太郎",
        name_en="Test Taro",
        email_address="test@example.com",
        submitted_at=None,
        num_submissions=1,
        submission_folder_name="submitted",
    )
    student_repo = Mock()
    student_repo.list.return_value = [student]
    student_repo.get.return_value = student
    path_service = Mock()
    path_service.execute.return_value = []
    mark_service = Mock()
    mark_service.execute.return_value = StudentMark(student_id=student_id, score=75)
    usecase = StudentTableLoadUseCase(
        student_repo=student_repo,
        stage_path_list_sub_service=path_service,
        student_stage_path_result_repo=Mock(),
        student_mark_get_sub_service=mark_service,
    )

    expected = usecase.execute(progress_callback=lambda _: None)[0]
    student_repo.reset_mock()
    actual = usecase.execute_row(student_id)

    assert actual == expected
    student_repo.get.assert_called_once_with(student_id)
    student_repo.list.assert_not_called()


def test_load_initialized_project_from_archive(initialized_project_from_archive) -> None:
    """実際に初期化したプロジェクトの全学生を読み込める。"""
    project_container = initialized_project_from_archive(
        archive_name="report-test-1",
        project_name="student_table_load_test",
    )
    progress: list[str] = []

    rows = project_container.student_table_load_usecase.execute(
        progress_callback=progress.append,
    )

    assert [row.student_id for row in rows] == project_container.student_list_id_usecase.execute()
    assert progress[-1].endswith(f"{len(rows)}/{len(rows)}")
