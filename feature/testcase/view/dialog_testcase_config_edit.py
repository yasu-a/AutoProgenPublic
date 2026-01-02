from PyQt5.QtCore import QObject
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QVBoxLayout, QDialog

from app.di.gateway import get_current_datetime_gateway
from app.di.usecase import get_testcase_config_get_usecase, \
    get_testcase_config_put_usecase
from feature.testcase.handler.config_edit_handler import TestCaseConfigEditHandler
from feature.testcase.view.config_edit_view import TestCaseConfigEditView
from shared.domain.value.identifier import TestCaseID
from util.app_logging import create_logger


class TestCaseConfigEditDialog(QDialog):
    _logger = create_logger()

    def __init__(self, parent: QObject = None, *, testcase_id: TestCaseID):
        super().__init__(parent)

        self._testcase_id = testcase_id

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle(f"テストケースの編集 - {self._testcase_id!s}")
        self.setModal(True)
        self.resize(1200, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # ViewとHandlerを生成
        view = TestCaseConfigEditView(self)
        handler = TestCaseConfigEditHandler(
            view=view,
            current_datetime_gateway=get_current_datetime_gateway(),
        )

        # データを読み込んで設定
        config = get_testcase_config_get_usecase().execute(
            testcase_id=self._testcase_id
        )
        handler.set_data(config)

        layout.addWidget(view)

        self._controller = handler
        self._view = view

        self._logger.info(
            f"Configuration of testcase {self._testcase_id!s} loaded\n"
            f"Current value: {config}"
        )

    def closeEvent(self, evt: QCloseEvent):
        config = self._controller.get_data()
        get_testcase_config_put_usecase().execute(config)

        self._logger.info(
            f"Configuration of testcase {self._testcase_id!s} saved\n"
            f"Current value: {config}"
        )
