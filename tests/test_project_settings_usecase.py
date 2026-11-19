"""プロジェクト設定の保存通知と採点除外追加を検証する。"""

from pathlib import Path
from unittest.mock import Mock, call

import pytest

from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.student_stage_result import BuildStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.domain.error.stage.build import (
    MultipleSourceFilesError,
    SourceEncodingUnknownError,
    SourceFilenameMultipleNumbersError,
    SourceFilenameNoNumberError,
    SubmissionNotFoundError,
    SubmissionSourceNotFoundError,
)
from autoprogen.usecase.project_settings import (
    BuildErrorStudentExcludeUseCase,
    BuildErrorStudentExcludeUseCaseError,
    BulkGradingSkipAddUseCase,
    BulkGradingSkipAddUseCaseError,
    ProjectSettingsPutUseCase,
)


def _put_usecase(
        previous: ProjectSettings,
) -> tuple[ProjectSettingsPutUseCase, Mock, Mock]:
    """保存前設定を返すRepositoryと通知先を持つUseCaseを返す。"""
    repository = Mock()
    repository.get.return_value = previous
    event_bus = Mock()
    usecase = ProjectSettingsPutUseCase(
        project_settings_repo=repository,
        student_change_event_bus=event_bus,
    )
    return usecase, repository, event_bus


def test_put_notifies_only_changed_bulk_grading_skip_students() -> None:
    """採点除外の追加・解除で変化した学生だけを保存後に通知する。"""
    first = StudentID("00A0000000A")
    second = StudentID("00B0000000B")
    unchanged = StudentID("00C0000000C")
    previous = ProjectSettings.create_default()
    for student_id in (first, unchanged):
        previous = previous.with_bulk_grading_skip(student_id)
    updated = previous.without_bulk_grading_skip(first).with_bulk_grading_skip(second)
    usecase, repository, event_bus = _put_usecase(previous)

    usecase.execute(updated)

    repository.put.assert_called_once_with(updated)
    assert event_bus.notify.call_args_list == [call(first), call(second)]


def test_put_does_not_notify_when_bulk_grading_skips_are_unchanged() -> None:
    """採点除外以外の設定保存では学生変更を通知しない。"""
    previous = ProjectSettings.create_default()
    updated = previous.with_source_code_check_skip(
        student_id=StudentID("00A0000000A"),
        source_sha256="a" * 64,
    )
    usecase, _, event_bus = _put_usecase(previous)

    usecase.execute(updated)

    event_bus.notify.assert_not_called()


def test_put_does_not_notify_when_save_fails() -> None:
    """Repository保存に失敗した場合は通知せず例外を伝播する。"""
    student_id = StudentID("00A0000000A")
    previous = ProjectSettings.create_default()
    updated = previous.with_bulk_grading_skip(student_id)
    usecase, repository, event_bus = _put_usecase(previous)
    repository.put.side_effect = OSError("write failed")

    with pytest.raises(OSError, match="write failed"):
        usecase.execute(updated)

    event_bus.notify.assert_not_called()


@pytest.mark.parametrize("score", [0, 50])
def test_bulk_grading_skip_add_accepts_marked_student(score: int) -> None:
    """0点を含む採点済み学生を共通保存経路へ渡す。"""
    student_id = StudentID("00A0000000A")
    mark_get = Mock()
    mark_get.execute.return_value = StudentMark(student_id, score)
    settings_get = Mock()
    settings_get.execute.return_value = ProjectSettings.create_default()
    settings_put = Mock()
    usecase = BulkGradingSkipAddUseCase(
        student_mark_get_usecase=mark_get,
        project_settings_get_usecase=settings_get,
        project_settings_put_usecase=settings_put,
    )

    usecase.execute(student_id)

    saved = settings_put.execute.call_args.args[0]
    assert saved.bulk_grading_skips == frozenset({student_id})
    assert mark_get.execute.return_value.score == score


def test_bulk_grading_skip_add_rejects_unmarked_student() -> None:
    """未採点学生を拒否し、設定を取得・保存しない。"""
    student_id = StudentID("00A0000000A")
    mark_get = Mock()
    mark_get.execute.return_value = StudentMark(student_id, None)
    settings_get = Mock()
    settings_put = Mock()
    usecase = BulkGradingSkipAddUseCase(
        student_mark_get_usecase=mark_get,
        project_settings_get_usecase=settings_get,
        project_settings_put_usecase=settings_put,
    )

    with pytest.raises(BulkGradingSkipAddUseCaseError):
        usecase.execute(student_id)

    settings_get.execute.assert_not_called()
    settings_put.execute.assert_not_called()


BUILD_CHECKSUM = 1234


