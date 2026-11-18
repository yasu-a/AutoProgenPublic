"""ソースコード安全性チェックの許可UseCaseを検証する。"""

from unittest.mock import Mock

import pytest

from autoprogen.domain.error.stage.compile import SourceSafetyViolationError
from autoprogen.domain.model.project_settings import ProjectSettings, SourceCodeCheckSkip
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.source_code_check import SourceCodeCheckFinding
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.source_code_check_skip import (
    SourceCodeCheckSkipApproveUseCase,
    SourceCodeCheckSkipApproveUseCaseError,
)


STUDENT = StudentID("21D5109047B")
OTHER_STUDENT = StudentID("21D5109048C")
SOURCE = SourceCode(text='int main(void) { system("echo hello"); }')
SOURCE_SHA = SOURCE.calculate_sha256()


def _safety_error(source_sha256: str = SOURCE_SHA) -> SourceSafetyViolationError:
    """指定したソースSHAを持つ安全性チェックエラーを作る。"""
    return SourceSafetyViolationError(
        source_sha256=source_sha256,
        findings=(SourceCodeCheckFinding(
            line_number=1,
            group_id="process",
            check_id="system",
        ),),
    )


def _make_usecase(
        *,
        source_code: SourceCode | None = SOURCE,
        latest_error: Exception | None = None,
        settings: ProjectSettings | None = None,
        task_empty: bool = True,
) -> tuple[SourceCodeCheckSkipApproveUseCase, dict[str, Mock]]:
    """状態を指定したUseCaseと検証用の依存Mockを返す。"""
    dependencies = {
        "source_get": Mock(),
        "stage_paths": Mock(),
        "results": Mock(),
        "settings_get": Mock(),
        "settings_put": Mock(),
        "task_manager": Mock(),
    }
    dependencies["source_get"].execute.return_value = source_code
    dependencies["stage_paths"].execute.return_value = (Mock(),)
    stage_path_result = Mock()
    stage_path_result.last_stage_result.error = (
        latest_error if latest_error is not None else _safety_error()
    )
    dependencies["results"].get.return_value = stage_path_result
    dependencies["settings_get"].execute.return_value = (
        settings if settings is not None else ProjectSettings.create_default()
    )
    dependencies["task_manager"].is_empty.return_value = task_empty
    usecase = SourceCodeCheckSkipApproveUseCase(
        student_source_code_get_usecase=dependencies["source_get"],
        stage_path_list_sub_service=dependencies["stage_paths"],
        student_stage_path_result_repository=dependencies["results"],
        project_settings_get_usecase=dependencies["settings_get"],
        project_settings_put_usecase=dependencies["settings_put"],
        task_manager=dependencies["task_manager"],
    )
    return usecase, dependencies


def test_approve_adds_only_target_student_and_source() -> None:
    """対象学生と現在ソースの組だけを追加し、他の設定を保持する。"""
    other_skip = SourceCodeCheckSkip(OTHER_STUDENT, "a" * 64)
    initial = ProjectSettings.create_default()
    settings = ProjectSettings(
        suppressed_source_code_checks=initial.suppressed_source_code_checks,
        source_code_check_skips=frozenset({other_skip}),
        bulk_grading_skips=frozenset({OTHER_STUDENT}),
    )
    usecase, dependencies = _make_usecase(settings=settings)

    usecase.execute(student_id=STUDENT, expected_sha256=SOURCE_SHA)

    saved = dependencies["settings_put"].execute.call_args.args[0]
    assert SourceCodeCheckSkip(STUDENT, SOURCE_SHA) in saved.source_code_check_skips
    assert other_skip in saved.source_code_check_skips
    assert saved.suppressed_source_code_checks == settings.suppressed_source_code_checks
    assert saved.bulk_grading_skips == settings.bulk_grading_skips


def test_approve_does_not_save_duplicate_skip() -> None:
    """同じ学生とソースが許可済みなら設定を重複保存しない。"""
    skip = SourceCodeCheckSkip(STUDENT, SOURCE_SHA)
    initial = ProjectSettings.create_default()
    settings = ProjectSettings(
        suppressed_source_code_checks=initial.suppressed_source_code_checks,
        source_code_check_skips=frozenset({skip}),
        bulk_grading_skips=initial.bulk_grading_skips,
    )
    usecase, dependencies = _make_usecase(settings=settings)

    usecase.execute(student_id=STUDENT, expected_sha256=SOURCE_SHA)

    dependencies["settings_put"].execute.assert_not_called()


@pytest.mark.parametrize(
    "source_code,latest_error,task_empty,expected_sha256",
    [
        (SOURCE, _safety_error(), False, SOURCE_SHA),
        (SOURCE, ValueError("別のエラー"), True, SOURCE_SHA),
        (SOURCE, _safety_error("b" * 64), True, SOURCE_SHA),
        (SourceCode(text="changed"), _safety_error(), True, SOURCE_SHA),
        (None, _safety_error(), True, SOURCE_SHA),
        (SOURCE, _safety_error(), True, "invalid"),
    ],
)
def test_approve_rejects_invalid_current_state(
        source_code: SourceCode | None,
        latest_error: Exception,
        task_empty: bool,
        expected_sha256: str,
) -> None:
    """実行中やソース・最新エラーの不一致では設定を保存しない。"""
    usecase, dependencies = _make_usecase(
        source_code=source_code,
        latest_error=latest_error,
        task_empty=task_empty,
    )

    with pytest.raises(SourceCodeCheckSkipApproveUseCaseError):
        usecase.execute(
            student_id=STUDENT,
            expected_sha256=expected_sha256,
        )

    dependencies["settings_put"].execute.assert_not_called()


def test_approve_rechecks_task_state_before_saving() -> None:
    """検証中に実行が始まった場合は設定保存を中止する。"""
    usecase, dependencies = _make_usecase()
    dependencies["task_manager"].is_empty.side_effect = (True, False)

    with pytest.raises(SourceCodeCheckSkipApproveUseCaseError):
        usecase.execute(student_id=STUDENT, expected_sha256=SOURCE_SHA)

    dependencies["settings_put"].execute.assert_not_called()


def test_approve_propagates_settings_save_failure() -> None:
    """設定保存に失敗した場合は許可成功として扱わない。"""
    usecase, dependencies = _make_usecase()
    dependencies["settings_put"].execute.side_effect = OSError("write failed")

    with pytest.raises(OSError, match="write failed"):
        usecase.execute(student_id=STUDENT, expected_sha256=SOURCE_SHA)
