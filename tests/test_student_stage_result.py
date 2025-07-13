# import itertools
# from datetime import datetime
# from typing import Optional

# import pytest

# from application.dependency.repositories import get_student_stage_result_repository
# from domain.errors import RepositoryItemNotFoundError
# from domain.models.output_file import OutputFileMapping, OutputFile
# from domain.models.student_stage_result import (
#     BuildSuccessStudentStageResult,
#     BuildFailureStudentStageResult,
#     CompileSuccessStudentStageResult,
#     CompileFailureStudentStageResult,
#     ExecuteSuccessStudentStageResult,
#     ExecuteFailureStudentStageResult,
#     TestSuccessStudentStageResult,
#     TestFailureStudentStageResult,
#     TestResultOutputFileMapping,
# )
# from domain.models.values import (
#     StudentID,
#     TestCaseID,
#     FileID,
# )


# @pytest.fixture
# def repo():
#     return get_student_stage_result_repository()


# @pytest.fixture
# def student_id_1(sample_student_ids):
#     return sample_student_ids[0]


# @pytest.fixture
# def student_id_2(sample_student_ids):
#     return sample_student_ids[1]


# @pytest.fixture
# def testcase_id_1():
#     return TestCaseID("TestCase-1")


# @pytest.fixture
# def testcase_id_2():
#     return TestCaseID(
#         "TestCase-2"
#     )


# # --- Fixtures for all result types (success/failure) as mappers ---
# @pytest.fixture
# def build_success_result(student_id_1, student_id_2):
#     def _mapper(student_id: StudentID, /, updated=False):
#         try:
#             checksum = {
#                 (student_id_1, False): 12,
#                 (student_id_1, True): 34,
#                 (student_id_2, False): 56,
#                 (student_id_2, True): 78
#             }[student_id, updated]
#         except KeyError:
#             raise AssertionError(f"unexpected student_id: {student_id}")
#         return BuildSuccessStudentStageResult.create_instance(
#             student_id=student_id,
#             submission_folder_checksum=checksum,
#         )

#     return _mapper


# @pytest.fixture
# def build_failure_result(student_id_1, student_id_2):
#     def _mapper(student_id: StudentID, /, updated=False):
#         try:
#             reason = {
#                 (student_id_1, False): "build failed for student 1",
#                 (student_id_1, True): "build failed for student 1 updated",
#                 (student_id_2, False): "build failed for student 2",
#                 (student_id_2, True): "build failed for student 2 updated"
#             }[student_id, updated]
#         except KeyError:
#             raise AssertionError(f"unexpected student_id: {student_id}")
#         return BuildFailureStudentStageResult.create_instance(
#             student_id=student_id,
#             reason=reason,
#         )

#     return _mapper


# @pytest.fixture
# def compile_success_result(student_id_1, student_id_2):
#     def _mapper(student_id: StudentID, /, updated=False):
#         try:
#             output = {
#                 (student_id_1, False): "compile ok for student 1",
#                 (student_id_1, True): "compile ok for student 1 updated",
#                 (student_id_2, False): "compile ok for student 2",
#                 (student_id_2, True): "compile ok for student 2 updated"
#             }[student_id, updated]
#         except KeyError:
#             raise AssertionError(f"unexpected student_id: {student_id}")
#         return CompileSuccessStudentStageResult.create_instance(
#             student_id=student_id,
#             output=output,
#         )

#     return _mapper


# @pytest.fixture
# def compile_failure_result(student_id_1, student_id_2):
#     def _mapper(student_id: StudentID, /, updated=False):
#         try:
#             reason, output = {
#                 (student_id_1, False): (
#                     "compile error for student 1",
#                     "error log 1",
#                 ),
#                 (student_id_1, True): (
#                     "compile error for student 1 updated",
#                     "error log 1 updated",
#                 ),
#                 (student_id_2, False): (
#                     "compile error for student 2",
#                     "error log 2",
#                 ),
#                 (student_id_2, True): (
#                     "compile error for student 2 updated",
#                     "error log 2 updated",
#                 ),
#             }[student_id, updated]
#         except KeyError:
#             raise AssertionError(f"unexpected student_id: {student_id}")
#         return CompileFailureStudentStageResult.create_instance(
#             student_id=student_id,
#             reason=reason,
#             output=output,
#         )

