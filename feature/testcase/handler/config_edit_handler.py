from datetime import datetime

from feature.testcase.handler.interface import (
    ITestCaseConfigEditView,
    ITestCaseConfigEditHandler,
)
from shared.domain.entity.testcase import TestCaseConfigEntity
from shared.domain.interface.gateway import ICurrentDatetimeGateway
from shared.domain.value.execute_config import TestCaseExecuteConfig
from shared.domain.value.identifier import TestCaseID
from shared.domain.value.test_config import TestCaseTestConfig


class TestCaseConfigEditHandler(ITestCaseConfigEditHandler):
    """Handler - DomainとViewの橋渡し"""

    def __init__(
            self,
            *,
            view: ITestCaseConfigEditView,
            current_datetime_gateway: ICurrentDatetimeGateway,
    ):
        self._view = view
        self._current_datetime_gateway = current_datetime_gateway
        self._testcase_id: TestCaseID | None = None
        self._execute_config_mtime: datetime | None = None
        self._test_config_mtime: datetime | None = None

        # ViewにHandlerを注入
        view.set_handler(self)

    def set_data(self, config: TestCaseConfigEntity) -> None:
        """DomainオブジェクトをViewに設定"""
        self._testcase_id = config.testcase_id
        self._execute_config_mtime = config.execute_config.mtime
        self._test_config_mtime = config.test_config.mtime

        # 子ウィジェットにデータを設定
        self._view.get_input_files_widget().set_data(config.execute_config.input_file_collection)
        self._view.get_execute_options_widget().set_data(config.execute_config.options)
        self._view.get_expected_output_files_widget().set_data(
            config.test_config.expected_output_file_collection)
        self._view.get_test_options_widget().set_data(config.test_config.options)

    def get_data(self) -> TestCaseConfigEntity:
        """ViewからDomainオブジェクトを構築"""
        assert self._testcase_id is not None
        assert self._execute_config_mtime is not None
        assert self._test_config_mtime is not None

        # 子ウィジェットからデータを取得
        input_files = self._view.get_input_files_widget().get_data()
        execute_options = self._view.get_execute_options_widget().get_data()
        expected_output_files = self._view.get_expected_output_files_widget().get_data()
        test_options = self._view.get_test_options_widget().get_data()

        return TestCaseConfigEntity(
            testcase_id=self._testcase_id,
            execute_config=TestCaseExecuteConfig(
                input_file_collection=input_files,
                options=execute_options,
                mtime=self._execute_config_mtime,
            ),
            test_config=TestCaseTestConfig(
                expected_output_file_collection=expected_output_files,
                options=test_options,
                mtime=self._test_config_mtime,
            ),
        )

    def on_run_test_requested(self) -> None:
        """テスト実行要求の処理"""
        current_file_id = self._view.get_current_expected_file_id()
        if current_file_id is None:
            return

        # 期待出力ファイルを取得
        expected_output_file_collection = self._view.get_expected_output_files_widget().get_data()
        expected_output_file = expected_output_file_collection.find(current_file_id)

        # テストオプションを取得
        test_config_options = self._view.get_test_options_widget().get_data()

        # テスト実行
        self._view.get_test_tester_widget().run_and_update(
            expected_output_file=expected_output_file,
            test_config_options=test_config_options,
        )
