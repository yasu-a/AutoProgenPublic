import itertools
import time
from datetime import datetime

import pytest

from application.dependency.repositories import get_student_stage_result_repository
from domain.errors import RepositoryItemNotFoundError
from domain.models.output_file import OutputFileMapping, OutputFile
from domain.models.stages import (
    BuildStage,
    CompileStage,
    ExecuteStage,
    TestStage,
    AbstractStage,
)
from domain.models.student_stage_result import (
    AbstractStudentStageResult,
    BuildFailureStudentStageResult,
    BuildSuccessStudentStageResult,
    CompileFailureStudentStageResult,
    CompileSuccessStudentStageResult,
    ExecuteFailureStudentStageResult,
    ExecuteSuccessStudentStageResult,
    TestFailureStudentStageResult,
    TestSuccessStudentStageResult,
    TestResultOutputFileMapping,
)
from domain.models.test_result_output_file_entry import TestResultUnexpectedOutputFileEntry
from domain.models.values import StudentID, TestCaseID, FileID


@pytest.fixture
def repo():
    return get_student_stage_result_repository()


@pytest.fixture
def sample_student_id(sample_student_ids):
    # Use the first student from the conftest fixture
    return sample_student_ids[0]


@pytest.fixture
def another_sample_student_id(sample_student_ids):
    # Use the second student from the conftest fixture for independence tests
    return sample_student_ids[1]


@pytest.fixture
def sample_testcase_id():
    return TestCaseID("TestCase-1")


@pytest.fixture
def another_sample_testcase_id():
    return TestCaseID("TestCase-2")


@pytest.fixture
def sample_build_success_result(sample_student_id):
    return BuildSuccessStudentStageResult.create_instance(
        student_id=sample_student_id,
        submission_folder_checksum=12345,
    )


@pytest.fixture
def sample_build_failure_result(sample_student_id):
    return BuildFailureStudentStageResult.create_instance(
        student_id=sample_student_id,
        reason="Build failed due to syntax error.",
    )


@pytest.fixture
def sample_compile_success_result(sample_student_id):
    return CompileSuccessStudentStageResult.create_instance(
        student_id=sample_student_id,
        output="Compile successful.",
    )


@pytest.fixture
def sample_compile_failure_result(sample_student_id):
    return CompileFailureStudentStageResult.create_instance(
        student_id=sample_student_id,
        reason="Compilation error: missing semicolon.",
        output="error: missing semicolon at line 5",
    )


@pytest.fixture
def sample_execute_success_result(sample_student_id, sample_testcase_id):
    output_files = OutputFileMapping()
    file_id = FileID.STDOUT
    output_files[file_id] = OutputFile(
        file_id=file_id,
        content="hello\n",
    )
    return ExecuteSuccessStudentStageResult.create_instance(
        student_id=sample_student_id,
        testcase_id=sample_testcase_id,
        execute_config_mtime=datetime.now(),
        output_files=output_files,
    )


@pytest.fixture
def sample_execute_failure_result(sample_student_id, sample_testcase_id):
    return ExecuteFailureStudentStageResult.create_instance(
        student_id=sample_student_id,
        testcase_id=sample_testcase_id,
        reason="Execution timeout.",
    )


@pytest.fixture
def sample_test_success_result(sample_student_id, sample_testcase_id):
    test_result_files = TestResultOutputFileMapping()
    file_id = FileID("output.txt")
    test_result_files[file_id] = TestResultUnexpectedOutputFileEntry(
        file_id=file_id,
        actual=OutputFile(
            file_id=file_id,
            content="hello\n",
        ),
    )
    return TestSuccessStudentStageResult.create_instance(
        student_id=sample_student_id,
        testcase_id=sample_testcase_id,
        test_config_mtime=datetime.now(),
        test_result_output_files=test_result_files,
    )


