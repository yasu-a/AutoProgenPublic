import itertools
from datetime import datetime
from typing import Optional

import pytest

from application.dependency.repositories import get_student_stage_path_result_repository
from domain.models.output_file import OutputFileMapping, OutputFile
from domain.models.stage_path import StagePath
from domain.models.stages import BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.student_stage_path_result import StudentStagePathResult
from domain.models.student_stage_result import (
    BuildSuccessStudentStageResult,
    BuildFailureStudentStageResult,
    CompileSuccessStudentStageResult,
    CompileFailureStudentStageResult,
    ExecuteSuccessStudentStageResult,
    ExecuteFailureStudentStageResult,
    TestSuccessStudentStageResult,
    TestFailureStudentStageResult,
    TestResultOutputFileMapping,
)
from domain.models.values import (
    StudentID,
    TestCaseID,
    FileID,
)


@pytest.fixture
def repo():
    return get_student_stage_path_result_repository()


@pytest.fixture
def student_id_1(sample_student_ids):
    return sample_student_ids[0]


@pytest.fixture
def student_id_2(sample_student_ids):
    return sample_student_ids[1]


@pytest.fixture
def testcase_id_1():
    return TestCaseID("TestCase-1")


@pytest.fixture
def testcase_id_2():
    return TestCaseID("TestCase-2")


@pytest.fixture
def stage_path_1(testcase_id_1):
    """単一テストケースのステージパス"""
    return StagePath([
        BuildStage(),
        CompileStage(),
        ExecuteStage(testcase_id_1),
        TestStage(testcase_id_1),
    ])


@pytest.fixture
def stage_path_2(testcase_id_2):
    """別のテストケースのステージパス"""
    return StagePath([
        BuildStage(),
        CompileStage(),
        ExecuteStage(testcase_id_2),
        TestStage(testcase_id_2),
    ])


# --- Fixtures for all result types (success/failure) as mappers ---
@pytest.fixture
def build_success_result(student_id_1, student_id_2):
    def _mapper(student_id: StudentID, /, updated=False):
        try:
            checksum = {
                (student_id_1, False): 12,
                (student_id_1, True): 34,
                (student_id_2, False): 56,
                (student_id_2, True): 78
            }[student_id, updated]
        except KeyError:
            raise AssertionError(f"unexpected student_id: {student_id}")
        return BuildSuccessStudentStageResult.create_instance(
            student_id=student_id,
            submission_folder_checksum=checksum,
        )

    return _mapper


@pytest.fixture
def build_failure_result(student_id_1, student_id_2):
    def _mapper(student_id: StudentID, /, updated=False):
        try:
            reason = {
                (student_id_1, False): "build failed for student 1",
                (student_id_1, True): "build failed for student 1 updated",
                (student_id_2, False): "build failed for student 2",
                (student_id_2, True): "build failed for student 2 updated"
            }[student_id, updated]
        except KeyError:
            raise AssertionError(f"unexpected student_id: {student_id}")
        return BuildFailureStudentStageResult.create_instance(
            student_id=student_id,
            reason=reason,
        )

    return _mapper


@pytest.fixture
def compile_success_result(student_id_1, student_id_2):
    def _mapper(student_id: StudentID, /, updated=False):
        try:
            output = {
                (student_id_1, False): "compile ok for student 1",
                (student_id_1, True): "compile ok for student 1 updated",
                (student_id_2, False): "compile ok for student 2",
                (student_id_2, True): "compile ok for student 2 updated"
            }[student_id, updated]
        except KeyError:
            raise AssertionError(f"unexpected student_id: {student_id}")
        return CompileSuccessStudentStageResult.create_instance(
            student_id=student_id,
            output=output,
        )

    return _mapper


