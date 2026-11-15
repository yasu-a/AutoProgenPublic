from PyQt5.QtCore import QObject

from autoprogen.control.dialog_settings_edit import AbstractSettingsEditDialog
from autoprogen.control.widget_testcase_config_edit import TestCaseConfigEditWidget
from autoprogen.domain.model.testcase_config import TestCaseConfig
from autoprogen.usecase.global_settings import GlobalSettingsGetUseCase
from autoprogen.usecase.test_test_stage import TestTestStageUseCase
from autoprogen.util.app_logging import create_logger


class TestCaseConfigEditDialog(AbstractSettingsEditDialog[TestCaseConfig]):
    """テストケース設定を編集し、内容が変わった場合だけ保存する。"""

    _logger = create_logger()

    def __init__(
            self,
            parent: QObject = None,
            *,
            data: TestCaseConfig,
            global_settings_get_usecase: GlobalSettingsGetUseCase,
            test_test_stage_usecase: TestTestStageUseCase,
    ):
        """指定されたテストケースの編集ダイアログを初期化する。"""
        super().__init__(parent)

        self._testcase_id = data.testcase_id
        self._global_settings_get_usecase = global_settings_get_usecase
        self._test_test_stage_usecase = test_test_stage_usecase
        self._init_ui(data)

    def _init_ui(self, data: TestCaseConfig) -> None:
        """編集対象の設定を読み込み、画面へ反映する。"""
        self.setWindowTitle(f"テストケースの編集 - {self._testcase_id!s}")
        self.setModal(True)
        self.resize(1200, 700)

        self._w_testcase_edit = TestCaseConfigEditWidget(
            self,
            global_settings_get_usecase=self._global_settings_get_usecase,
            test_test_stage_usecase=self._test_test_stage_usecase,
        )
        self.content_layout.addWidget(self._w_testcase_edit)
        self.add_standard_buttons()
        self.set_data(data)

        self._logger.info(
            f"Configuration of testcase {self._testcase_id!s} loaded\n"
            f"Current value: {data}"
        )

    def _set_data(self, data: TestCaseConfig) -> None:
        """テストケース設定を編集Widgetへ反映する。"""
        self._w_testcase_edit.set_data(data)

    def get_data(self) -> TestCaseConfig:
        """編集Widgetから現在のテストケース設定を返す。"""
        return self._w_testcase_edit.get_data()

    def save_data(self, data: TestCaseConfig) -> None:
        """編集内容を確定し、親ダイアログから取得可能な状態にする。"""
        # NOTE: 一覧全体を保存するまで永続化しないため、このダイアログでは保存処理を行わない。
        pass
