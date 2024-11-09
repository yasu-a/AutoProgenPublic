from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QTabBar, QLabel, QWidget

from controls.res.fonts import get_font
from controls.res.icons import get_icon
from controls.widget_testcase_execute_options import TestCaseExecuteConfigOptionsEditWidget
from controls.widget_testcase_input_files_edit import TestCaseInputFilesEditWidget
from controls.widget_testcase_output_files_edit import TestCaseExpectedOutputFilesEditWidget
from controls.widget_testcase_test_config_options import TestCaseTestConfigOptionsEditWidget
from domain.models.execute_config import TestCaseExecuteConfig
from domain.models.test_config import TestCaseTestConfig
from domain.models.testcase_config import TestCaseConfig


class TestCaseConfigEditWidget(QTabWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._testcase_id = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        if "execute":
            container = QWidget(self)
            self.addTab(container, "")

            layout = QVBoxLayout()
            container.setLayout(layout)

            label = QLabel("入力ストリームの構成", self)
            label.setFont(get_font(bold=True))
            layout.addWidget(label)

            self._w_input_files_edit = TestCaseInputFilesEditWidget(self)
            layout.addWidget(self._w_input_files_edit)

            label = QLabel("実行のオプション", self)
            label.setFont(get_font(bold=True))
            layout.addWidget(label)

            self._w_execute_config_options_edit = TestCaseExecuteConfigOptionsEditWidget(self)
            layout.addWidget(self._w_execute_config_options_edit)

        if "test":
            container = QWidget(self)
            self.addTab(container, "")

            layout = QVBoxLayout()
            container.setLayout(layout)

            label = QLabel("出力ストリームの自動テスト構成", self)
            label.setFont(get_font(bold=True))
            layout.addWidget(label)

            self._w_expected_output_files_edit = TestCaseExpectedOutputFilesEditWidget(self)
            layout.addWidget(self._w_expected_output_files_edit)

            label = QLabel("自動テストのオプション", self)
            label.setFont(get_font(bold=True))
            layout.addWidget(label)

            self._w_test_config_options_edit = TestCaseTestConfigOptionsEditWidget(self)
            layout.addWidget(self._w_test_config_options_edit)

        # タブを左横にする
        self.setTabPosition(QTabWidget.West)  # これだけだと文字が90度傾く
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

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, config: TestCaseConfig):
        self._testcase_id = config.testcase_id
        self._w_input_files_edit.set_data(
            config.execute_config._input_files,
        )
        self._w_execute_config_options_edit.set_data(
            config.execute_config._options,
        )
        self._w_expected_output_files_edit.set_data(
            config.test_config.expected_output_files,
        )
        self._w_test_config_options_edit.set_data(
            config.test_config.options,
        )

    @pyqtSlot()
    def get_data(self) -> TestCaseConfig:
        assert self._testcase_id is not None
        config = TestCaseConfig(
            testcase_id=self._testcase_id,
            execute_config=TestCaseExecuteConfig(
                input_files=self._w_input_files_edit.get_data(),
                options=self._w_execute_config_options_edit.get_data(),
            ),
            test_config=TestCaseTestConfig(
                expected_output_files=self._w_expected_output_files_edit.get_data(),
                options=self._w_test_config_options_edit.get_data(),
            ),
        )
        return config