#     return _mapper


# @pytest.fixture
# def execute_success_result(student_id_1, student_id_2, testcase_id_1, testcase_id_2):
#     def _mapper(student_id: StudentID, testcase_id: TestCaseID, /, updated=False):
#         try:
#             content, mtime = {
#                 (student_id_1, testcase_id_1, False): (
#                     "ok 1-1",
#                     datetime.fromisoformat("2023-01-01T00:00:01"),
#                 ),
#                 (student_id_1, testcase_id_1, True): (
#                     "ok 1-1 updated",
#                     datetime.fromisoformat("2023-01-01T00:00:11"),
#                 ),
#                 (student_id_1, testcase_id_2, False): (
#                     "ok 1-2",
#                     datetime.fromisoformat("2023-01-01T00:00:02"),
#                 ),
#                 (student_id_1, testcase_id_2, True): (
#                     "ok 1-2 updated",
#                     datetime.fromisoformat("2023-01-01T00:00:12"),
#                 ),
#                 (student_id_2, testcase_id_1, False): (
#                     "ok 2-1",
#                     datetime.fromisoformat("2023-01-01T00:00:03"),
#                 ),
#                 (student_id_2, testcase_id_1, True): (
#                     "ok 2-1 updated",
#                     datetime.fromisoformat("2023-01-01T00:00:13"),
#                 ),
#                 (student_id_2, testcase_id_2, False): (
#                     "ok 2-2",
#                     datetime.fromisoformat("2023-01-01T00:00:04"),
#                 ),
#                 (student_id_2, testcase_id_2, True): (
#                     "ok 2-2 updated",
#                     datetime.fromisoformat("2023-01-01T00:00:14"),
#                 ),
#             }[student_id, testcase_id, updated]
#         except KeyError:
#             raise AssertionError(
#                 f"unexpected student_id or testcase_id: {student_id}, {testcase_id}")
#         files = OutputFileMapping(
#             {FileID.STDOUT: OutputFile(file_id=FileID.STDOUT, content=content)})
#         return ExecuteSuccessStudentStageResult.create_instance(
#             student_id=student_id,
#             testcase_id=testcase_id,
#             execute_config_mtime=mtime,
#             output_files=files,
#         )

#     return _mapper


# @pytest.fixture
# def execute_failure_result(student_id_1, student_id_2, testcase_id_1, testcase_id_2):
#     def _mapper(student_id: StudentID, testcase_id: TestCaseID, /, updated=False):
#         try:
#             reason = {
#                 (student_id_1, testcase_id_1, False): "exec fail 1-1",
#                 (student_id_1, testcase_id_1, True): "exec fail 1-1 updated",
#                 (student_id_1, testcase_id_2, False): "exec fail 1-2",
#                 (student_id_1, testcase_id_2, True): "exec fail 1-2 updated",
#                 (student_id_2, testcase_id_1, False): "exec fail 2-1",
#                 (student_id_2, testcase_id_1, True): "exec fail 2-1 updated",
#                 (student_id_2, testcase_id_2, False): "exec fail 2-2",
#                 (student_id_2, testcase_id_2, True): "exec fail 2-2 updated"
#             }[student_id, testcase_id, updated]
#         except KeyError:
#             raise AssertionError(
#                 f"unexpected student_id or testcase_id: {student_id}, {testcase_id}")
#         return ExecuteFailureStudentStageResult.create_instance(
#             student_id=student_id,
#             testcase_id=testcase_id,
#             reason=reason,
#         )

#     return _mapper