@pytest.fixture
def compile_failure_result(student_id_1, student_id_2):
    def _mapper(student_id: StudentID, /, updated=False):
        try:
            reason, output = {
                (student_id_1, False): (
                    "compile error for student 1",
                    "error log 1",
                ),
                (student_id_1, True): (
                    "compile error for student 1 updated",
                    "error log 1 updated",
                ),
                (student_id_2, False): (
                    "compile error for student 2",
                    "error log 2",
                ),
                (student_id_2, True): (
                    "compile error for student 2 updated",
                    "error log 2 updated",
                ),
            }[student_id, updated]
        except KeyError:
            raise AssertionError(f"unexpected student_id: {student_id}")
        return CompileFailureStudentStageResult.create_instance(
            student_id=student_id,
            reason=reason,
            output=output,
        )

    return _mapper


@pytest.fixture
def execute_success_result(student_id_1, student_id_2, testcase_id_1, testcase_id_2):
    def _mapper(student_id: StudentID, testcase_id: TestCaseID, /, updated=False):
        try:
            content, mtime = {
                (student_id_1, testcase_id_1, False): (
                    "ok 1-1",
                    datetime.fromisoformat("2023-01-01T00:00:01"),
                ),
                (student_id_1, testcase_id_1, True): (
                    "ok 1-1 updated",
                    datetime.fromisoformat("2023-01-01T00:00:11"),
                ),
                (student_id_1, testcase_id_2, False): (
                    "ok 1-2",
                    datetime.fromisoformat("2023-01-01T00:00:02"),
                ),
                (student_id_1, testcase_id_2, True): (
                    "ok 1-2 updated",
                    datetime.fromisoformat("2023-01-01T00:00:12"),
                ),
                (student_id_2, testcase_id_1, False): (
                    "ok 2-1",
                    datetime.fromisoformat("2023-01-01T00:00:03"),
                ),
                (student_id_2, testcase_id_1, True): (
                    "ok 2-1 updated",
                    datetime.fromisoformat("2023-01-01T00:00:13"),
                ),
                (student_id_2, testcase_id_2, False): (
                    "ok 2-2",
                    datetime.fromisoformat("2023-01-01T00:00:04"),
                ),
                (student_id_2, testcase_id_2, True): (
                    "ok 2-2 updated",
                    datetime.fromisoformat("2023-01-01T00:00:14"),
                ),
            }[student_id, testcase_id, updated]
        except KeyError:
            raise AssertionError(
                f"unexpected student_id or testcase_id: {student_id}, {testcase_id}")
        files = OutputFileMapping(
            {FileID.STDOUT: OutputFile(file_id=FileID.STDOUT, content=content)})
        return ExecuteSuccessStudentStageResult.create_instance(
            student_id=student_id,
            testcase_id=testcase_id,
            execute_config_mtime=mtime,
            output_files=files,
        )

    return _mapper


@pytest.fixture
def execute_failure_result(student_id_1, student_id_2, testcase_id_1, testcase_id_2):
    def _mapper(student_id: StudentID, testcase_id: TestCaseID, /, updated=False):
        try:
            reason = {
                (student_id_1, testcase_id_1, False): "exec fail 1-1",
                (student_id_1, testcase_id_1, True): "exec fail 1-1 updated",
                (student_id_1, testcase_id_2, False): "exec fail 1-2",
                (student_id_1, testcase_id_2, True): "exec fail 1-2 updated",
                (student_id_2, testcase_id_1, False): "exec fail 2-1",
                (student_id_2, testcase_id_1, True): "exec fail 2-1 updated",
                (student_id_2, testcase_id_2, False): "exec fail 2-2",
                (student_id_2, testcase_id_2, True): "exec fail 2-2 updated"
            }[student_id, testcase_id, updated]
        except KeyError:
            raise AssertionError(
                f"unexpected student_id or testcase_id: {student_id}, {testcase_id}")
        return ExecuteFailureStudentStageResult.create_instance(
            student_id=student_id,
            testcase_id=testcase_id,
            reason=reason,
        )

    return _mapper


