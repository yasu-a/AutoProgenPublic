"""ステージの再試行・ロールバック動作を固定する。"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from autoprogen.domain.error import StopTask
from autoprogen.domain.error.stage.build import SubmissionNotFoundError
from autoprogen.domain.error.stage.compile import CompilerDiagnosticError
from autoprogen.domain.error.stage.execute import ExecutionTimeoutError
from autoprogen.domain.error.stage.test import OutputMatchingError
from autoprogen.domain.model.output_file import OutputFileCollection
from autoprogen.domain.model.project_settings import (
    ProjectSettings,
    SourceCodeCheckIdentifier,
    SourceCodeCheckSkip,
    SourceCodeCheckSuppressions,
)
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.stage import (
    BuildStage,
    CompileStage,
    ExecuteStage,
    TestStage as StageTest,
)
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student_stage_result import (
    BuildFailureStudentStageResult,
    BuildSuccessStudentStageResult,
    CompileFailureStudentStageResult,
    CompileSuccessStudentStageResult,
    ExecuteFailureStudentStageResult,
    ExecuteSuccessStudentStageResult,
    TestFailureStudentStageResult as StageTestFailureResult,
    TestResultOutputFileCollection as StageTestOutputCollection,
    TestSuccessStudentStageResult as StageTestSuccessResult,
)
from autoprogen.domain.model.value import StudentID, TestCaseID as CaseID
from autoprogen.infra.io.project_database import ProjectDatabaseIO
from autoprogen.infra.repository.student_stage_path_result import StudentStagePathResultRepository
from autoprogen.service.student_stage_path_result import (
    StudentPutStageResultService,
    StudentStagePathResultCheckRollbackService,
    StudentStagePathResultGetService,
    StudentStagePathResultPutService,
)
from autoprogen.usecase.student_run_next_stage import StudentRunNextStageUseCase


STUDENT = StudentID("20A1234567B")
CASE_A = CaseID("case-a")
CASE_B = CaseID("case-b")
EXECUTE_MTIME = datetime(2026, 11, 1, 12, 0, 0)
TEST_MTIME = datetime(2026, 11, 2, 12, 0, 0)
CHECKSUM = 100
SOURCE_CODE = SourceCode(text="int main(void) { return 0; }\n")
SUPPRESSED_CHECK = SourceCodeCheckIdentifier(
    group_id="process",
    check_id="system",
)
PROJECT_SETTINGS = ProjectSettings(
    suppressed_source_code_checks=SourceCodeCheckSuppressions({SUPPRESSED_CHECK}),
    source_code_check_skips=frozenset(),
)


@pytest.fixture
def repository(tmp_path):
    """実際のSQLiteで学生1人分のステージ結果を扱う。"""
    database = ProjectDatabaseIO(database_path=tmp_path / "retry-rollback.sqlite3")
    with database.connect() as connection:
        connection.execute("CREATE TABLE student (student_id TEXT PRIMARY KEY)")
        connection.execute("INSERT INTO student (student_id) VALUES (?)", (str(STUDENT),))
        connection.commit()
    return StudentStagePathResultRepository(project_database_io=database)


def _path(case_id: CaseID = CASE_A) -> StagePath:
    """テストケースに対応する経路を返す。"""
    return StagePath.list_paths([case_id])[0]


def _success_results(
        case_id: CaseID = CASE_A,
        *,
        suppressed_source_code_checks: SourceCodeCheckSuppressions = (
            PROJECT_SETTINGS.suppressed_source_code_checks
        ),
        source_code_check_skipped: bool = False,
):
    """成功した4ステージの結果を順番に生成する。"""
    return (
        BuildSuccessStudentStageResult.create_instance(
            student_id=STUDENT, submission_folder_checksum=CHECKSUM,
        ),
        CompileSuccessStudentStageResult.create_instance(
            student_id=STUDENT, output="compile output\n",
            suppressed_source_code_checks=suppressed_source_code_checks,
            source_code_check_skipped=source_code_check_skipped,
        ),
        ExecuteSuccessStudentStageResult.create_instance(
            student_id=STUDENT, testcase_id=case_id,
            execute_config_mtime=EXECUTE_MTIME,
            output_file_collection=OutputFileCollection(),
        ),
        StageTestSuccessResult.create_instance(
            student_id=STUDENT, testcase_id=case_id,
            test_config_mtime=TEST_MTIME,
            test_result_output_file_collection=StageTestOutputCollection(),
        ),
    )


def _failure_result(stage_index: int, case_id: CaseID = CASE_A):
    """各ステージに対応する失敗結果を作る。"""
    return (
        BuildFailureStudentStageResult.create_instance(
            student_id=STUDENT,
            error=SubmissionNotFoundError(),
        ),
        CompileFailureStudentStageResult.create_instance(
            student_id=STUDENT,
            error=CompilerDiagnosticError(),
            output="compiler stderr\n",
        ),
        ExecuteFailureStudentStageResult.create_instance(
            student_id=STUDENT,
            testcase_id=case_id,
            error=ExecutionTimeoutError(),
        ),
        StageTestFailureResult.create_instance(
            student_id=STUDENT,
            testcase_id=case_id,
            error=OutputMatchingError(detail="TEST失敗"),
        ),
    )[stage_index]


def _seed(
        repository,
        case_id: CaseID,
        *,
        failure_stage_index: int | None = None,
        source_code_check_skipped: bool = False,
):
    """成功または指定箇所で失敗するステージの履歴をDBへ保存する。"""
    aggregate = repository.get(STUDENT, _path(case_id))
    for index, success in enumerate(_success_results(
            case_id,
            source_code_check_skipped=source_code_check_skipped,
    )):
        if failure_stage_index is not None and index > failure_stage_index:
            break
        if failure_stage_index == index:
            aggregate.put_result(_failure_result(index, case_id))
        else:
            aggregate.put_result(success)
    repository.put(aggregate)


def _rollback_checker(
        *,
        checksum=CHECKSUM,
        project_settings: ProjectSettings = PROJECT_SETTINGS,
        source_code: SourceCode = SOURCE_CODE,
        execute_mtime=EXECUTE_MTIME,
        test_mtime=TEST_MTIME,
):
    """比較用の値を指定した本物のロールバック判定Serviceを作る。"""
    source = Mock()
    source.execute.return_value = checksum
    settings = Mock()
    settings.get.return_value = project_settings
    dynamic_source = Mock()
    dynamic_source.execute.return_value = source_code
    execute_config = Mock()
    execute_config.execute.return_value = execute_mtime
    test_config = Mock()
    test_config.execute.return_value = test_mtime
    checker = StudentStagePathResultCheckRollbackService(
        student_submission_get_checksum_service=source,
        project_settings_repository=settings,
        student_dynamic_get_source_code_service=dynamic_source,
        testcase_config_get_execute_config_mtime_service=execute_config,
        testcase_config_get_test_config_mtime_service=test_config,
    )
    return checker, source, settings, dynamic_source, execute_config, test_config


def _make_runner(repository, paths, rollback_checker):
    """ステージ実行だけをMock化し、実Repositoryを使うUseCaseを作る。"""
    get_service = StudentStagePathResultGetService(
        student_stage_path_result_repo=repository,
    )
    put_service = StudentStagePathResultPutService(
        student_stage_path_result_repo=repository,
        student_change_event_bus=Mock(),
    )
    writer = StudentPutStageResultService(
        student_stage_path_result_repo=repository,
        student_stage_path_result_put_service=put_service,
    )
    listing = Mock()
    listing.execute.return_value = paths
    runners = [Mock() for _ in range(4)]
    usecase = StudentRunNextStageUseCase(
        stage_path_list_sub_service=listing,
        student_stage_path_result_get_service=get_service,
        student_stage_path_result_repo=repository,
        student_stage_path_result_put_service=put_service,
        student_run_build_stage_usecase=runners[0],
        student_run_compile_stage_usecase=runners[1],
        student_run_execute_stage_usecase=runners[2],
        student_run_test_stage_usecase=runners[3],
        student_stage_path_result_check_rollback_service=rollback_checker,
    )
    return usecase, writer, runners


def _stop_on_second_check():
    """最初の1ステップ後、次の反復の直前に停止する。"""
    count = 0

    def should_stop() -> bool:
        """二度目以降の停止確認に応答する。"""
        nonlocal count
        count += 1
        return count >= 2

    return should_stop


@pytest.mark.parametrize(
    ("checksum", "execute_mtime", "test_mtime", "expected"),
    [
        (101, datetime(2026, 12, 1), datetime(2026, 12, 2), BuildStage),
        (CHECKSUM, datetime(2026, 12, 1), datetime(2026, 12, 2), ExecuteStage),
        (CHECKSUM, EXECUTE_MTIME, datetime(2026, 12, 2), StageTest),
        (CHECKSUM, EXECUTE_MTIME, TEST_MTIME, None),
    ],
    ids=["build-priority", "execute-priority", "test", "unchanged"],
)
def test_rollback_detector_returns_first_changed_stage(
    repository, checksum, execute_mtime, test_mtime, expected,
) -> None:
    """提出物・実行設定・テスト設定の変更を前段優先で判定する。"""
    _seed(repository, CASE_A)
    checker, _, _, _, _, _ = _rollback_checker(
        checksum=checksum, execute_mtime=execute_mtime, test_mtime=test_mtime,
    )
    assert checker.execute(
        stage_path_result=repository.get(STUDENT, _path()),
        student_id=STUDENT,
    ) is expected


def test_compile_policy_change_rolls_back(repository) -> None:
    """抑制規則が変わった場合はCOMPILEへ戻す。"""
    _seed(repository, CASE_A)
    changed_settings = ProjectSettings(
        suppressed_source_code_checks=SourceCodeCheckSuppressions(),
        source_code_check_skips=frozenset(),
    )
    checker, _, settings, dynamic_source, _, _ = _rollback_checker(
        project_settings=changed_settings,
    )

    rollback_stage = checker.execute(
        stage_path_result=repository.get(STUDENT, _path()),
        student_id=STUDENT,
    )

    assert rollback_stage is CompileStage
    settings.get.assert_called_once_with()
    dynamic_source.execute.assert_called_once_with(STUDENT)


def test_missing_dynamic_source_rolls_back_to_build(repository) -> None:
    """COMPILE成功後にソースが欠損していた場合はBUILDへ戻す。"""
    _seed(repository, CASE_A)
    checker, _, _, dynamic_source, _, _ = _rollback_checker()
    dynamic_source.execute.side_effect = FileNotFoundError()

    assert checker.execute(
        stage_path_result=repository.get(STUDENT, _path()),
        student_id=STUDENT,
    ) is BuildStage


@pytest.mark.parametrize(
    ("stored_skip", "current_skip"),
    [(False, True), (True, False)],
    ids=["approval-added", "approval-removed"],
)
def test_compile_skip_change_rolls_back(
        repository,
        stored_skip: bool,
        current_skip: bool,
) -> None:
    """対象学生・対象ソースへの省略許可変更ではCOMPILEへ戻す。"""
    _seed(repository, CASE_A, source_code_check_skipped=stored_skip)
    skip = SourceCodeCheckSkip(
        student_id=STUDENT,
        source_sha256=SOURCE_CODE.calculate_sha256(),
    )
    settings = ProjectSettings(
        suppressed_source_code_checks=PROJECT_SETTINGS.suppressed_source_code_checks,
        source_code_check_skips=frozenset({skip}) if current_skip else frozenset(),
    )
    checker, _, _, _, _, _ = _rollback_checker(project_settings=settings)

    assert checker.execute(
        stage_path_result=repository.get(STUDENT, _path()),
        student_id=STUDENT,
    ) is CompileStage


@pytest.mark.parametrize(
    "unrelated_skip",
    [
        SourceCodeCheckSkip(
            student_id=StudentID("20A7654321B"),
            source_sha256=SOURCE_CODE.calculate_sha256(),
        ),
        SourceCodeCheckSkip(
            student_id=STUDENT,
            source_sha256=SourceCode(text="different source\n").calculate_sha256(),
        ),
    ],
    ids=["other-student", "other-source"],
)
def test_unrelated_skip_does_not_roll_back(repository, unrelated_skip) -> None:
    """他学生または別ソースへの省略許可は現在のCOMPILE結果に影響しない。"""
    _seed(repository, CASE_A)
    settings = ProjectSettings(
        suppressed_source_code_checks=PROJECT_SETTINGS.suppressed_source_code_checks,
        source_code_check_skips=frozenset({unrelated_skip}),
    )
    checker, _, _, _, _, _ = _rollback_checker(project_settings=settings)

    assert checker.execute(
        stage_path_result=repository.get(STUDENT, _path()),
        student_id=STUDENT,
    ) is None


def test_build_change_takes_priority_over_compile_change(repository) -> None:
    """BUILDが変わった場合はCOMPILE設定を読み込まずBUILDへ戻す。"""
    _seed(repository, CASE_A)
    changed_settings = ProjectSettings(
        suppressed_source_code_checks=SourceCodeCheckSuppressions(),
        source_code_check_skips=frozenset(),
    )
    checker, _, settings, dynamic_source, _, _ = _rollback_checker(
        checksum=CHECKSUM + 1,
        project_settings=changed_settings,
    )

    assert checker.execute(
        stage_path_result=repository.get(STUDENT, _path()),
        student_id=STUDENT,
    ) is BuildStage
    settings.get.assert_not_called()
    dynamic_source.execute.assert_not_called()


@pytest.mark.parametrize("compile_state", ["unfinished", "failed"])
def test_compile_settings_are_not_compared_without_compile_success(
        repository,
        compile_state: str,
) -> None:
    """COMPILEが未実行または失敗なら安全性設定を比較しない。"""
    if compile_state == "failed":
        _seed(repository, CASE_A, failure_stage_index=1)
    else:
        aggregate = repository.get(STUDENT, _path())
        aggregate.put_result(_success_results()[0])
        repository.put(aggregate)
    checker, _, settings, dynamic_source, _, _ = _rollback_checker()

    assert checker.execute(
        stage_path_result=repository.get(STUDENT, _path()),
        student_id=STUDENT,
    ) is None
    settings.get.assert_not_called()
    dynamic_source.execute.assert_not_called()


def test_failed_stage_is_not_treated_as_success_for_rollback(repository) -> None:
    """失敗結果の設定時刻などは比較せず、ロールバック対象にしない。"""
    _seed(repository, CASE_A, failure_stage_index=2)
    checker, source, settings, dynamic_source, execute_config, test_config \
        = _rollback_checker()
    assert checker.execute(
        stage_path_result=repository.get(STUDENT, _path()),
        student_id=STUDENT,
    ) is None
    source.execute.assert_called_once_with(student_id=STUDENT)
    settings.get.assert_called_once_with()
    dynamic_source.execute.assert_called_once_with(STUDENT)
    execute_config.execute.assert_not_called()
    test_config.execute.assert_not_called()


@pytest.mark.parametrize("failed_index", range(4), ids=["build", "compile", "execute", "test"])
def test_failed_stage_is_retried_on_next_invocation(repository, failed_index: int) -> None:
    """失敗したステージを次の処理で再度実行し、成功へ更新できる。"""
    _seed(repository, CASE_A, failure_stage_index=failed_index)
    rollback = Mock()
    rollback.execute.return_value = None
    usecase, writer, runners = _make_runner(repository, [_path()], rollback)
    result_to_save = _success_results()[failed_index]

    def save_success(*, student_id, stage_path):
        """Mock実行時に実Repositoryへ成功結果を保存する。"""
        assert student_id == STUDENT
        assert stage_path == _path()
        writer.execute(stage_path=stage_path, result=result_to_save)

    runners[failed_index].execute.side_effect = save_success
    with pytest.raises(StopTask):
        usecase.execute(student_id=STUDENT, stop_producer=_stop_on_second_check())

    runners[failed_index].execute.assert_called_once_with(
        student_id=STUDENT, stage_path=_path(),
    )
    for index, runner in enumerate(runners):
        if index != failed_index:
            runner.execute.assert_not_called()
    restored = repository.get(STUDENT, _path()).get_result(_path()[failed_index])
    assert type(restored) is type(result_to_save)
    assert restored.is_success is True


def test_failed_stage_without_progress_does_not_loop_forever(repository) -> None:
    """ステージ結果が変化しなければ、その呼び出し内では再実行し続けない。"""
    _seed(repository, CASE_A, failure_stage_index=0)
    rollback = Mock()
    rollback.execute.return_value = None
    usecase, _, runners = _make_runner(repository, [_path()], rollback)
    usecase.execute(student_id=STUDENT, stop_producer=lambda: False)
    runners[0].execute.assert_called_once()
    assert isinstance(
        repository.get(STUDENT, _path()).last_stage_result.error,
        SubmissionNotFoundError,
    )


def test_unexpected_exception_propagates_without_overwriting_failure(repository) -> None:
    """ステージ実行で生じた予期しない例外は失敗結果に変換しない。"""
    _seed(repository, CASE_A, failure_stage_index=1)
    rollback = Mock()
    rollback.execute.return_value = None
    usecase, _, runners = _make_runner(repository, [_path()], rollback)
    runners[1].execute.side_effect = RuntimeError("unexpected")
    with pytest.raises(RuntimeError, match="unexpected"):
        usecase.execute(student_id=STUDENT, stop_producer=lambda: False)
    assert isinstance(
        repository.get(STUDENT, _path()).last_stage_result.error,
        CompilerDiagnosticError,
    )


def test_stop_before_first_step_leaves_results_unchanged(repository) -> None:
    """先に停止要求があればステージやDBへ触れず処理を中断する。"""
    rollback = Mock()
    usecase, _, runners = _make_runner(repository, [_path()], rollback)
    with pytest.raises(StopTask):
        usecase.execute(student_id=STUDENT, stop_producer=lambda: True)
    rollback.execute.assert_not_called()
    for runner in runners:
        runner.execute.assert_not_called()
    assert repository.get(STUDENT, _path()).get_next_stage() == BuildStage()


@pytest.mark.parametrize(
    ("rollback_stage", "expected_a", "expected_b"),
    [
        (BuildStage, [False, False, False, False], [False, False, False, False]),
        (CompileStage, [True, False, False, False], [True, False, False, False]),
        (ExecuteStage, [True, True, False, False], [True, True, True, True]),
        (StageTest, [True, True, True, False], [True, True, True, True]),
    ],
    ids=["shared-build", "shared-compile", "local-execute", "local-test"],
)
def test_rollback_clears_only_required_scope(
    repository, rollback_stage, expected_a, expected_b,
) -> None:
    """共有ステージは全ケース、個別ステージは当該ケースだけ削除する。"""
    _seed(repository, CASE_A)
    _seed(repository, CASE_B)
    path_a, path_b = _path(CASE_A), _path(CASE_B)
    rollback_checker = Mock()

    def affected_case_only(*, stage_path_result, student_id):
        """最初のケースだけに設定変更を発生させる。"""
        assert student_id == STUDENT
        return rollback_stage if stage_path_result.stage_path == path_a else None

    rollback_checker.execute.side_effect = affected_case_only
    usecase, _, runners = _make_runner(repository, [path_a, path_b], rollback_checker)
    with pytest.raises(StopTask):
        usecase.execute(student_id=STUDENT, stop_producer=_stop_on_second_check())

    for path, expected in ((path_a, expected_a), (path_b, expected_b)):
        actual = repository.get(STUDENT, path)
        assert [actual.has_result(stage) for stage in path] == expected
    for runner in runners:
        runner.execute.assert_not_called()


def test_unchanged_completed_path_requires_no_retry_or_rollback(repository) -> None:
    """全ステージ成功かつ設定に変更がなければ何もしない。"""
    _seed(repository, CASE_A)
    checker, _, _, _, _, _ = _rollback_checker()
    usecase, _, runners = _make_runner(repository, [_path()], checker)
    usecase.execute(student_id=STUDENT, stop_producer=lambda: False)
    assert repository.get(STUDENT, _path()).are_all_finished is True
    for runner in runners:
        runner.execute.assert_not_called()