@pytest.fixture
def sample_test_failure_result(sample_student_id, sample_testcase_id):
    return TestFailureStudentStageResult.create_instance(
        student_id=sample_student_id,
        testcase_id=sample_testcase_id,
        reason="Test case failed: output mismatch.",
    )


# --- Helper function for comparison ---
# noinspection PyInconsistentReturns
def _assert_stage_results_are_equal(
        r1: AbstractStudentStageResult,
        r2: AbstractStudentStageResult,
):
    assert type(r1) is type(r2)
    assert r1.student_id == r2.student_id

    # Ensure stage comparison is robust for stages with testcase_id
    assert isinstance(r1.stage, AbstractStage) and isinstance(r2.stage, AbstractStage)

    # Custom comparison for stages with testcase_id
    if isinstance(r1.stage, (ExecuteStage, TestStage)) \
            and isinstance(r2.stage, (ExecuteStage, TestStage)):
        assert r1.stage.testcase_id == r2.stage.testcase_id
    else:  # For BuildStage, CompileStage (no testcase_id)
        return type(r1.stage) is type(r2.stage)

    # Specific field comparison based on the result type
    if isinstance(r1, BuildSuccessStudentStageResult) \
            and isinstance(r2, BuildSuccessStudentStageResult):
        assert r1.submission_folder_checksum == r2.submission_folder_checksum

    elif isinstance(r1, BuildFailureStudentStageResult) \
            and isinstance(r2, BuildFailureStudentStageResult):
        assert r1.reason == r2.reason

    elif isinstance(r1, CompileSuccessStudentStageResult) \
            and isinstance(r2, CompileSuccessStudentStageResult):
        assert r1.output == r2.output

    elif isinstance(r1, CompileFailureStudentStageResult) \
            and isinstance(r2, CompileFailureStudentStageResult):
        assert r1.reason == r2.reason and r1.output == r2.output

    elif isinstance(r1, ExecuteSuccessStudentStageResult) \
            and isinstance(r2, ExecuteSuccessStudentStageResult):
        assert r1.execute_config_mtime == r2.execute_config_mtime \
               and r1.output_files.to_json() == r2.output_files.to_json()

    elif isinstance(r1, ExecuteFailureStudentStageResult) \
            and isinstance(r2, ExecuteFailureStudentStageResult):
        assert r1.reason == r2.reason

    elif isinstance(r1, TestSuccessStudentStageResult) \
            and isinstance(r2, TestSuccessStudentStageResult):
        assert r1.test_config_mtime == r2.test_config_mtime \
               and r1.test_result_output_files.to_json() == r2.test_result_output_files.to_json()

    elif isinstance(r1, TestFailureStudentStageResult) \
            and isinstance(r2, TestFailureStudentStageResult):
        assert r1.reason == r2.reason

    else:
        assert False, (type(r1), type(r2))


# --- Test Functions ---

# Test put and get for all result types
@pytest.mark.parametrize(
    "result_fixture_name",
    [
        "sample_build_success_result", "sample_build_failure_result",
        "sample_compile_success_result", "sample_compile_failure_result",
        "sample_execute_success_result", "sample_execute_failure_result",
        "sample_test_success_result", "sample_test_failure_result",
    ]
)
def test_put_and_get_result(repo, request, result_fixture_name):
    result = request.getfixturevalue(result_fixture_name)

    # Initially, confirm it does not exist
    assert not repo.exists(result.student_id, result.stage)
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(result.student_id, result.stage)

    # Save using put
    repo.put(result)

    # After saving, confirm it exists
    assert repo.exists(result.student_id, result.stage)

    # Retrieve using get and confirm content matches
    retrieved_result = repo.get(result.student_id, result.stage)
    _assert_stage_results_are_equal(result, retrieved_result)


