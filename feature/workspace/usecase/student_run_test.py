from feature.workspace.usecase.interface import IStudentRunTestStageUseCase
from shared.domain.error import TestServiceError, MatchServiceError
from shared.domain.interface.gateway import ICurrentDatetimeGateway
from shared.domain.model.stage import StageElement, Stage
from shared.domain.model.student_result import ExecuteStageResultEntity, TestStageResultEntity
from shared.domain.service.match import MatchGetBestService
from shared.domain.service.student_stage_path_result import StudentPutStagePathResultEntityService, \
    StudentGetStagePathResultMapService
from shared.domain.value.identifier import FileID
from shared.domain.value.identifier import StudentID
from shared.domain.value.output_file import OutputFile
from shared.domain.value.student_stage_result import TestResultOutputFileCollection
from shared.domain.value.test_result_output_file_entry import TestResultTestedOutputFileEntry, \
    TestResultAbsentOutputFileEntry, TestResultUnexpectedOutputFileEntry
from shared.infra.repository.testcase_config import TestCaseConfigRepository


class StudentRunTestStageUseCase(IStudentRunTestStageUseCase):  # TODO: ロジックからStudentTestServiceを分離
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
            student_put_stage_result_service: StudentPutStagePathResultEntityService,
            student_get_stage_result_map_service: StudentGetStagePathResultMapService,
            match_get_best_service: MatchGetBestService,
            current_datetime_gateway: ICurrentDatetimeGateway,
    ):
        self._testcase_config_repo = testcase_config_repo
        self._student_put_stage_result_service = student_put_stage_result_service
        self._student_get_stage_result_map_service = student_get_stage_result_map_service
        self._match_get_best_service = match_get_best_service
        self._current_datetime_gateway = current_datetime_gateway

    def execute(self, student_id: StudentID, stage_path: tuple[StageElement, ...]) -> None:
        stage_element = next((e for e in stage_path if e.stage == Stage.TEST), None)
        assert stage_element is not None
        testcase_id = stage_element.testcase_id
        assert testcase_id is not None

        try:
            # 実行結果を取得する
            results_map = self._student_get_stage_result_map_service.execute(
                student_id=student_id,
                stage_path=list(stage_path),
            )
            execute_result = next((r for e, r in results_map.items() if e.stage == Stage.EXECUTE), None)

            if execute_result is None:
                raise TestServiceError(
                    reason="実行結果が見つかりません",
                )
            if not execute_result.is_success:
                raise TestServiceError(
                    reason="失敗した実行のテストはできません",
                )
            assert isinstance(execute_result, ExecuteStageResultEntity)

            # テストケースのテスト構成を読み込む
            test_config = self._testcase_config_repo.get(
                testcase_id=testcase_id,
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
                        raise TestServiceError(
                            reason=e.reason,
                        )
                    file_test_result = TestResultTestedOutputFileEntry(
                        file_id=file_id,
                        actual=actual_output_file,
                        expected=expected_output_file,
                        test_result=match_result,
                    )
                else:
                    assert False, "unreachable"
                test_result_output_file_collection.put(file_test_result)
        except TestServiceError as e:
            self._student_put_stage_result_service.execute(
                result=TestStageResultEntity(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    test_config_mtime=None,
                    test_result_output_file_collection=None,
                    failure_reason=e.reason,
                    timestamp=self._current_datetime_gateway.execute(),
                    is_success=False,
                    error_summary=e.reason,
                )
            )
        else:
            test_config_mtime = self._testcase_config_repo.get(
                testcase_id=testcase_id,
            ).test_config.mtime  # TODO: UoWの導入
            self._student_put_stage_result_service.execute(
                result=TestStageResultEntity(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    test_config_mtime=test_config_mtime,
                    test_result_output_file_collection=test_result_output_file_collection,
                    failure_reason=None,
                    timestamp=self._current_datetime_gateway.execute(),
                    is_success=True,
                    error_summary=None,
                )
            )