# @pytest.fixture
# def test_success_result(student_id_1, student_id_2, testcase_id_1, testcase_id_2):
#     def _mapper(student_id: StudentID, testcase_id: TestCaseID, /, updated=False):
#         try:
#             mtime = {
#                 (student_id_1, testcase_id_1, False): datetime.fromisoformat("2023-01-02T00:00:01"),
#                 (student_id_1, testcase_id_1, True): datetime.fromisoformat("2023-01-02T00:00:11"),
#                 (student_id_1, testcase_id_2, False): datetime.fromisoformat("2023-01-02T00:00:02"),
#                 (student_id_1, testcase_id_2, True): datetime.fromisoformat("2023-01-02T00:00:12"),
#                 (student_id_2, testcase_id_1, False): datetime.fromisoformat("2023-01-02T00:00:03"),
#                 (student_id_2, testcase_id_1, True): datetime.fromisoformat("2023-01-02T00:00:13"),
#                 (student_id_2, testcase_id_2, False): datetime.fromisoformat("2023-01-02T00:00:04"),
#                 (student_id_2, testcase_id_2, True): datetime.fromisoformat("2023-01-02T00:00:14"),
#             }[student_id, testcase_id, updated]
#         except KeyError:
#             raise AssertionError(
#                 f"unexpected student_id or testcase_id: {student_id}, {testcase_id}"
#             )
#         return TestSuccessStudentStageResult.create_instance(
#             student_id=student_id,
#             testcase_id=testcase_id,
#             test_config_mtime=mtime,
#             test_result_output_files=TestResultOutputFileMapping(),
#         )

#     return _mapper


# @pytest.fixture
# def test_failure_result(student_id_1, student_id_2, testcase_id_1, testcase_id_2):
#     def _mapper(student_id: StudentID, testcase_id: TestCaseID, /, updated=False):
#         try:
#             reason = {
#                 (student_id_1, testcase_id_1, False): "test fail 1-1",
#                 (student_id_1, testcase_id_1, True): "test fail 1-1 updated",
#                 (student_id_1, testcase_id_2, False): "test fail 1-2",
#                 (student_id_1, testcase_id_2, True): "test fail 1-2 updated",
#                 (student_id_2, testcase_id_1, False): "test fail 2-1",
#                 (student_id_2, testcase_id_1, True): "test fail 2-1 updated",
#                 (student_id_2, testcase_id_2, False): "test fail 2-2",
#                 (student_id_2, testcase_id_2, True): "test fail 2-2 updated"
#             }[student_id, testcase_id, updated]
#         except KeyError:
#             raise AssertionError(
#                 f"unexpected student_id or testcase_id: {student_id}, {testcase_id}"
#             )
#         return TestFailureStudentStageResult.create_instance(
#             student_id=student_id,
#             testcase_id=testcase_id,
#             reason=reason,
#         )

#     return _mapper


# # --- Parametrize pattern for all result types ---
# ALL_RESULT_MAPPERS = [
#     "build_success_result",
#     "build_failure_result",
#     "compile_success_result",
#     "compile_failure_result",
#     "execute_success_result",
#     "execute_failure_result",
#     "test_success_result",
#     "test_failure_result",
# ]


# def get_positional_arg_names(func) -> tuple[str, ...]:
#     import inspect
#     sig = inspect.signature(func)
#     names = []
#     for param in sig.parameters.values():
#         if param.kind == inspect.Parameter.POSITIONAL_ONLY:
#             names.append(param.name)
#     return tuple(names)


# @pytest.fixture
# def get_single_result(request, student_id_1, testcase_id_1):
#     def _mapper(
#             result_fixture: str,
#             student_id: Optional[StudentID] = None,
#             testcase_id: Optional[TestCaseID] = None,
#             updated=False,
#     ):
#         if student_id is None:
#             student_id = student_id_1
#         if testcase_id is None:
#             testcase_id = testcase_id_1

#         mapper = request.getfixturevalue(result_fixture)

#         if get_positional_arg_names(mapper) == ("student_id",):
#             return mapper(student_id, updated=updated)
#         elif get_positional_arg_names(mapper) == ("student_id", "testcase_id"):
#             return mapper(student_id, testcase_id, updated=updated)
#         else:
#             raise AssertionError(f"unexpected arg names: {get_positional_arg_names(mapper)}")

#     return _mapper