# Test updating existing results for all stage types
@pytest.mark.parametrize(
    "stage_type, initial_result_factory, updated_result_factory",
    [
        (
                BuildStage,
                lambda student_id: BuildSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    submission_folder_checksum=111
                ),
                lambda student_id: BuildFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason="New build failed."
                ),
        ),
        (
                CompileStage,
                lambda student_id: CompileSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    output="Initial compile output."
                ),
                lambda student_id: CompileFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason="New compile error.",
                    output="new error"
                ),
        ),
        # ExecuteStage and TestStage need testcase_id
        (
                ExecuteStage,
                lambda student_id, testcase_id: ExecuteSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    execute_config_mtime=datetime.now(),
                    output_files=OutputFileMapping()
                ),
                lambda student_id, testcase_id: ExecuteFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    reason="New execution error."
                ),
        ),
        (
                TestStage,
                lambda student_id, testcase_id: TestSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    test_config_mtime=datetime.now(),
                    test_result_output_files=TestResultOutputFileMapping()
                ),
                lambda student_id, testcase_id: TestFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    reason="New test error."
                ),
        ),
    ],
)
def test_put_updates_existing_result_all_stages(
        repo, sample_student_id, sample_testcase_id,
        stage_type, initial_result_factory,
        updated_result_factory,
):
    if stage_type in (ExecuteStage, TestStage):
        initial_result = initial_result_factory(sample_student_id, sample_testcase_id)
        updated_result = updated_result_factory(sample_student_id, sample_testcase_id)
    else:
        initial_result = initial_result_factory(sample_student_id)
        updated_result = updated_result_factory(sample_student_id)

    repo.put(initial_result)
    _assert_stage_results_are_equal(repo.get(sample_student_id, initial_result.stage),
                                    initial_result)

    repo.put(updated_result)
    retrieved_result = repo.get(sample_student_id, updated_result.stage)
    _assert_stage_results_are_equal(updated_result, retrieved_result)
    assert retrieved_result.is_success != initial_result.is_success  # Ensure success/failure status changed


# Test exists method for non-existent results across all stages
@pytest.mark.parametrize(
    "stage",
    [
        BuildStage(),
        CompileStage(),
        ExecuteStage(TestCaseID("NON_EXISTENT_TC_A")),
        TestStage(TestCaseID("NON_EXISTENT_TC_B")),
    ]
)
def test_exists_non_existent_result_all_stages(repo, sample_student_id, stage):
    # Test with existing student ID but non-existent stage result
    assert not repo.exists(sample_student_id, stage)

    # Test with non-existent student ID
    unknown_student_id = StudentID("01Z2345678X")
    assert not repo.exists(unknown_student_id, stage)


# Test get method for non-existent keys across all stages
@pytest.mark.parametrize(
    "stage",
    [
        BuildStage(),
        CompileStage(),
        ExecuteStage(TestCaseID("NON_EXISTENT_TC_C")),
        TestStage(TestCaseID("NON_EXISTENT_TC_D")),
    ]
)
def test_get_non_existent_result_all_stages(repo, sample_student_id, stage):
    # Test with existing student ID but non-existent stage result
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(sample_student_id, stage)

    # Test with non-existent student ID
    unknown_student_id = StudentID("02Y9876543W")
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(unknown_student_id, stage)


# Test delete method for all result types
@pytest.mark.parametrize(
    "result_fixture_name",
    [
        "sample_build_success_result", "sample_build_failure_result",
        "sample_compile_success_result", "sample_compile_failure_result",
        "sample_execute_success_result", "sample_execute_failure_result",
        "sample_test_success_result", "sample_test_failure_result",
    ]
)
def test_delete_result(repo, request, result_fixture_name):
    result = request.getfixturevalue(result_fixture_name)

    # Save
    repo.put(result)
    assert repo.exists(result.student_id, result.stage)

    # Delete
    repo.delete(result.student_id, result.stage)

    # After deletion, confirm it no longer exists
    assert not repo.exists(result.student_id, result.stage)
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(result.student_id, result.stage)

    # Attempting to delete again should raise an error
    with pytest.raises(RepositoryItemNotFoundError):
        repo.delete(result.student_id, result.stage)