def _build_error_exclude_usecase(
        *,
        error: object = SubmissionNotFoundError(),
        task_empty: bool = True,
        current_checksum: int = BUILD_CHECKSUM,
        is_submitted: bool = False,
) -> tuple[BuildErrorStudentExcludeUseCase, dict[str, Mock]]:
    """BUILDエラー学生への処置に必要な依存をMock化して返す。"""
    dependencies = {
        "stage_paths": Mock(),
        "results": Mock(),
        "mark_put": Mock(),
        "skip_add": Mock(),
        "settings_get": Mock(),
        "task_manager": Mock(),
        "submission_exists": Mock(),
        "checksum": Mock(),
    }
    dependencies["stage_paths"].execute.return_value = [Mock()]
    stage_path_result = Mock()
    stage_path_result.get_result_by_stage_type.return_value = (
        BuildStudentStageResult.create_instance(
            student_id=StudentID("00A0000000A"),
            submission_folder_checksum=BUILD_CHECKSUM,
            error=error,
        )
    )
    dependencies["results"].get.return_value = stage_path_result
    dependencies["settings_get"].execute.return_value = ProjectSettings.create_default()
    dependencies["task_manager"].is_empty.return_value = task_empty
    dependencies["submission_exists"].execute.return_value = is_submitted
    dependencies["checksum"].execute.return_value = current_checksum
    usecase = BuildErrorStudentExcludeUseCase(
        stage_path_list_sub_service=dependencies["stage_paths"],
        student_stage_path_result_repository=dependencies["results"],
        student_mark_put_usecase=dependencies["mark_put"],
        bulk_grading_skip_add_usecase=dependencies["skip_add"],
        project_settings_get_usecase=dependencies["settings_get"],
        task_manager=dependencies["task_manager"],
        student_submission_exist_service=dependencies["submission_exists"],
        student_submission_get_checksum_service=dependencies["checksum"],
    )
    return usecase, dependencies


def test_not_submitted_exclude_saves_zero_before_adding_skip() -> None:
    """未提出学生は0点を保存してから一括採点除外へ追加する。"""
    student_id = StudentID("00A0000000A")
    usecase, dependencies = _build_error_exclude_usecase()

    usecase.execute(student_id)

    saved_mark = dependencies["mark_put"].execute.call_args.args[0]
    assert saved_mark.student_id == student_id
    assert saved_mark.score == 0
    dependencies["skip_add"].execute.assert_called_once_with(student_id)


@pytest.mark.parametrize("error", [
    SourceFilenameMultipleNumbersError(
        file_relative_path=Path("prog12.c"),
        numbers=("1", "2"),
    ),
    SourceFilenameNoNumberError(file_relative_path=Path("prog.c")),
    MultipleSourceFilesError(file_relative_paths=(Path("prog1.c"), Path("prog2.c"))),
    SubmissionSourceNotFoundError(),
    SourceEncodingUnknownError(file_relative_path=Path("prog1.c")),
])
def test_submission_file_exclude_saves_zero_and_adds_skip(error: object) -> None:
    """提出ファイルエラー5種は0点保存後に一括採点除外へ追加する。"""
    student_id = StudentID("00A0000000A")
    usecase, dependencies = _build_error_exclude_usecase(
        error=error,
        is_submitted=True,
    )

    usecase.execute(student_id)

    saved_mark = dependencies["mark_put"].execute.call_args.args[0]
    assert saved_mark.student_id == student_id
    assert saved_mark.score == 0
    dependencies["skip_add"].execute.assert_called_once_with(student_id)


def test_submission_file_exclude_rejects_changed_submission_folder() -> None:
    """BUILD後に提出フォルダが変わった場合は0点・除外処置を拒否する。"""
    usecase, dependencies = _build_error_exclude_usecase(
        error=SubmissionSourceNotFoundError(),
        is_submitted=True,
        current_checksum=BUILD_CHECKSUM + 1,
    )

    with pytest.raises(BuildErrorStudentExcludeUseCaseError, match="再実行"):
        usecase.execute(StudentID("00A0000000A"))

    dependencies["mark_put"].execute.assert_not_called()
    dependencies["skip_add"].execute.assert_not_called()


def test_not_submitted_exclude_rejects_changed_submission_state() -> None:
    """未提出エラー後に提出済みへ変わった学生への処置を拒否する。"""
    usecase, dependencies = _build_error_exclude_usecase(
        is_submitted=True,
    )

    with pytest.raises(BuildErrorStudentExcludeUseCaseError, match="再実行"):
        usecase.execute(StudentID("00A0000000A"))

    dependencies["mark_put"].execute.assert_not_called()
    dependencies["skip_add"].execute.assert_not_called()


def test_build_error_exclude_rejects_while_task_is_running() -> None:
    """実行中はBUILDエラー学生の点数と設定を変更しない。"""
    usecase, dependencies = _build_error_exclude_usecase(
        task_empty=False,
    )

    with pytest.raises(BuildErrorStudentExcludeUseCaseError):
        usecase.execute(StudentID("00A0000000A"))

    dependencies["mark_put"].execute.assert_not_called()
    dependencies["skip_add"].execute.assert_not_called()


def test_not_submitted_exclude_reports_partial_save_when_setting_fails() -> None:
    """除外設定だけ失敗した場合は0点が保存済みであることを報告する。"""
    usecase, dependencies = _build_error_exclude_usecase()
    dependencies["skip_add"].execute.side_effect = OSError("settings write failed")

    with pytest.raises(BuildErrorStudentExcludeUseCaseError) as captured:
        usecase.execute(StudentID("00A0000000A"))

    assert captured.value.score_saved
    assert "0点は保存されました" in str(captured.value)


def test_not_submitted_exclude_does_not_add_skip_when_score_save_fails() -> None:
    """点数保存に失敗した場合は除外設定へ進まない。"""
    usecase, dependencies = _build_error_exclude_usecase()
    dependencies["mark_put"].execute.side_effect = OSError("database write failed")

    with pytest.raises(BuildErrorStudentExcludeUseCaseError) as captured:
        usecase.execute(StudentID("00A0000000A"))

    assert not captured.value.score_saved
    dependencies["skip_add"].execute.assert_not_called()