# # --- Helper for equality ---
# def _assert_stage_results_are_equal(r1, r2):
#     assert type(r1) is type(r2)
#     assert r1.student_id == r2.student_id
#     assert r1.stage == r2.stage
#     if hasattr(r1, "submission_folder_checksum"):
#         assert r1.submission_folder_checksum == r2.submission_folder_checksum
#     if hasattr(r1, "reason"):
#         assert r1.reason == r2.reason
#     if hasattr(r1, "output"):
#         assert r1.output == r2.output
#     if hasattr(r1, "execute_config_mtime"):
#         assert r1.execute_config_mtime == r2.execute_config_mtime
#     if hasattr(r1, "output_files"):
#         assert r1.output_files.to_json() == r2.output_files.to_json()
#     if hasattr(r1, "test_config_mtime"):
#         assert r1.test_config_mtime == r2.test_config_mtime
#     if hasattr(r1, "test_result_output_files"):
#         assert r1.test_result_output_files.to_json() == r2.test_result_output_files.to_json()


# def _are_results_equal(r1, r2):
#     try:
#         _assert_stage_results_are_equal(r1, r2)
#     except AssertionError:
#         return False
#     else:
#         return True


# # --- Parametrized test for all result types ---
# @pytest.mark.parametrize(
#     "result_fixture",
#     ALL_RESULT_MAPPERS,
# )
# def test_put_get_exists_delete(
#         repo,
#         result_fixture,
#         get_single_result,
# ):
#     result = get_single_result(result_fixture)
#     # exists -> False
#     assert not repo.exists(result.student_id, result.stage)
#     # get -> (not found)
#     with pytest.raises(RepositoryItemNotFoundError):
#         repo.get(result.student_id, result.stage)
#     # *** put result
#     repo.put(result)
#     # exists -> True
#     assert repo.exists(result.student_id, result.stage)
#     # verify content
#     _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))
#     # *** delete
#     repo.delete(result.student_id, result.stage)
#     # exists -> False
#     assert not repo.exists(result.student_id, result.stage)
#     # get -> (not found)
#     with pytest.raises(RepositoryItemNotFoundError):
#         repo.get(result.student_id, result.stage)
#     # *** delete again -> (not found)
#     with pytest.raises(RepositoryItemNotFoundError):
#         repo.delete(result.student_id, result.stage)


# # --- 複雑な操作シーケンス ---
# @pytest.mark.parametrize(
#     "result_fixture",
#     ALL_RESULT_MAPPERS,
# )
# def test_complex_sequence(
#         repo,
#         result_fixture,
#         get_single_result,
# ):
#     result = get_single_result(result_fixture)
#     updated_result = get_single_result(result_fixture, updated=True)
#     # *** put result
#     repo.put(result)
#     # exists -> True
#     assert repo.exists(result.student_id, result.stage)
#     # verify content
#     _assert_stage_results_are_equal(result, repo.get(result.student_id, result.stage))
#     # *** put updated result (overwrite)
#     repo.put(updated_result)
#     # exists -> True (still exists)
#     assert repo.exists(result.student_id, result.stage)
#     # verify updated content
#     retrieved = repo.get(result.student_id, result.stage)
#     _assert_stage_results_are_equal(updated_result, retrieved)
#     # *** delete
#     repo.delete(result.student_id, result.stage)
#     # exists -> False
#     assert not repo.exists(result.student_id, result.stage)
#     # get -> (not found)
#     with pytest.raises(RepositoryItemNotFoundError):
#         repo.get(result.student_id, result.stage)


