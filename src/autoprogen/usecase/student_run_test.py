from autoprogen.domain.error import MatchServiceError
from autoprogen.domain.error.stage.test import ExecuteResultFailedError, ExecuteResultNotFoundError, \
    OutputMatchingError, TestStageError
from autoprogen.domain.model.output_file import OutputFile
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.stage import ExecuteStage
from autoprogen.domain.model.student_stage_result import TestFailureStudentStageResult, \
    TestSuccessStudentStageResult, TestResultOutputFileCollection, ExecuteSuccessStudentStageResult
from autoprogen.domain.model.test_result_output_file_entry import TestResultTestedOutputFileEntry, \
    TestResultAbsentOutputFileEntry, TestResultUnexpectedOutputFileEntry
from autoprogen.domain.model.value import FileID
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.testcase_config import TestCaseConfigRepository
from autoprogen.domain.service.match import MatchGetBestService
from autoprogen.service.student_stage_path_result import StudentPutStageResultService, \
    StudentGetStageResultService
from autoprogen.service.testcase_config import TestCaseConfigGetTestConfigMtimeService


class StudentRunTestStageUseCase:  # TODO: ロジックからStudentTestServiceを分離
    """EXECUTE結果を期待値と照合してTEST結果を保存する。"""

    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
            student_put_stage_result_service: StudentPutStageResultService,
            student_get_stage_result_service: StudentGetStageResultService,
            testcase_config_get_test_config_mtime_service: TestCaseConfigGetTestConfigMtimeService,
            match_get_best_service: MatchGetBestService,
    ) -> None:
        """TESTステージで使用するRepositoryとServiceを受け取る。"""
        self._testcase_config_repo = testcase_config_repo
        self._student_put_stage_result_service = student_put_stage_result_service
        self._student_get_stage_result_service = student_get_stage_result_service
        self._testcase_config_get_test_config_mtime_service = testcase_config_get_test_config_mtime_service
        self._match_get_best_service = match_get_best_service

    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
        """学生一人分のTESTステージを実行して結果を保存する。"""
        try:
            # 実行結果を取得する
            execute_result = self._student_get_stage_result_service.execute(
                student_id=student_id,
                stage_path=stage_path,
                stage=stage_path.get_stage_by_stage_type(ExecuteStage),
            )
            if execute_result is None:
                raise ExecuteResultNotFoundError()
            if not execute_result.is_success:
                raise ExecuteResultFailedError()
            assert isinstance(execute_result, ExecuteSuccessStudentStageResult)

            # テストケースのテスト構成を読み込む
            test_config = self._testcase_config_repo.get(
                testcase_id=stage_path.testcase_id,
            ).test_config

            # テストの実行 - それぞれの出力ファイルについてテストを実行する
            test_result_output_file_collection = TestResultOutputFileCollection()
            # v 正解
            expected_output_file_ids: set[FileID] \
                = set(test_config.expected_output_file_collection.file_ids)
            # v 実行結果
            actual_output_file_ids: set[FileID] \
                = set(execute_result.output_file_collection.file_ids)

            for file_id in expected_output_file_ids | actual_output_file_ids:
                if test_config.expected_output_file_collection.has(file_id):
                    expected_output_file = test_config.expected_output_file_collection.find(file_id)
                else:
                    expected_output_file = None
                # ^ None if not found

                actual_output_file: OutputFile | None
                if execute_result.output_file_collection.has(file_id):
                    actual_output_file = execute_result.output_file_collection.find(file_id)
                else:
                    actual_output_file = None
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
                        match_result = self._match_get_best_service.execute(
                            content_string=actual_output_file.content_string,
                            test_config_options=test_config.options,
                            patterns=expected_output_file.patterns,
                        )
                    except MatchServiceError as e:
                        raise OutputMatchingError(detail=e.reason)
                    file_test_result = TestResultTestedOutputFileEntry(
                        file_id=file_id,
                        actual=actual_output_file,
                        expected=expected_output_file,
                        test_result=match_result,
                    )
                else:
                    assert False, "unreachable"
                test_result_output_file_collection.put(file_test_result)
        except TestStageError as e:
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=TestFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=stage_path.testcase_id,
                    error=e,
                )
            )
        else:
            test_config_mtime = self._testcase_config_get_test_config_mtime_service.execute(
                testcase_id=stage_path.testcase_id,
            )  # TODO: UoWの導入
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=TestSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=stage_path.testcase_id,
                    test_config_mtime=test_config_mtime,
                    test_result_output_file_collection=test_result_output_file_collection,
                )
            )
