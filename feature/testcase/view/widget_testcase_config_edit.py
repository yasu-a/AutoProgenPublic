from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QTabBar, QLabel, QWidget, QHBoxLayout

from feature.testcase.view.widget_testcase_execute_options import \
    TestCaseExecuteConfigOptionsEditWidget
from feature.testcase.view.widget_testcase_input_files_edit import TestCaseInputFilesEditWidget
from feature.testcase.view.widget_testcase_output_files_edit import \
    TestCaseExpectedOutputFilesEditWidget
from feature.testcase.view.widget_testcase_test_config_options import \
    TestCaseTestConfigOptionsEditWidget
from feature.testcase.view.widget_testcase_test_config_tester import TestCaseTestConfigTesterWidget
from shared.domain.entity.testcase import TestCaseConfigEntity
from shared.domain.value.execute_config import TestCaseExecuteConfig
from shared.domain.value.test_config import TestCaseTestConfig
from shared.view.style.font import get_font
from shared.view.style.icon import get_icon


class TestCaseConfigEditWidget(QTabWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._testcase_id = None
        self._execute_config_mtime = None
        self._test_config_mtime = None

        self._init_ui()

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

        # シグナル接続
        self._w_test_config_tester.run_requested.connect(self.__w_test_config_tester_run_requested)

    @pyqtSlot()
    def __w_test_config_tester_run_requested(self):
        current_file_id = self._w_expected_output_files_edit.get_current_file_id()
        if current_file_id is None:  # ファイルタブが選択されていなかったら
            return
        self._w_test_config_tester.run_and_update(
            expected_output_file=self._w_expected_output_files_edit.get_data().find(
                current_file_id),
            test_config_options=self._w_test_config_options_edit.get_data(),
        )

    @pyqtSlot()
    def set_data(self, config: TestCaseConfigEntity):
        self._testcase_id = config.testcase_id
        self._execute_config_mtime = config.execute_config.mtime
        self._test_config_mtime = config.test_config.mtime
        self._w_input_files_edit.set_data(
            config.execute_config.input_file_collection,
        )
        self._w_execute_config_options_edit.set_data(
            config.execute_config.options,
        )
        self._w_expected_output_files_edit.set_data(
            config.test_config.expected_output_file_collection,
        )
        self._w_test_config_options_edit.set_data(
            config.test_config.options,
        )

    @pyqtSlot()
    def get_data(self) -> TestCaseConfigEntity:
        assert self._testcase_id is not None
        assert self._execute_config_mtime is not None
        assert self._test_config_mtime is not None
        config = TestCaseConfigEntity(
            testcase_id=self._testcase_id,
            execute_config=TestCaseExecuteConfig(
                input_file_collection=self._w_input_files_edit.get_data(),
                options=self._w_execute_config_options_edit.get_data(),
                mtime=self._execute_config_mtime,
            ),
            test_config=TestCaseTestConfig(
                expected_output_file_collection=self._w_expected_output_files_edit.get_data(),
                options=self._w_test_config_options_edit.get_data(),
                mtime=self._test_config_mtime,
            ),
        )
        return config
