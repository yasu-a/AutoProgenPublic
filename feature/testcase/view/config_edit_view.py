from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QTabBar, QLabel, QWidget, QHBoxLayout

from feature.testcase.handler.interface import ITestCaseConfigEditView, \
    ITestCaseConfigEditHandler
# 子ウィジェットは既存のものを使用（これらはdomainに依存しているが、Viewはそれらへのアクセサを提供するだけ）
from feature.testcase.view.widget_testcase_execute_options import \
    TestCaseExecuteConfigOptionsEditWidget
from feature.testcase.view.widget_testcase_input_files_edit import TestCaseInputFilesEditWidget
from feature.testcase.view.widget_testcase_output_files_edit import \
    TestCaseExpectedOutputFilesEditWidget
from feature.testcase.view.widget_testcase_test_config_options import \
    TestCaseTestConfigOptionsEditWidget
from feature.testcase.view.widget_testcase_test_config_tester import TestCaseTestConfigTesterWidget
from shared.view.style.font import get_font
from shared.view.style.icon import get_icon


class TestCaseConfigEditView(QTabWidget, ITestCaseConfigEditView):
    """Pure UI - No domain logic"""

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._handler: ITestCaseConfigEditHandler

        self._init_ui()

    def set_handler(self, handler: ITestCaseConfigEditHandler) -> None:
        """Handlerを注入（DI）"""
        # noinspection PyAttributeOutsideInit
        self._handler = handler

    def _init_ui(self):
        # 実行タブ
        container_execute = QWidget(self)
        self.addTab(container_execute, "")

        layout_execute = QVBoxLayout()
        container_execute.setLayout(layout_execute)

        label = QLabel("入力ストリームの構成", self)
        label.setFont(get_font(bold=True))
        layout_execute.addWidget(label)

        self._w_input_files_edit = TestCaseInputFilesEditWidget(self)
        layout_execute.addWidget(self._w_input_files_edit)

        label = QLabel("実行のオプション", self)
        label.setFont(get_font(bold=True))
        layout_execute.addWidget(label)

        self._w_execute_config_options_edit = TestCaseExecuteConfigOptionsEditWidget(self)
        layout_execute.addWidget(self._w_execute_config_options_edit)

        # テストタブ
        container_test = QWidget(self)
        self.addTab(container_test, "")

        layout_test = QHBoxLayout()
        container_test.setLayout(layout_test)

        # 左側
        layout_left = QVBoxLayout()
        layout_test.addLayout(layout_left)

        label = QLabel("出力ストリームの自動テスト構成", self)
        label.setFont(get_font(bold=True))
        layout_left.addWidget(label)

        self._w_expected_output_files_edit = TestCaseExpectedOutputFilesEditWidget(self)
        layout_left.addWidget(self._w_expected_output_files_edit)

        label = QLabel("自動テストのオプション", self)
        label.setFont(get_font(bold=True))
        layout_left.addWidget(label)

        self._w_test_config_options_edit = TestCaseTestConfigOptionsEditWidget(self)
        layout_left.addWidget(self._w_test_config_options_edit)

        # 右側
        layout_right = QVBoxLayout()
        layout_test.addLayout(layout_right)

        self._w_test_config_tester = TestCaseTestConfigTesterWidget(self)
        layout_right.addWidget(self._w_test_config_tester)

        # タブの設定
        self.setTabPosition(QTabWidget.West)
        self.tabBar().setTabIcon(0, get_icon("run", rotate=90))
        self.tabBar().setTabButton(
            0,
            QTabBar.LeftSide,
            QLabel("実行の構成", self),
        )
        self.tabBar().setTabIcon(1, get_icon("checkbox", rotate=90))
        self.tabBar().setTabButton(
            1,
            QTabBar.LeftSide,
            QLabel("自動テストの構成", self),
        )

        # シグナル接続
        self._w_test_config_tester.run_requested.connect(self.__on_run_test_requested)

    @pyqtSlot()
    def __on_run_test_requested(self):
        """テスト実行要求をHandlerに転送"""
        self._handler.on_run_test_requested()

    # ===== ITestCaseConfigEditView実装 =====
    def get_input_files_widget(self):
        return self._w_input_files_edit

    def get_execute_options_widget(self):
        return self._w_execute_config_options_edit

    def get_expected_output_files_widget(self):
        return self._w_expected_output_files_edit

    def get_test_options_widget(self):
        return self._w_test_config_options_edit

    def get_test_tester_widget(self):
        return self._w_test_config_tester

    def get_current_expected_file_id(self):
        return self._w_expected_output_files_edit.get_current_file_id()