# Test that repository operations are independent between students
def test_delete_build_stage_independent_from_other_student_compile_stage(
        repo, sample_student_id, another_sample_student_id
):
    """
    Student 1 のビルド結果を削除しても Student 2 のコンパイル結果には影響しないことを確認します。
    """

    # Student 1 の初期結果
    initial_results_s1 = [
        BuildSuccessStudentStageResult.create_instance(
            student_id=sample_student_id,
            submission_folder_checksum=100,
        ),
    ]
    # Student 2 の初期結果
    initial_results_s2 = [
        CompileSuccessStudentStageResult.create_instance(
            student_id=another_sample_student_id,
            output="S2 compiled OK",
        )
    ]

    # 全ての結果を保存
    for result in initial_results_s1:
        repo.put(result)
    for result in initial_results_s2:
        repo.put(result)

    # 全ての結果が存在し、内容が正しいことを確認
    for result in initial_results_s1:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))
    for result in initial_results_s2:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))

    # Student 1 のビルド結果を削除
    repo.delete(sample_student_id, BuildStage())

    # Student 1 の対象結果が削除されたことを確認
    assert not repo.exists(sample_student_id, BuildStage())
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(sample_student_id, BuildStage())

    # Student 2 の結果が影響を受けていないことを確認
    for result in initial_results_s2:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))


# テストケース: 特定のテストケースIDにおける実行ステージの削除が他の学生に影響しないこと
def test_delete_execute_stage_for_specific_testcase_independent_between_students(
        repo, sample_student_id, another_sample_student_id, sample_testcase_id,
        another_sample_testcase_id
):
    """
    同じExecuteStageで異なるテストケースIDの結果を保存し、一方を削除します。
    Student 1 の特定の ExecuteStage (TestCaseID TC001) を削除しても、
    Student 1 の他の ExecuteStage (TestCaseID TC002) や Student 2 の結果には影響しないことを確認します。
    """

    # Student 1 の初期結果
    initial_results_s1 = [
        ExecuteSuccessStudentStageResult.create_instance(
            student_id=sample_student_id,
            testcase_id=sample_testcase_id,
            execute_config_mtime=datetime.now(),
            output_files=OutputFileMapping(),
        ),
        ExecuteFailureStudentStageResult.create_instance(
            student_id=sample_student_id,
            testcase_id=another_sample_testcase_id,
            reason="S1 exec fail",
        ),
    ]
    # Student 2 の初期結果
    initial_results_s2 = [
        ExecuteSuccessStudentStageResult.create_instance(
            student_id=another_sample_student_id,
            testcase_id=sample_testcase_id,
            execute_config_mtime=datetime.now(),
            output_files=OutputFileMapping(),
        ),
        ExecuteFailureStudentStageResult.create_instance(
            student_id=another_sample_student_id,
            testcase_id=another_sample_testcase_id,
            reason="S2 exec fail",
        )
    ]

    # 全ての結果を保存
    for result in initial_results_s1:
        repo.put(result)
    for result in initial_results_s2:
        repo.put(result)

    # 全ての結果が存在し、内容が正しいことを確認
    for result in initial_results_s1:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))
    for result in initial_results_s2:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))

    # Student 1 の ExecuteStage (TC1) を削除
    repo.delete(sample_student_id, ExecuteStage(sample_testcase_id))

    # Student 1 の対象結果 (TC1) が削除されたことを確認
    assert not repo.exists(sample_student_id, ExecuteStage(sample_testcase_id))
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(sample_student_id, ExecuteStage(sample_testcase_id))

    # Student 1 の他の結果 (TC2) が影響を受けていないことを確認
    expected_s1_tc2_result = ExecuteFailureStudentStageResult.create_instance(
        student_id=sample_student_id, testcase_id=another_sample_testcase_id, reason="S1 exec fail"
    )  # 比較用のインスタンスを再生成
    assert repo.exists(sample_student_id, ExecuteStage(another_sample_testcase_id))
    _assert_stage_results_are_equal(expected_s1_tc2_result,
                                    repo.get(sample_student_id,
                                             ExecuteStage(another_sample_testcase_id)))

    # Student 2 の結果が影響を受けていないことを確認
    for result in initial_results_s2:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))