# # --- 生徒ごとの独立性テスト ---
# @pytest.mark.parametrize(
#     ("student_1_result_fixture", "student_2_result_fixture"),
#     tuple(itertools.combinations(ALL_RESULT_MAPPERS, r=2)),
# )
# def test_student_isolation(
#         repo,
#         get_single_result,
#         student_1_result_fixture,
#         student_2_result_fixture,
#         student_id_1,
#         student_id_2,
# ):
#     result_s_1 = get_single_result(student_1_result_fixture, student_id=student_id_1)
#     result_s_2 = get_single_result(student_2_result_fixture, student_id=student_id_2)
#     # exits s1 -> False
#     assert not repo.exists(result_s_1.student_id, result_s_1.stage)
#     # exits s2 -> False
#     assert not repo.exists(result_s_2.student_id, result_s_2.stage)
#     # *** put s1
#     repo.put(result_s_1)
#     # exits s1 -> True
#     assert repo.exists(result_s_1.student_id, result_s_1.stage)
#     # verify updated content s2
#     assert repo.get(result_s_1.student_id, result_s_1.stage) == result_s_1
#     # exists s2 -> False
#     assert not repo.exists(result_s_2.student_id, result_s_2.stage)
#     # *** put s2
#     repo.put(result_s_2)
#     # exits s1 -> True
#     assert repo.exists(result_s_1.student_id, result_s_1.stage)
#     # verify updated content s1
#     assert repo.get(result_s_1.student_id, result_s_1.stage) == result_s_1
#     # exits s2 -> True
#     assert repo.exists(result_s_2.student_id, result_s_2.stage)
#     # verify updated content s2
#     assert repo.get(result_s_2.student_id, result_s_2.stage) == result_s_2
#     # *** delete s2
#     repo.delete(result_s_2.student_id, result_s_2.stage)
#     # exits s1 -> True
#     assert repo.exists(result_s_1.student_id, result_s_1.stage)
#     # verify updated content s2
#     assert repo.get(result_s_1.student_id, result_s_1.stage) == result_s_1
#     # exists s2 -> False
#     assert not repo.exists(result_s_2.student_id, result_s_2.stage)


# # --- testcaseごとの独立性テスト ---
# @pytest.mark.parametrize(
#     ("testcase_1_result_fixture", "testcase_2_result_fixture"),
#     tuple(itertools.combinations(ALL_RESULT_MAPPERS, r=2)),
# )
# def test_testcase_isolation(
#         repo,
#         get_single_result,
#         testcase_1_result_fixture,
#         testcase_2_result_fixture,
#         student_id_1,
#         testcase_id_1,
#         testcase_id_2,
# ):
#     result_tc_1 = get_single_result(testcase_1_result_fixture, testcase_id=testcase_id_1)
#     result_tc_2 = get_single_result(testcase_2_result_fixture, testcase_id=testcase_id_2)
#     if result_tc_1.stage == result_tc_2.stage:
#         # 他方が片方を上書きする関係なのでスキップ
#         pytest.skip("testcase_1_result_fixture == testcase_2_result_fixture")
#     # exits tc1 -> False
#     assert not repo.exists(result_tc_1.student_id, result_tc_1.stage)
#     # exits tc2 -> False
#     assert not repo.exists(result_tc_2.student_id, result_tc_2.stage)
#     # *** put tc1
#     repo.put(result_tc_1)
#     # exits tc1 -> True
#     assert repo.exists(result_tc_1.student_id, result_tc_1.stage)
#     # verify updated content tc1
#     assert repo.get(result_tc_1.student_id, result_tc_1.stage) == result_tc_1
#     # exists tc2 -> False
#     assert not repo.exists(result_tc_2.student_id, result_tc_2.stage)
#     # *** put tc2
#     repo.put(result_tc_2)
#     # exits tc1 -> True
#     assert repo.exists(result_tc_1.student_id, result_tc_1.stage)
#     # verify updated content tc1
#     assert repo.get(result_tc_1.student_id, result_tc_1.stage) == result_tc_1
#     # exits tc2 -> True
#     assert repo.exists(result_tc_2.student_id, result_tc_2.stage)
#     # verify updated content tc2
#     assert repo.get(result_tc_2.student_id, result_tc_2.stage) == result_tc_2
#     # *** delete tc2
#     repo.delete(result_tc_2.student_id, result_tc_2.stage)
#     # exits tc1 -> True
#     assert repo.exists(result_tc_1.student_id, result_tc_1.stage)
#     # verify updated content tc1
#     assert repo.get(result_tc_1.student_id, result_tc_1.stage) == result_tc_1
#     # exists tc2 -> False
#     assert not repo.exists(result_tc_2.student_id, result_tc_2.stage)


