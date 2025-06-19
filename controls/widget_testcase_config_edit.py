from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QTabBar, QLabel, QWidget, QHBoxLayout

from controls.widget_testcase_execute_options import TestCaseExecuteConfigOptionsEditWidget
from controls.widget_testcase_input_files_edit import TestCaseInputFilesEditWidget
from controls.widget_testcase_output_files_edit import TestCaseExpectedOutputFilesEditWidget
from controls.widget_testcase_test_config_options import TestCaseTestConfigOptionsEditWidget
from controls.widget_testcase_test_config_tester import TestCaseTestConfigTesterWidget
from domain.models.execute_config import TestCaseExecuteConfig
from domain.models.test_config import TestCaseTestConfig
from domain.models.testcase_config import TestCaseConfig
from res.fonts import get_font
from res.icons import get_icon


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

            layout = QHBoxLayout()
            container.setLayout(layout)

            if "left":
                layout_left = QVBoxLayout()
                layout.addLayout(layout_left)

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

            if "right":
                layout_right = QVBoxLayout()
                layout.addLayout(layout_right)

                self._w_test_config_tester = TestCaseTestConfigTesterWidget(self)
                layout_right.addWidget(self._w_test_config_tester)

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
        self._w_test_config_tester.run_requested.connect(self.__w_test_config_tester_run_requested)

    @pyqtSlot()
    def __w_test_config_tester_run_requested(self):
        current_file_id = self._w_expected_output_files_edit.get_current_file_id()
        if current_file_id is None:  # ファイルタブが選択されていなかったら
            return
        self._w_test_config_tester.run_and_update(
            expected_output_file=self._w_expected_output_files_edit.get_data()[current_file_id],
            test_config_options=self._w_test_config_options_edit.get_data(),
        )

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