# テストケース: 特定のテストケースIDにおけるテストステージの削除が他の学生に影響しないこと
def test_delete_test_stage_for_specific_testcase_independent_between_students(
        repo, sample_student_id, another_sample_student_id, sample_testcase_id
):
    """
    同じTestStageで同じテストケースIDの結果を保存し、一方を削除します。
    Student 1 の特定の TestStage (TestCaseID TC_A) を削除しても、
    Student 2 の同じ TestStage (TestCaseID TC_A) には影響しないことを確認します。
    """

    # Student 1 の初期結果
    initial_results_s1 = [
        TestSuccessStudentStageResult.create_instance(
            student_id=sample_student_id,
            testcase_id=sample_testcase_id,
            test_config_mtime=datetime.now(),
            test_result_output_files=TestResultOutputFileMapping(),
        ),
    ]
    # Student 2 の初期結果
    initial_results_s2 = [
        TestSuccessStudentStageResult.create_instance(
            student_id=another_sample_student_id,
            testcase_id=sample_testcase_id,
            test_config_mtime=datetime.now(),
            test_result_output_files=TestResultOutputFileMapping(),
        ),
    ]

    # 全ての結果を保存
    for result in initial_results_s1:
        repo.put(result)
    for result in initial_results_s2:
        repo.put(result)

    # 全ての結果が存在し、内容が正しいことを確認
    for result in initial_results_s1:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))
    for result in initial_results_s2:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))

    # Student 1 の TestStage (TC_A) を削除
    repo.delete(sample_student_id, TestStage(sample_testcase_id))

    # Student 1 の対象結果 (TC_A) が削除されたことを確認
    assert not repo.exists(sample_student_id, TestStage(sample_testcase_id))
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(sample_student_id, TestStage(sample_testcase_id))

    # Student 2 の結果が影響を受けていないことを確認
    for result in initial_results_s2:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))


# テストケース: 学生のステージ結果の更新が他の学生に影響しないこと
def test_update_student_stage_result_independent_between_students(
        repo, sample_student_id, another_sample_student_id, sample_testcase_id
):
    """
    学生1で同じステージの成功から失敗への更新を行い、学生2は影響を受けないことを確認します。
    Student 1 のビルド結果を更新しても、Student 2 の結果には影響しないことを確認します。
    """

    # Student 1 の初期結果 (成功)
    initial_results_s1 = [
        BuildSuccessStudentStageResult.create_instance(
            student_id=sample_student_id,
            submission_folder_checksum=100,
        ),
    ]
    # Student 2 の初期結果
    initial_results_s2 = [
        CompileSuccessStudentStageResult.create_instance(
            student_id=another_sample_student_id,
            output="S2 compiled OK",
        ),
    ]

    # 全ての結果を保存
    for result in initial_results_s1:
        repo.put(result)
    for result in initial_results_s2:
        repo.put(result)

    # 全ての結果が存在し、内容が正しいことを確認
    for result in initial_results_s1:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))
    for result in initial_results_s2:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))

    # Student 1 のビルド結果を失敗に更新
    student1_updated_result = BuildFailureStudentStageResult.create_instance(
        student_id=sample_student_id,
        reason="Updated reason for failure for S1.",
    )
    repo.put(student1_updated_result)

    # 更新が正しく適用されたことを確認
    assert repo.exists(student1_updated_result.student_id, student1_updated_result.stage)
    retrieved_updated_s1 = repo.get(student1_updated_result.student_id,
                                    student1_updated_result.stage)
    _assert_stage_results_are_equal(student1_updated_result, retrieved_updated_s1)

    # Student 2 の結果が影響を受けていないことを確認
    for result in initial_results_s2:
        assert repo.exists(result.student_id, result.stage)
        _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))


