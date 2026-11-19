from types import SimpleNamespace
from unittest.mock import Mock

from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.value import ProjectID, StudentID
from autoprogen.usecase.main_window import MainWindowFacade


def _create_facade() -> tuple[MainWindowFacade, dict[str, Mock]]:
    """Mock依存関係を持つメイン画面Facadeを返す。"""
    dependencies = {
        "current_project_repository": Mock(),
        "student_folder_show_in_explorer_io": Mock(),
        "student_repository": Mock(),
        "stage_path_list_sub_service": Mock(),
        "student_stage_path_result_repository": Mock(),
        "student_mark_get_sub_service": Mock(),
        "project_settings_get_usecase": Mock(),
        "stage_error_text_formatter": Mock(),
        "student_source_code_get_usecase": Mock(),
        "global_settings_get_usecase": Mock(),
        "source_code_check_skip_approve_usecase": Mock(),
        "build_error_student_exclude_usecase": Mock(),
        "student_list_id_usecase": Mock(),
        "student_run_next_stage_usecase": Mock(),
        "student_stage_result_clear_service": Mock(),
        "app_version_repository": Mock(),
        "resource_usage_io": Mock(),
        "student_change_event_bus": Mock(),
        "task_manager": Mock(),
    }
    dependencies["project_settings_get_usecase"].execute.return_value = (
        ProjectSettings.create_default()
    )
    return MainWindowFacade(**dependencies), dependencies


def test_main_window_only_operations_are_owned_by_facade() -> None:
    """プロジェクト概要・学生名・提出フォルダ操作をFacadeが提供する。"""
    facade, dependencies = _create_facade()
    project = SimpleNamespace(
        project_id=ProjectID("facade-test"),
        target_id="4",
        zip_name="report.zip",
        open_at=Mock(),
    )
    dependencies["current_project_repository"].get.return_value = project
    student_id = StudentID("21D5109047B")
    student = SimpleNamespace(name="試験 太郎")
    dependencies["student_repository"].get.return_value = student

    summary = facade.get_project_summary()
    student_name = facade.get_student_name(student_id)
    facade.open_student_submission_folder(student_id)

    assert summary.project_id == project.project_id
    assert summary.target_number == 4
    assert student_name == "試験 太郎"
    dependencies["student_repository"].get.assert_called_once_with(student_id)
    dependencies[
        "student_folder_show_in_explorer_io"
    ].show_submission_folder.assert_called_once_with(student_id)


def test_facade_owns_main_window_operations_and_delegates_shared_usecase() -> None:
    """専用処理を直接実行し、共有するステージ処理だけUseCaseへ委譲する。"""
    facade, dependencies = _create_facade()
    student_id = StudentID("21D5109047B")
    stop_producer = Mock(return_value=False)
    dependencies["student_repository"].list.return_value = []
    dependencies["stage_path_list_sub_service"].execute.return_value = []
    dependencies["student_list_id_usecase"].execute.return_value = [student_id]
    dependencies["app_version_repository"].get.return_value.is_stable = False
    dependencies["resource_usage_io"].get_stat.return_value = SimpleNamespace(
        disk_read_count=10,
        disk_write_count=20,
        cpu_percent=30,
        memory=40 * (1 << 20),
    )

    assert facade.load_student_table(progress_callback=Mock()) == []
    assert facade.list_student_ids() == [student_id]
    assert not facade.is_app_version_stable()
    usage = facade.get_resource_usage()
    assert usage.disk_read_count == 10
    assert usage.disk_write_count == 20
    assert usage.cpu_percent == 30
    assert usage.memory_mega_bytes == 40
    facade.run_student_next_stage(
        student_id=student_id,
        stop_producer=stop_producer,
    )
    facade.clear_student_stage_results(
        student_id=student_id,
        stop_producer=stop_producer,
    )

    dependencies["student_run_next_stage_usecase"].execute.assert_called_once_with(
        student_id=student_id,
        stop_producer=stop_producer,
    )
    dependencies[
        "student_stage_result_clear_service"
    ].execute.assert_called_once_with(
        student_id=student_id,
    )


def test_student_error_operations_delegate_through_facade() -> None:
    """エラー処置の入口がFacadeに集約され、個別UseCaseへ委譲される。"""
    facade, dependencies = _create_facade()
    student_id = StudentID("21D5109047B")
    dependencies["task_manager"].is_empty.return_value = True
    dependencies["student_mark_get_sub_service"].execute.return_value.score = 75

    assert facade.can_perform_student_error_action()
    assert facade.get_student_mark_score(student_id) == 75
    facade.approve_source_code_check(student_id, "valid-hash")
    facade.exclude_build_error_student(student_id)

    dependencies["source_code_check_skip_approve_usecase"].execute.assert_called_once_with(
        student_id=student_id,
        expected_sha256="valid-hash",
    )
    dependencies["build_error_student_exclude_usecase"].execute.assert_called_once_with(
        student_id,
    )


def test_student_error_usecase_refusal_is_converted_by_facade() -> None:
    """UseCaseの想定内拒否をGUI側へ統一した例外として返す。"""
    import pytest

    from autoprogen.usecase.main_window import StudentErrorActionRefused
    from autoprogen.usecase.project_settings import BuildErrorStudentExcludeUseCaseError
    from autoprogen.usecase.source_code_check_skip import (
        SourceCodeCheckSkipApproveUseCaseError,
    )

    facade, dependencies = _create_facade()
    student_id = StudentID("21D5109047B")
    dependencies["build_error_student_exclude_usecase"].execute.side_effect = (
        BuildErrorStudentExcludeUseCaseError("提出フォルダが変更されました")
    )
    dependencies["source_code_check_skip_approve_usecase"].execute.side_effect = (
        SourceCodeCheckSkipApproveUseCaseError("ソースコードが変更されました")
    )

    with pytest.raises(StudentErrorActionRefused, match="提出フォルダ"):
        facade.exclude_build_error_student(student_id)
    with pytest.raises(StudentErrorActionRefused, match="ソースコード"):
        facade.approve_source_code_check(student_id, "valid-hash")