# # --- success/failureの片方を他方が上書きする挙動の確認 ---
# @pytest.mark.parametrize(
#     ("success_result_fixture", "failure_result_fixture"),
#     [
#         ("build_success_result", "build_failure_result"),
#         ("compile_success_result", "compile_failure_result"),
#         ("execute_success_result", "execute_failure_result"),
#         ("test_success_result", "test_failure_result"),
#         ("build_failure_result", "build_success_result"),
#         ("compile_failure_result", "compile_success_result"),
#         ("execute_failure_result", "execute_success_result"),
#         ("test_failure_result", "test_success_result"),
#     ],
# )
# def test_success_overwrite_with_failure(
#         repo,
#         get_single_result,
#         success_result_fixture,
#         failure_result_fixture,
# ):
#     success_result = get_single_result(success_result_fixture)
#     failure_result = get_single_result(failure_result_fixture)

#     # *** put success result
#     repo.put(success_result)
#     # exists -> True
#     assert repo.exists(success_result.student_id, success_result.stage)
#     # verify success content
#     retrieved_success = repo.get(success_result.student_id, success_result.stage)
#     _assert_stage_results_are_equal(success_result, retrieved_success)

#     # *** put failure result (overwrite success)
#     repo.put(failure_result)
#     # exists -> True (still exists)
#     assert repo.exists(failure_result.student_id, failure_result.stage)
#     # verify failure content (success was overwritten)
#     retrieved_failure = repo.get(failure_result.student_id, failure_result.stage)
#     _assert_stage_results_are_equal(failure_result, retrieved_failure)
#     # verify success content is gone
#     assert not _are_results_equal(retrieved_failure, success_result)

#     # *** put success result again (overwrite failure)
#     repo.put(success_result)
#     # exists -> True (still exists)
#     assert repo.exists(success_result.student_id, success_result.stage)
#     # verify success content (failure was overwritten)
#     retrieved_success_again = repo.get(success_result.student_id, success_result.stage)
#     _assert_stage_results_are_equal(success_result, retrieved_success_again)
#     # verify failure content is gone
#     assert not _are_results_equal(retrieved_success_again, failure_result)


# # --- タイムスタンプのテスト ---
# @pytest.mark.parametrize(
#     "result_fixture",
#     ALL_RESULT_MAPPERS,
# )
# def test_timestamp_on_put_and_delete(
#         repo,
#         get_single_result,
#         result_fixture,
#         student_id_1,
# ):
#     from time import sleep
#     result = get_single_result(result_fixture, student_id=student_id_1)
#     # put前はNone
#     assert repo.get_timestamp(student_id_1) is None
#     sleep(0.001)
#     t0 = datetime.now()
#     # putでタイムスタンプ更新
#     repo.put(result)
#     t1 = repo.get_timestamp(student_id_1)
#     assert t1 is not None and t1 > t0
#     sleep(0.001)
#     t2 = datetime.now()
#     # deleteでさらにタイムスタンプ更新
#     repo.delete(result.student_id, result.stage)
#     t3 = repo.get_timestamp(student_id_1)
#     assert t3 is not None and t3 > t1 and t3 >= t2


# @pytest.mark.parametrize(
#     "result_fixture",
#     ALL_RESULT_MAPPERS,
# )
# def test_timestamp_not_update_on_get_exists(
#         repo,
#         get_single_result,
#         result_fixture,
#         student_id_1,
# ):
#     result = get_single_result(result_fixture, student_id=student_id_1)
#     # *** put result
#     repo.put(result)
#     t0 = repo.get_timestamp(student_id_1)
#     from time import sleep
#     sleep(0.001)
#     # existsではタイムスタンプ変化しない
#     repo.exists(result.student_id, result.stage)
#     t1 = repo.get_timestamp(student_id_1)
#     assert t1 == t0
#     sleep(0.001)
#     # getでもタイムスタンプ変化しない
#     repo.get(result.student_id, result.stage)
#     t2 = repo.get_timestamp(student_id_1)
#     assert t2 == t0