@pytest.fixture
def generate_results_patterns(
        sample_student_id,
        another_sample_student_id,
        sample_testcase_id,
        another_sample_testcase_id,
):
    table: dict[
        type[AbstractStage],
        dict[
            tuple[StudentID, TestCaseID | None],
            list[AbstractStudentStageResult],
        ],
    ] = {
        BuildStage: {
            (sample_student_id, None): [
                BuildSuccessStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    submission_folder_checksum=1001,
                ),
                BuildFailureStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    reason="S1 Build failed due to compiler issues.",
                ),
            ],
            (another_sample_student_id, None): [
                BuildSuccessStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    submission_folder_checksum=2002,
                ),
                BuildFailureStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    reason="S2 Build failed due to missing dependencies.",
                ),
            ]
        },
        CompileStage: {
            (sample_student_id, None): [
                CompileSuccessStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    output="S1 compile successful with warnings.",
                ),
                CompileFailureStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    reason="S1 Compile error: header not found.",
                    output="S1 error: fatal error: 'missing.h' file not found",
                ),
            ],
            (another_sample_student_id, None): [
                CompileSuccessStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    output="S2 compile successful.",
                ),
                CompileFailureStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    reason="S2 Compile error: syntax error.",
                    output="S2 error: syntax error on line 10",
                ),

            ]
        },
        ExecuteStage: {
            (sample_student_id, sample_testcase_id): [
                ExecuteSuccessStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    testcase_id=sample_testcase_id,
                    execute_config_mtime=datetime.now(),
                    output_files=OutputFileMapping({
                        FileID.STDOUT: OutputFile(
                            file_id=FileID.STDOUT,
                            content="S1_TC_A_Output: Hello World\n",
                        ),
                        FileID("log.txt"): OutputFile(
                            file_id=FileID("log.txt"),
                            content="S1_TC_A_Log data.",
                        ),
                    }),
                ),
                ExecuteFailureStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    testcase_id=sample_testcase_id,
                    reason="S1_TC_A Execution timeout after 5s.",
                ),
            ],
            (sample_student_id, another_sample_testcase_id): [
                ExecuteSuccessStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    testcase_id=another_sample_testcase_id,
                    execute_config_mtime=datetime.now(),
                    output_files=OutputFileMapping({
                        FileID.STDOUT: OutputFile(
                            file_id=FileID.STDOUT,
                            content="S1_TC_B_Result: 42\n",
                        ),
                    }),
                ),
                ExecuteFailureStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    testcase_id=another_sample_testcase_id,
                    reason="S1_TC_B Runtime error: division by zero.",
                ),
            ],
            (another_sample_student_id, sample_testcase_id): [
                ExecuteSuccessStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    testcase_id=sample_testcase_id,
                    execute_config_mtime=datetime.now(),
                    output_files=OutputFileMapping({
                        FileID.STDOUT: OutputFile(
                            file_id=FileID.STDOUT,
                            content="S2_TC_A_Output: Test successful\n",
                        ),
                    }),
                ),
                ExecuteFailureStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    testcase_id=sample_testcase_id,
                    reason="S2_TC_A Execution failed due to permissions.",
                ),
            ],
            (another_sample_student_id, another_sample_testcase_id): [
                ExecuteSuccessStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    testcase_id=another_sample_testcase_id,
                    execute_config_mtime=datetime.now(),
                    output_files=OutputFileMapping({
                        FileID.STDOUT: OutputFile(
                            file_id=FileID.STDOUT,
                            content="S2_TC_B_Output: Completed.\n",
                        ),
                        FileID("err.txt"): OutputFile(
                            file_id=FileID("err.txt"),
                            content="S2_TC_B_Error log.",
                        ),
                    }),
                ),
                ExecuteFailureStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    testcase_id=another_sample_testcase_id,
                    reason="S2_TC_B Runtime error: out of memory.",
                ),
            ],
        },
        TestStage: {
            (sample_student_id, sample_testcase_id): [
                TestSuccessStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    testcase_id=sample_testcase_id,
                    test_config_mtime=datetime.now(),
                    test_result_output_files=TestResultOutputFileMapping(),
                ),
                TestFailureStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    testcase_id=sample_testcase_id,
                    reason="S1_TC_A Test case failed: output did not match.",
                ),
            ],
            (sample_student_id, another_sample_testcase_id): [
                TestSuccessStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    testcase_id=another_sample_testcase_id,
                    test_config_mtime=datetime.now(),
                    test_result_output_files=TestResultOutputFileMapping(),
                ),
                TestFailureStudentStageResult.create_instance(
                    student_id=sample_student_id,
                    testcase_id=another_sample_testcase_id,
                    reason="S1_TC_B Test case failed: incorrect data structure.",
                ),
            ],
            (another_sample_student_id, sample_testcase_id): [
                TestSuccessStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    testcase_id=sample_testcase_id,
                    test_config_mtime=datetime.now(),
                    test_result_output_files=TestResultOutputFileMapping(),
                ),
                TestFailureStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    testcase_id=sample_testcase_id,
                    reason="S2_TC_A Test case failed: report mismatch.",
                ),
            ],
            (another_sample_student_id, another_sample_testcase_id): [
                TestSuccessStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    testcase_id=another_sample_testcase_id,
                    test_config_mtime=datetime.now(),
                    test_result_output_files=TestResultOutputFileMapping(),
                ),
                TestFailureStudentStageResult.create_instance(
                    student_id=another_sample_student_id,
                    testcase_id=another_sample_testcase_id,
                    reason="S2_TC_B Test case failed: CSV format error.",
                ),
            ],
        }
    }

    patterns: list[
        dict[
            tuple[StudentID, TestCaseID | None],
            tuple[AbstractStudentStageResult],
        ],
    ] = []
    for result_index_pattern in itertools.product(range(2), repeat=4):
        pattern = {}
        for testcase_id in sample_testcase_id, another_sample_testcase_id:
            for student_id in sample_student_id, another_sample_student_id:
                result_lst = []
                for stage_type, which in zip(
                        (BuildStage, CompileStage, ExecuteStage, TestStage),
                        result_index_pattern,
                ):
                    result_samples = table[stage_type].get((student_id, testcase_id))
                    if result_samples is None:
                        result_samples = table[stage_type][student_id, None]
                    result_lst.append(result_samples[which])
                pattern[(student_id, testcase_id)] = tuple(result_lst)
        patterns.append(pattern)

    return (
        (sample_student_id, another_sample_student_id),
        (sample_testcase_id, another_sample_testcase_id),
        patterns,
    )


