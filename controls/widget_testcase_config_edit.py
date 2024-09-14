from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout

from controls.widget_testcase_execute_options import TestCaseExecuteConfigOptionsEditWidget
from controls.widget_testcase_input_file_mapping import TestCaseInputFileMappingEditWidget
from controls.widget_testcase_output_file_mapping import TestCaseExpectedOutputFileMappingEditWidget
from controls.widget_testcase_test_config_options import TestCaseTestConfigOptionsEditWidget
from domain.models.testcase import TestCaseConfig, TestCaseExecuteConfig, TestCaseTestConfig


class TestCaseConfigEditWidget(QTabWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_input_files_edit = TestCaseInputFileMappingEditWidget(self)
        self.addTab(self._w_input_files_edit, "入力ストリームの構成")

        self._w_execute_config_options_edit = TestCaseExecuteConfigOptionsEditWidget(self)
        self.addTab(self._w_execute_config_options_edit, "実行のオプション")

        self._w_expected_output_files_edit = TestCaseExpectedOutputFileMappingEditWidget(self)
        self.addTab(self._w_expected_output_files_edit, "出力ストリームの自動テスト構成")

        self._w_test_config_options_edit = TestCaseTestConfigOptionsEditWidget(self)
        self.addTab(self._w_test_config_options_edit, "自動テストのオプション")

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, config: TestCaseConfig):
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
        config = TestCaseConfig(
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