@pytest.fixture
def test_success_result(student_id_1, student_id_2, testcase_id_1, testcase_id_2):
    def _mapper(student_id: StudentID, testcase_id: TestCaseID, /, updated=False):
        try:
            mtime = {
                (student_id_1, testcase_id_1, False): datetime.fromisoformat("2023-01-02T00:00:01"),
                (student_id_1, testcase_id_1, True): datetime.fromisoformat("2023-01-02T00:00:11"),
                (student_id_1, testcase_id_2, False): datetime.fromisoformat("2023-01-02T00:00:02"),
                (student_id_1, testcase_id_2, True): datetime.fromisoformat("2023-01-02T00:00:12"),
                (student_id_2, testcase_id_1, False): datetime.fromisoformat("2023-01-02T00:00:03"),
                (student_id_2, testcase_id_1, True): datetime.fromisoformat("2023-01-02T00:00:13"),
                (student_id_2, testcase_id_2, False): datetime.fromisoformat("2023-01-02T00:00:04"),
                (student_id_2, testcase_id_2, True): datetime.fromisoformat("2023-01-02T00:00:14"),
            }[student_id, testcase_id, updated]
        except KeyError:
            raise AssertionError(
                f"unexpected student_id or testcase_id: {student_id}, {testcase_id}"
            )
        return TestSuccessStudentStageResult.create_instance(
            student_id=student_id,
            testcase_id=testcase_id,
            test_config_mtime=mtime,
            test_result_output_files=TestResultOutputFileMapping(),
        )

    return _mapper


@pytest.fixture
def test_failure_result(student_id_1, student_id_2, testcase_id_1, testcase_id_2):
    def _mapper(student_id: StudentID, testcase_id: TestCaseID, /, updated=False):
        try:
            reason = {
                (student_id_1, testcase_id_1, False): "test fail 1-1",
                (student_id_1, testcase_id_1, True): "test fail 1-1 updated",
                (student_id_1, testcase_id_2, False): "test fail 1-2",
                (student_id_1, testcase_id_2, True): "test fail 1-2 updated",
                (student_id_2, testcase_id_1, False): "test fail 2-1",
                (student_id_2, testcase_id_1, True): "test fail 2-1 updated",
                (student_id_2, testcase_id_2, False): "test fail 2-2",
                (student_id_2, testcase_id_2, True): "test fail 2-2 updated"
            }[student_id, testcase_id, updated]
        except KeyError:
            raise AssertionError(
                f"unexpected student_id or testcase_id: {student_id}, {testcase_id}"
            )
        return TestFailureStudentStageResult.create_instance(
            student_id=student_id,
            testcase_id=testcase_id,
            reason=reason,
        )

    return _mapper


# --- Parametrize pattern for all result types ---
ALL_RESULT_MAPPERS = [
    "build_success_result",
    "build_failure_result",
    "compile_success_result",
    "compile_failure_result",
    "execute_success_result",
    "execute_failure_result",
    "test_success_result",
    "test_failure_result",
]


def get_positional_arg_names(func) -> tuple[str, ...]:
    import inspect
    sig = inspect.signature(func)
    names = []
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            names.append(param.name)
    return tuple(names)


@pytest.fixture
def get_single_result(request, student_id_1, testcase_id_1):
    def _mapper(
            result_fixture: str,
            student_id: Optional[StudentID] = None,
            testcase_id: Optional[TestCaseID] = None,
            updated=False,
    ):
        if student_id is None:
            student_id = student_id_1
        if testcase_id is None:
            testcase_id = testcase_id_1

        mapper = request.getfixturevalue(result_fixture)

        if get_positional_arg_names(mapper) == ("student_id",):
            return mapper(student_id, updated=updated)
        elif get_positional_arg_names(mapper) == ("student_id", "testcase_id"):
            return mapper(student_id, testcase_id, updated=updated)
        else:
            raise AssertionError(f"unexpected arg names: {get_positional_arg_names(mapper)}")

    return _mapper