def test_put_and_get_all_results_for_multiple_students(repo, generate_results_patterns):
    student_ids, testcase_ids, patterns = generate_results_patterns

    for pattern in patterns:
        # update
        for student_id in student_ids:
            for testcase_id in testcase_ids:
                for result in pattern[student_id, testcase_id]:
                    repo.put(result)
        # readout
        for student_id in student_ids:
            for testcase_id in testcase_ids:
                for j, stage in enumerate([
                    BuildStage(),
                    CompileStage(),
                    ExecuteStage(testcase_id),
                    TestStage(testcase_id),
                ]):
                    result = repo.get(student_id, stage)
                    result_true = pattern[student_id, testcase_id][j]
                    _assert_stage_results_are_equal(result, result_true)


def test_get_timestamp_initially_returns_none(repo, sample_student_id: StudentID):
    """
    結果がまだ保存されていない学生IDに対して、get_timestamp が None を返すことを確認します。
    """
    assert repo.get_timestamp(sample_student_id) is None


def test_get_timestamp_updates_on_put(repo, sample_student_id: StudentID):
    """
    put 操作後に get_timestamp が時刻を更新することを確認します。
    """
    # 初期状態を確認
    assert repo.get_timestamp(sample_student_id) is None

    # put 操作を実行
    time.sleep(0.001)  # 1ミリ秒待機
    initial_put_time = datetime.now()
    result = BuildSuccessStudentStageResult.create_instance(
        student_id=sample_student_id,
        submission_folder_checksum=123,
    )
    repo.put(result)

    # 時刻が更新されたことを確認
    timestamp = repo.get_timestamp(sample_student_id)
    assert timestamp is not None
    assert isinstance(timestamp, datetime)
    assert timestamp > initial_put_time


