"""プロジェクト設定の保存通知と採点除外追加を検証する。"""

from unittest.mock import Mock, call

import pytest

from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.project_settings import (
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
