from PyQt5.QtCore import QObject, Qt, pyqtSlot
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QDialog, QHBoxLayout, \
    QMessageBox, QInputDialog, QGridLayout, QLabel, QDoubleSpinBox

from app_logging import create_logger
from controls.widget_button_box import ButtonBox
from controls.widget_plain_text_edit import PlainTextEdit
from domain.models.testcase import ExecuteConfigInputFiles, TestCaseConfig, ExecuteConfigOptions
from domain.models.values import TestCaseID
from service_provider import get_testcase_edit_service


class TestCaseExecuteConfigInputFilesEditWidget(QWidget):
    _logger = create_logger()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._w_tab = QTabWidget(self)
        layout.addWidget(self._w_tab)

        self._buttons = ButtonBox(self, orientation=Qt.Vertical)
        self._buttons.add_button("標準入力の追加", "add-stdin")
        self._buttons.add_button("ファイルの追加", "add-file")
        self._buttons.add_button("ファイル名の変更", "rename")
        self._buttons.add_button("削除", "delete")
        layout.addWidget(self._buttons)

    def _init_signals(self):
        self._buttons.triggered.connect(self.__buttons_triggered)

    __STDIN_TAB_TITLE = "＜標準入力＞"

    @pyqtSlot(ExecuteConfigInputFiles)
    def set_data(self, input_files: ExecuteConfigInputFiles):
        self._w_tab.clear()
        for filename, content_bytes in input_files.items():
            te = PlainTextEdit()
            te.set_show_editing_symbols(False)
            te.setPlainText(content_bytes.decode("utf-8"))
            if filename is None:
                self._w_tab.addTab(te, self.__STDIN_TAB_TITLE)
            else:
                self._w_tab.addTab(te, filename)

    @pyqtSlot()
    def get_data(self) -> ExecuteConfigInputFiles:
        # apply editing to instance and return it
        input_files = ExecuteConfigInputFiles()
        for i_tab in range(self._w_tab.count()):
            filename = self._w_tab.tabText(i_tab)
            content_string = self._w_tab.widget(i_tab).toPlainText()
            if filename == self.__STDIN_TAB_TITLE:
                filename = None
            input_files[filename] = content_string.encode("utf-8")
        return input_files

    def __find_filename(self, filename: str | None) -> int | None:
        if filename is None:
            filename = self.__STDIN_TAB_TITLE
        for i_tab in range(self._w_tab.count()):
            if self._w_tab.tabText(i_tab) == filename:
                return i_tab
        return None

    def __has_filename(self, filename: str | None) -> bool:
        return self.__find_filename(filename) is not None

    @pyqtSlot()
    def dispatch_action_add_stdin(self):
        if self.__has_filename(self.__STDIN_TAB_TITLE):
            QMessageBox.critical(
                self,
                "標準入力の追加",
                "標準入力がすでに存在します。"
            )
            return
        te = PlainTextEdit()
        te.set_show_editing_symbols(False)
        te.setPlainText("")
        self._w_tab.insertTab(0, te, self.__STDIN_TAB_TITLE)

    @pyqtSlot()
    def dispatch_action_add_file(self):
        filename, ok = QInputDialog.getText(
            self,
            "ファイルの追加",
            "新しい入力ファイル名を入力してください",
            text="",
        )
        if not ok:
            return
        filename = filename.strip()
        if not filename:
            return
        if self.__has_filename(filename):
            QMessageBox.critical(
                self,
                "ファイルの追加",
                f"同じ名前の入力ファイルが存在します。"
            )
            return
        if filename == self.__STDIN_TAB_TITLE:
            QMessageBox.critical(
                self,
                "ファイルの追加",
                "そのファイル名は追加できません。"
            )
            return
        te = PlainTextEdit()
        te.set_show_editing_symbols(False)
        te.setPlainText("")
        self._w_tab.insertTab(0, te, filename)

    @pyqtSlot(str)
    def dispatch_action_rename(self, filename: str):
        new_filename, ok = QInputDialog.getText(
            self,
            "ファイル名の変更",
            f"「{filename}」の新しいファイル名を入力してください",
            text=filename,
        )
        if not ok:
            return
        new_filename = new_filename.strip()
        if not new_filename:
            return
        if self.__has_filename(new_filename):
            QMessageBox.critical(
                self,
                "ファイル名の変更",
                f"同じ名前の入力ファイルが既に存在します。"
            )
            return
        i_tab = self.__find_filename(filename)
        assert i_tab is not None
        self._w_tab.setTabText(i_tab, new_filename)

    @pyqtSlot(str)
    def dispatch_action_delete(self, filename: str):
        res = QMessageBox.critical(
            self,
            "ファイルの削除",
            f"ファイル「{filename}」を削除しますか？",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if res != QMessageBox.Yes:
            return
        i_tab = self.__find_filename(filename)
        assert i_tab is not None
        self._w_tab.removeTab(i_tab)

    def _current_filename(self) -> str | None:
        i_tab = self._w_tab.currentIndex()
        if i_tab < 0:
            return None
        return self._w_tab.tabText(i_tab)

    @pyqtSlot(str)
    def __buttons_triggered(self, name: str):
        if name == "add-stdin":
            self.dispatch_action_add_stdin()
        elif name == "add-file":
            self.dispatch_action_add_file()
        elif name == "rename":
            filename = self._current_filename()
            if filename is None:
                return
            self.dispatch_action_rename(filename)
        elif name == "delete":
            filename = self._current_filename()
            if filename is None:
                return
            self.dispatch_action_delete(filename)
        else:
            assert False, name


class TestCaseExecuteConfigOptionsEditWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        layout_content = QGridLayout()
        layout_root.addLayout(layout_content)

        layout_content.addWidget(QLabel("実行のタイムアウト（秒）", self), 0, 0)

        self._sb_timeout = QDoubleSpinBox(self)
        self._sb_timeout.setMinimum(0.1)
        self._sb_timeout.setMaximum(30.0)
        self._sb_timeout.setSingleStep(0.1)
        self._sb_timeout.setDecimals(1)
        layout_content.addWidget(self._sb_timeout, 0, 1)

        layout_root.addStretch(1)

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, options: ExecuteConfigOptions):
        self._sb_timeout.setValue(options.timeout)

    @pyqtSlot()
    def get_data(self) -> ExecuteConfigOptions:
        options = ExecuteConfigOptions(
            timeout=self._sb_timeout.value(),
        )
        return options


class TestCaseConfigEditWidget(QTabWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_execute_config_input_file_edit = TestCaseExecuteConfigInputFilesEditWidget(self)
        self.addTab(self._w_execute_config_input_file_edit, "入力ストリーム")

        self._w_execute_config_options_edit = TestCaseExecuteConfigOptionsEditWidget(self)
        self.addTab(self._w_execute_config_options_edit, "実行のオプション")

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, config: TestCaseConfig):
        self._w_execute_config_input_file_edit.set_data(config.execute_config.input_files)
        self._w_execute_config_options_edit.set_data(config.execute_config.options)

    @pyqtSlot()
    def get_data(self) -> TestCaseConfig:
        config = TestCaseConfig.create_new()
        config.execute_config.input_files = self._w_execute_config_input_file_edit.get_data()
        config.execute_config.options = self._w_execute_config_options_edit.get_data()
        return config


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
