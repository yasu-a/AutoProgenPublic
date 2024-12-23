from domain.errors import TestServiceError, MatchServiceError
from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.output_file import OutputFile
from domain.models.output_file_test_result import OutputFileTestResult
from domain.models.stages import ExecuteStage
from domain.models.student_stage_result import TestFailureStudentStageResult, \
    TestSuccessStudentStageResult, TestResultOutputFileMapping, ExecuteSuccessStudentStageResult
from domain.models.test_result_output_file_entry import TestResultTestedOutputFileEntry, \
    AbstractTestResultOutputFileEntry, TestResultAbsentOutputFileEntry, \
    TestResultUnexpectedOutputFileEntry
from domain.models.values import FileID
from domain.models.values import StudentID, TestCaseID
from infra.repositories.student_stage_result import StudentStageResultRepository
from services.match import MatchGetBestService
from services.testcase_config import TestCaseConfigGetTestConfigMtimeService, \
    TestCaseConfigGetService


class StudentRunTestStageUseCase:  # TODO: ロジックからStudentTestServiceを分離
    def __init__(
            self,
            *,
            testcase_config_get_service: TestCaseConfigGetService,
            student_stage_result_repo: StudentStageResultRepository,
            testcase_config_get_test_config_mtime_service: TestCaseConfigGetTestConfigMtimeService,
            match_get_best_service: MatchGetBestService,
    ):
        self._testcase_config_get_service = testcase_config_get_service
        self._student_stage_result_repo = student_stage_result_repo
        self._testcase_config_get_test_config_mtime_service = testcase_config_get_test_config_mtime_service
        self._match_get_best_service = match_get_best_service

    def execute(self, student_id: StudentID, testcase_id: TestCaseID) -> None:
        try:
            # 実行結果を取得する
            if not self._student_stage_result_repo.exists(
                    student_id=student_id,
                    stage=ExecuteStage(testcase_id=testcase_id),
            ):
                raise TestServiceError(
                    reason="実行結果が見つかりません",
                )
            execute_result = self._student_stage_result_repo.get(
                student_id=student_id,
                stage=ExecuteStage(testcase_id=testcase_id),
            )
            if not execute_result.is_success:
                raise TestServiceError(
                    reason="失敗した実行のテストはできません",
                )
            assert isinstance(execute_result, ExecuteSuccessStudentStageResult)

            # テストケースのテスト構成を読み込む
            test_config = self._testcase_config_get_service.execute(
                testcase_id=testcase_id,
            ).test_config

            # テストの実行 - それぞれの出力ファイルについてテストを実行する
            output_file_id_test_result_mapping: dict[FileID, AbstractTestResultOutputFileEntry] = {}
            # v 正解
            expected_output_file_ids: set[FileID] = set(test_config.expected_output_files.keys())
            # v 実行結果
            actual_output_file_ids: set[FileID] = set(execute_result.output_files.keys())
            for file_id in expected_output_file_ids | actual_output_file_ids:
                expected_output_file: ExpectedOutputFile | None \
                    = test_config.expected_output_files.get(file_id)
                # ^ None if not found
                actual_output_file: OutputFile | None \
                    = execute_result.output_files.get(file_id)
                # ^ None if not found

                if actual_output_file is not None and expected_output_file is None:
                    # 実行結果には含まれているがテストケースにはない出力ファイル
                    file_test_result = TestResultUnexpectedOutputFileEntry(
                        file_id=file_id,
                        actual=actual_output_file,
                    )
                elif actual_output_file is None and expected_output_file is not None:
                    # 実行結果には含まれていないがテストケースで出力が期待されているファイル
                    file_test_result = TestResultAbsentOutputFileEntry(
                        file_id=file_id,
                        expected=expected_output_file,
                    )
                elif actual_output_file is not None and expected_output_file is not None:
                    # 実行結果とテストケースの両方に含まれているファイル
                    #  -> テストを行う
                    try:
                        match_service_result = self._match_get_best_service.execute(
                            content_string=actual_output_file.content_string,
                            test_config_options=test_config.options,
                            patterns=expected_output_file.patterns,
                        )
                    except MatchServiceError as e:
                        raise TestServiceError(
                            reason=e.reason,
                        )
                    file_test_result = TestResultTestedOutputFileEntry(
                        file_id=file_id,
                        actual=actual_output_file,
                        expected=expected_output_file,
                        test_result=OutputFileTestResult(
                            matched_tokens=match_service_result.matched_tokens,
                            nonmatched_tokens=match_service_result.nonmatched_tokens,
                        ),
                    )
                else:
                    assert False, "unreachable"
                output_file_id_test_result_mapping[file_id] = file_test_result

            # すべての出力ファイルの結果を生成
            test_result_output_files = TestResultOutputFileMapping(
                output_file_id_test_result_mapping
            )
        except TestServiceError as e:
            self._student_stage_result_repo.put(
                result=TestFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    reason=e.reason,
                )
            )
        else:
            test_config_mtime = self._testcase_config_get_test_config_mtime_service.execute(
                testcase_id=testcase_id,
            )  # TODO: UoWの導入
            self._student_stage_result_repo.put(
                result=TestSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    test_config_mtime=test_config_mtime,
                    test_result_output_files=test_result_output_files,
                )
            )