# --- Helper for equality ---
def _assert_stage_results_are_equal(r1, r2):
    assert type(r1) is type(r2)
    assert r1.student_id == r2.student_id
    assert r1.stage == r2.stage
    if hasattr(r1, "submission_folder_checksum"):
        assert r1.submission_folder_checksum == r2.submission_folder_checksum
    if hasattr(r1, "reason"):
        assert r1.reason == r2.reason
    if hasattr(r1, "output"):
        assert r1.output == r2.output
    if hasattr(r1, "execute_config_mtime"):
        assert r1.execute_config_mtime == r2.execute_config_mtime
    if hasattr(r1, "output_files"):
        assert r1.output_files.to_json() == r2.output_files.to_json()
    if hasattr(r1, "test_config_mtime"):
        assert r1.test_config_mtime == r2.test_config_mtime
    if hasattr(r1, "test_result_output_files"):
        assert r1.test_result_output_files.to_json() == r2.test_result_output_files.to_json()


def _are_results_equal(r1, r2):
    try:
        _assert_stage_results_are_equal(r1, r2)
    except AssertionError:
        return False
    else:
        return True


def _create_stage_path_result(student_id: StudentID, stage_path: StagePath,
                              result) -> StudentStagePathResult:
    """単一のステージ結果からStudentStagePathResultを作成"""
    from collections import OrderedDict
    from domain.models.stages import AbstractStage
    from domain.models.student_stage_result import AbstractStudentStageResult

    stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None] = OrderedDict()

    # ステージパスの各ステージに対して、該当するステージのみ結果を設定
    for stage in stage_path:
        if stage == result.stage:
            stage_results[stage] = result
        else:
            stage_results[stage] = None

    return StudentStagePathResult(
        student_id=student_id,
        stage_results=stage_results,
    )


# --- Parametrized test for all result types ---
@pytest.mark.parametrize(
    "result_fixture",
    ALL_RESULT_MAPPERS,
)
def test_put_get_stage_path_result(
        repo,
        result_fixture,
        get_single_result,
        stage_path_1,
):
    result = get_single_result(result_fixture)
    stage_path_result = _create_stage_path_result(result.student_id, stage_path_1, result)

    # put前は存在しない（空のStudentStagePathResultが返される）
    empty_result = repo.get(result.student_id, stage_path_1)
    assert empty_result.student_id == result.student_id
    # すべてのステージ結果がNoneであることを確認
    for stage in stage_path_1:
        assert empty_result.get_result(stage) is None

    # *** put result
    repo.put(stage_path_result)

    # getで取得できることを確認
    retrieved = repo.get(result.student_id, stage_path_1)
    assert retrieved.student_id == result.student_id
    assert retrieved.get_result(result.stage) is not None
    _assert_stage_results_are_equal(result, retrieved.get_result(result.stage))


# --- 複雑な操作シーケンス ---
@pytest.mark.parametrize(
    "result_fixture",
    ALL_RESULT_MAPPERS,
)
def test_complex_sequence(
        repo,
        result_fixture,
        get_single_result,
        stage_path_1,
):
    result = get_single_result(result_fixture)
    updated_result = get_single_result(result_fixture, updated=True)

    stage_path_result = _create_stage_path_result(result.student_id, stage_path_1, result)
    updated_stage_path_result = _create_stage_path_result(updated_result.student_id, stage_path_1,
                                                          updated_result)

    # *** put result
    repo.put(stage_path_result)

    # verify content
    retrieved = repo.get(result.student_id, stage_path_1)
    _assert_stage_results_are_equal(result, retrieved.get_result(result.stage))

    # *** put updated result (overwrite)
    repo.put(updated_stage_path_result)

    # verify updated content
    retrieved = repo.get(result.student_id, stage_path_1)
    _assert_stage_results_are_equal(updated_result, retrieved.get_result(result.stage))


