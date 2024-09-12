from PyQt5.QtCore import QObject
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QVBoxLayout, QDialog

from app_logging import create_logger
from application.dependency.services import get_testcase_edit_service
from controls.widget_testcase_config_edit import TestCaseConfigEditWidget
from domain.models.values import TestCaseID


class TestCaseConfigEditDialog(QDialog):
    _logger = create_logger()

    def __init__(self, parent: QObject = None, *, testcase_id: TestCaseID):
        super().__init__(parent)

        self._testcase_id = testcase_id

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle(f"テストケースの編集 - {self._testcase_id!s}")
        self.setModal(True)
        self.resize(1000, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_testcase_edit = TestCaseConfigEditWidget(self)
        config = get_testcase_edit_service().get_config(
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
        get_testcase_edit_service().set_config(
            testcase_id=self._testcase_id,
            config=config,
        )

        self._logger.info(
            f"Configuration of testcase {self._testcase_id!s} saved\n"
            f"Current value: {config}"
        )
