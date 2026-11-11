from copy import deepcopy

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QVBoxLayout, QDialog

from autoprogen.control.widget_testcase_config_edit import TestCaseConfigEditWidget
from autoprogen.domain.model.testcase_config import TestCaseConfig
from autoprogen.domain.model.value import TestCaseID
from autoprogen.usecase.global_settings import GlobalSettingsGetUseCase
from autoprogen.usecase.testcase_config import TestCaseGetUseCase, TestCasePutUseCase
from autoprogen.usecase.test_test_stage import TestTestStageUseCase
from autoprogen.util.app_logging import create_logger


class TestCaseConfigEditDialog(QDialog):
    """テストケース設定を編集し、内容が変わった場合だけ保存する。"""

    _logger = create_logger()

    def __init__(
            self,
            parent: QObject = None,
            *,
            testcase_id: TestCaseID,
            global_settings_get_usecase: GlobalSettingsGetUseCase,
            test_test_stage_usecase: TestTestStageUseCase,
            testcase_get_usecase: TestCaseGetUseCase,
            testcase_put_usecase: TestCasePutUseCase,
    ):
        """指定されたテストケースの編集ダイアログを初期化する。"""
        super().__init__(parent)

        self._testcase_id = testcase_id
        self._global_settings_get_usecase = global_settings_get_usecase
        self._test_test_stage_usecase = test_test_stage_usecase
        self._testcase_get_usecase = testcase_get_usecase
        self._testcase_put_usecase = testcase_put_usecase
        self._initial_config: TestCaseConfig | None = None
        self._has_changes = False

        self._init_ui()

    @property
    def has_changes(self) -> bool:
        """ダイアログを開いてから設定内容が変更されたかを返す。"""
        return self._has_changes

    def _init_ui(self):
        """編集対象の設定を読み込み、画面へ反映する。"""
        self.setWindowTitle(f"テストケースの編集 - {self._testcase_id!s}")
        self.setModal(True)
        self.resize(1200, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_testcase_edit = TestCaseConfigEditWidget(
            self,
            global_settings_get_usecase=self._global_settings_get_usecase,
            test_test_stage_usecase=self._test_test_stage_usecase,
        )
        config = self._testcase_get_usecase.execute(
            testcase_id=self._testcase_id
        )
        # 編集用ウィジェットによる参照先の変更に備え、比較用の値を独立して保持する。
        self._initial_config = deepcopy(config)
        self._w_testcase_edit.set_data(config)
        layout.addWidget(self._w_testcase_edit)

        self._logger.info(
            f"Configuration of testcase {self._testcase_id!s} loaded\n"
            f"Current value: {config}"
        )

    def closeEvent(self, evt: QCloseEvent):
        """編集前後の内容を比較し、変更された設定だけを保存する。"""
        config = self._w_testcase_edit.get_data()
        self._has_changes = config != self._initial_config
        if not self._has_changes:
            super().closeEvent(evt)
            return

        self._testcase_put_usecase.execute(config)

        self._logger.info(
            f"Configuration of testcase {self._testcase_id!s} saved\n"
            f"Current value: {config}"
        )
        super().closeEvent(evt)