# --- 生徒ごとの独立性テスト ---
@pytest.mark.parametrize(
    ("student_1_result_fixture", "student_2_result_fixture"),
    tuple(itertools.combinations(ALL_RESULT_MAPPERS, r=2)),
)
def test_student_isolation(
        repo,
        get_single_result,
        student_1_result_fixture,
        student_2_result_fixture,
        student_id_1,
        student_id_2,
        stage_path_1,
):
    result_s_1 = get_single_result(student_1_result_fixture, student_id=student_id_1)
    result_s_2 = get_single_result(student_2_result_fixture, student_id=student_id_2)

    stage_path_result_s_1 = _create_stage_path_result(student_id_1, stage_path_1, result_s_1)
    stage_path_result_s_2 = _create_stage_path_result(student_id_2, stage_path_1, result_s_2)

    # *** put s1
    repo.put(stage_path_result_s_1)

    # verify s1 content
    retrieved_s_1 = repo.get(student_id_1, stage_path_1)
    _assert_stage_results_are_equal(result_s_1, retrieved_s_1.get_result(result_s_1.stage))

    # s2は存在しない（空のStudentStagePathResultが返される）
    empty_result_s_2 = repo.get(student_id_2, stage_path_1)
    assert empty_result_s_2.student_id == student_id_2
    # すべてのステージ結果がNoneであることを確認
    for stage in stage_path_1:
        assert empty_result_s_2.get_result(stage) is None

    # *** put s2
    repo.put(stage_path_result_s_2)

    # s1は引き続き存在
    retrieved_s_1_again = repo.get(student_id_1, stage_path_1)
    _assert_stage_results_are_equal(result_s_1, retrieved_s_1_again.get_result(result_s_1.stage))

    # s2も存在
    retrieved_s_2 = repo.get(student_id_2, stage_path_1)
    _assert_stage_results_are_equal(result_s_2, retrieved_s_2.get_result(result_s_2.stage))


# --- BUILD, COMPILEの共有確認テスト ---
@pytest.mark.parametrize(
    "result_fixture",
    ["build_success_result", "build_failure_result", "compile_success_result",
     "compile_failure_result"],
)
def test_stage_sharing_across_testcases_build_compile_shared(
        repo,
        get_single_result,
        result_fixture,
        student_id_1,
        testcase_id_1,
        testcase_id_2,
        stage_path_1,
        stage_path_2,
):
    # testcase_idが異なる2つのStagePathでBUILD/COMPILEの結果をput
    result_tc_1 = get_single_result(result_fixture, testcase_id=testcase_id_1)
    result_tc_2 = get_single_result(result_fixture, testcase_id=testcase_id_2, updated=True)

    # BUILD/COMPILEはtestcase_idを持たないので、同じステージとして共有される
    stage_path_result_tc_1 = _create_stage_path_result(student_id_1, stage_path_1, result_tc_1)
    stage_path_result_tc_2 = _create_stage_path_result(student_id_1, stage_path_2, result_tc_2)

    # まずtc1の結果をput
    repo.put(stage_path_result_tc_1)
    # tc2のStagePathでも同じステージの結果が見える
    retrieved_tc_2 = repo.get(student_id_1, stage_path_2)
    _assert_stage_results_are_equal(result_tc_1, retrieved_tc_2.get_result(result_tc_1.stage))

    # tc2の結果で上書き
    repo.put(stage_path_result_tc_2)
    # tc1のStagePathでも上書きされている
    retrieved_tc_1 = repo.get(student_id_1, stage_path_1)
    _assert_stage_results_are_equal(result_tc_2, retrieved_tc_1.get_result(result_tc_2.stage))


# --- EXECUTE, TESTの独立性確認テスト ---
@pytest.mark.parametrize(
    "result_fixture",
    ["execute_success_result", "execute_failure_result", "test_success_result",
     "test_failure_result"],
)
def test_stage_sharing_across_testcases_execute_test_independent(
        repo,
        get_single_result,
        result_fixture,
        student_id_1,
        testcase_id_1,
        testcase_id_2,
        stage_path_1,
        stage_path_2,
):
    # testcase_idが異なる2つのStagePathでEXECUTE/TESTの結果をput
    result_tc_1 = get_single_result(result_fixture, testcase_id=testcase_id_1)
    result_tc_2 = get_single_result(result_fixture, testcase_id=testcase_id_2, updated=True)

    # EXECUTE/TESTはtestcase_idごとに独立している
    stage_path_result_tc_1 = _create_stage_path_result(student_id_1, stage_path_1, result_tc_1)
    stage_path_result_tc_2 = _create_stage_path_result(student_id_1, stage_path_2, result_tc_2)

    # まずtc1の結果をput
    repo.put(stage_path_result_tc_1)
    # tc2のStagePathでは結果が存在しない（独立している）
    retrieved_tc_2 = repo.get(student_id_1, stage_path_2)
    assert retrieved_tc_2.get_result(result_tc_2.stage) is None

    # tc2の結果をput
    repo.put(stage_path_result_tc_2)
    # それぞれ独立していることを確認
    retrieved_tc_1 = repo.get(student_id_1, stage_path_1)
    _assert_stage_results_are_equal(result_tc_1, retrieved_tc_1.get_result(result_tc_1.stage))
    retrieved_tc_2 = repo.get(student_id_1, stage_path_2)
    _assert_stage_results_are_equal(result_tc_2, retrieved_tc_2.get_result(result_tc_2.stage))