def test_get_timestamp_updates_on_delete(repo, sample_student_id: StudentID):
    """
    delete 操作後に get_timestamp が時刻を更新することを確認します。
    """
    # まず結果をputして、更新時刻がセットされている状態にする
    initial_result = CompileSuccessStudentStageResult.create_instance(
        student_id=sample_student_id,
        output="Initial compile output",
    )
    repo.put(initial_result)
    initial_timestamp = repo.get_timestamp(sample_student_id)
    assert isinstance(initial_timestamp, datetime)

    # delete 操作の前に少し待つ（時刻の差を明確にするため）
    time.sleep(0.001)  # 1ミリ秒待機
    delete_operation_time = datetime.now()

    # delete 操作を実行
    repo.delete(sample_student_id, CompileStage())

    # 時刻が更新されたことを確認
    timestamp_after_delete = repo.get_timestamp(sample_student_id)
    assert isinstance(timestamp_after_delete, datetime)
    # delete 操作前の時刻よりも新しいこと
    assert timestamp_after_delete > initial_timestamp
    # delete 操作を実行した時刻以降であること
    assert timestamp_after_delete >= delete_operation_time


def test_get_timestamp_does_not_change_on_exists(repo, sample_student_id, sample_testcase_id):
    """
    exists 操作では get_timestamp が時刻を変更しないことを確認します。
    """
    # まず結果をputして、更新時刻がセットされている状態にする
    result = ExecuteSuccessStudentStageResult.create_instance(
        student_id=sample_student_id,
        testcase_id=sample_testcase_id,
        execute_config_mtime=datetime.now(),
        output_files=OutputFileMapping(),
    )
    repo.put(result)
    initial_timestamp = repo.get_timestamp(sample_student_id)
    assert isinstance(initial_timestamp, datetime)

    # exists 操作を実行
    # existsの前に少し待って、existsが更新を起こさないことをより明確にする
    time.sleep(0.001)  # 1ミリ秒待機

    repo.exists(sample_student_id, ExecuteStage(sample_testcase_id))

    # 時刻が変わっていないことを確認 (完全一致)
    timestamp_after_exists = repo.get_timestamp(sample_student_id)
    assert timestamp_after_exists is not None
    assert timestamp_after_exists == initial_timestamp


def test_get_timestamp_does_not_change_on_get(repo, sample_student_id, sample_testcase_id):
    """
    get 操作では get_timestamp が時刻を変更しないことを確認します。
    """
    # まず結果をputして、更新時刻がセットされている状態にする
    result = TestSuccessStudentStageResult.create_instance(
        student_id=sample_student_id,
        testcase_id=sample_testcase_id,
        test_config_mtime=datetime.now(),
        test_result_output_files=TestResultOutputFileMapping(),
    )
    repo.put(result)
    initial_timestamp = repo.get_timestamp(sample_student_id)
    assert isinstance(initial_timestamp, datetime)

    # get 操作を実行
    # getの前に少し待って、getが更新を起こさないことをより明確にする
    time.sleep(0.001)  # 1ミリ秒待機
    repo.get(sample_student_id, TestStage(sample_testcase_id))

    # 時刻が変わっていないことを確認 (完全一致)
    timestamp_after_get = repo.get_timestamp(sample_student_id)
    assert timestamp_after_get is not None
    assert timestamp_after_get.isoformat(timespec='microseconds') == initial_timestamp.isoformat(
        timespec='microseconds')
