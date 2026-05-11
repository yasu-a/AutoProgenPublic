from PyQt5.QtCore import QObject
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QVBoxLayout, QDialog

from control.widget_testcase_config_edit import TestCaseConfigEditWidget
from domain.model.value import TestCaseID
from usecase.global_settings import GlobalSettingsGetUseCase
from usecase.testcase_config import TestCaseGetUseCase, TestCasePutUseCase
from usecase.test_test_stage import TestTestStageUseCase
from util.app_logging import create_logger


class TestCaseConfigEditDialog(QDialog):
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
        super().__init__(parent)

        self._testcase_id = testcase_id
        self._global_settings_get_usecase = global_settings_get_usecase
        self._test_test_stage_usecase = test_test_stage_usecase
        self._testcase_get_usecase = testcase_get_usecase
        self._testcase_put_usecase = testcase_put_usecase

        self._init_ui()

    def _init_ui(self):
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
        self._w_testcase_edit.set_data(config)
        layout.addWidget(self._w_testcase_edit)

        self._logger.info(
            f"Configuration of testcase {self._testcase_id!s} loaded\n"
            f"Current value: {config}"
        )

    def closeEvent(self, evt: QCloseEvent):
        config = self._w_testcase_edit.get_data()
        self._testcase_put_usecase.execute(config)

        self._logger.info(
            f"Configuration of testcase {self._testcase_id!s} saved\n"
            f"Current value: {config}"
        )