# --- success/failureの片方を他方が上書きする挙動の確認 ---
@pytest.mark.parametrize(
    ("success_result_fixture", "failure_result_fixture"),
    [
        ("build_success_result", "build_failure_result"),
        ("compile_success_result", "compile_failure_result"),
        ("execute_success_result", "execute_failure_result"),
        ("test_success_result", "test_failure_result"),
        ("build_failure_result", "build_success_result"),
        ("compile_failure_result", "compile_success_result"),
        ("execute_failure_result", "execute_success_result"),
        ("test_failure_result", "test_success_result"),
    ],
)
def test_success_overwrite_with_failure(
        repo,
        get_single_result,
        success_result_fixture,
        failure_result_fixture,
        stage_path_1,
):
    success_result = get_single_result(success_result_fixture)
    failure_result = get_single_result(failure_result_fixture)

    success_stage_path_result = _create_stage_path_result(success_result.student_id, stage_path_1,
                                                          success_result)
    failure_stage_path_result = _create_stage_path_result(failure_result.student_id, stage_path_1,
                                                          failure_result)

    # *** put success result
    repo.put(success_stage_path_result)

    # verify success content
    retrieved_success = repo.get(success_result.student_id, stage_path_1)
    _assert_stage_results_are_equal(success_result,
                                    retrieved_success.get_result(success_result.stage))

    # *** put failure result (overwrite success)
    repo.put(failure_stage_path_result)

    # verify failure content (success was overwritten)
    retrieved_failure = repo.get(failure_result.student_id, stage_path_1)
    _assert_stage_results_are_equal(failure_result,
                                    retrieved_failure.get_result(failure_result.stage))

    # verify success content is gone
    assert not _are_results_equal(retrieved_failure.get_result(failure_result.stage),
                                  success_result)

    # *** put success result again (overwrite failure)
    repo.put(success_stage_path_result)

    # verify success content (failure was overwritten)
    retrieved_success_again = repo.get(success_result.student_id, stage_path_1)
    _assert_stage_results_are_equal(success_result,
                                    retrieved_success_again.get_result(success_result.stage))

    # verify failure content is gone
    assert not _are_results_equal(retrieved_success_again.get_result(success_result.stage),
                                  failure_result)


# --- タイムスタンプのテスト ---
@pytest.mark.parametrize(
    "result_fixture",
    ALL_RESULT_MAPPERS,
)
def test_timestamp_on_put(
        repo,
        get_single_result,
        result_fixture,
        student_id_1,
        stage_path_1,
):
    from time import sleep
    result = get_single_result(result_fixture, student_id=student_id_1)
    stage_path_result = _create_stage_path_result(student_id_1, stage_path_1, result)

    # put前はNone
    assert repo.get_timestamp(student_id_1) is None

    sleep(0.001)
    t0 = datetime.now()

    # putでタイムスタンプ更新
    repo.put(stage_path_result)
    t1 = repo.get_timestamp(student_id_1)
    assert t1 is not None and t1 > t0


@pytest.mark.parametrize(
    "result_fixture",
    ALL_RESULT_MAPPERS,
)
def test_timestamp_not_update_on_get(
        repo,
        get_single_result,
        result_fixture,
        student_id_1,
        stage_path_1,
):
    result = get_single_result(result_fixture, student_id=student_id_1)
    stage_path_result = _create_stage_path_result(student_id_1, stage_path_1, result)

    # *** put result
    repo.put(stage_path_result)
    t0 = repo.get_timestamp(student_id_1)

    from time import sleep
    sleep(0.001)

    # getでもタイムスタンプ変化しない
    repo.get(student_id_1, stage_path_1)
    t1 = repo.get_timestamp(student_id_1)
    assert t1 == t0


# --- 集約単位での操作テスト ---
def test_aggregate_operations(
        repo,
        get_single_result,
        student_id_1,
        stage_path_1,
):
    """集約単位での操作をテスト"""
    # 複数のステージ結果を含む集約を作成
    build_result = get_single_result("build_success_result", student_id=student_id_1)
    compile_result = get_single_result("compile_success_result", student_id=student_id_1)

    from collections import OrderedDict
    from domain.models.stages import AbstractStage
    from domain.models.student_stage_result import AbstractStudentStageResult

    stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None] = OrderedDict([
        (BuildStage(), build_result),
        (CompileStage(), compile_result),
        (ExecuteStage(TestCaseID("TestCase-1")), None),
        (TestStage(TestCaseID("TestCase-1")), None),
    ])

    stage_path_result = StudentStagePathResult(
        student_id=student_id_1,
        stage_results=stage_results,
    )

    # put
    repo.put(stage_path_result)

    # get
    retrieved = repo.get(student_id_1, stage_path_1)

    # 各ステージの結果を確認
    assert retrieved.get_result(BuildStage()) is not None
    assert retrieved.get_result(CompileStage()) is not None
    assert retrieved.get_result(ExecuteStage(TestCaseID("TestCase-1"))) is None
    assert retrieved.get_result(TestStage(TestCaseID("TestCase-1"))) is None

    # 成功したステージの結果を確認
    _assert_stage_results_are_equal(build_result, retrieved.get_result(BuildStage()))
    _assert_stage_results_are_equal(compile_result, retrieved.get_result(CompileStage()))


def test_stage_path_result_methods(
        repo,
        get_single_result,
        student_id_1,
        stage_path_1,
):
    """StudentStagePathResultのメソッドをテスト"""
    build_result = get_single_result("build_success_result", student_id=student_id_1)
    compile_result = get_single_result("compile_success_result", student_id=student_id_1)

    from collections import OrderedDict
    from domain.models.stages import AbstractStage
    from domain.models.student_stage_result import AbstractStudentStageResult

    stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None] = OrderedDict([
        (BuildStage(), build_result),
        (CompileStage(), compile_result),
        (ExecuteStage(TestCaseID("TestCase-1")), None),
        (TestStage(TestCaseID("TestCase-1")), None),
    ])

    stage_path_result = StudentStagePathResult(
        student_id=student_id_1,
        stage_results=stage_results,
    )

    # put
    repo.put(stage_path_result)

    # get
    retrieved = repo.get(student_id_1, stage_path_1)

    # has_result
    assert retrieved.has_result(BuildStage()) is True
    assert retrieved.has_result(CompileStage()) is True
    assert retrieved.has_result(ExecuteStage(TestCaseID("TestCase-1"))) is False
    assert retrieved.has_result(TestStage(TestCaseID("TestCase-1"))) is False

    # stage_statuses
    statuses = retrieved.stage_statuses
    assert statuses[BuildStage()] == StudentStagePathResult.StageStatus.SUCCESS
    assert statuses[CompileStage()] == StudentStagePathResult.StageStatus.SUCCESS
    assert statuses[ExecuteStage(
        TestCaseID("TestCase-1"))] == StudentStagePathResult.StageStatus.UNFINISHED
    assert statuses[
               TestStage(TestCaseID("TestCase-1"))] == StudentStagePathResult.StageStatus.UNFINISHED

    # get_next_stage
    assert retrieved.get_next_stage() == ExecuteStage(TestCaseID("TestCase-1"))

    # is_last_stage_success
    assert retrieved.is_last_stage_success is True
