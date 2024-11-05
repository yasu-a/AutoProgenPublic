from enum import IntEnum, auto

from PyQt5.QtCore import QObject, Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QTabWidget, QMessageBox, QInputDialog

from controls.widget_button_box import ButtonBox
from controls.widget_plain_text_edit import PlainTextEdit
from domain.models.input_file import InputFile, InputFileMapping
from domain.models.values import FileID, SpecialFileType
from utils.app_logging import create_logger


# TODO: TestCaseExpectedOutputFileMappingEditWidgetと機能が重複 抽象化
# noinspection DuplicatedCode
class TestCaseInputFileMappingEditWidget(QWidget):
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

    __STDIN_TAB_TITLE = "[標準入力]"

    @classmethod
    def __file_id_to_tab_title(cls, file_id: FileID) -> str:
        if file_id.is_special:
            assert file_id.special_file_type == SpecialFileType.STDIN, file_id
            tab_title = cls.__STDIN_TAB_TITLE
        else:
            tab_title = str(file_id)
        return tab_title

    @classmethod
    def __tab_title_to_file_id(cls, tab_title: str) -> FileID:
        if tab_title == cls.__STDIN_TAB_TITLE:
            return FileID.STDIN
        else:
            return FileID(tab_title)

    def __find_tab_title(self, tab_title: str) -> int | None:  # None if not found
        for i_tab in range(self._w_tab.count()):
            if self._w_tab.tabText(i_tab) == tab_title:
                return i_tab
        return None

    def __has_tab_title(self, tab_title: str) -> bool:
        return self.__find_tab_title(tab_title) is not None

    def __insert_tab(
            self,
            *,
            tab_title: str,
            insert_at: int = None,
            content_string: str = "",
    ) -> None:
        if insert_at is None:
            insert_at = self._w_tab.count()
        # noinspection PyTypeChecker
        te = PlainTextEdit(self)
        te.set_show_editing_symbols(False)
        te.setPlainText(content_string)
        self._w_tab.insertTab(insert_at, te, tab_title)

    def __rename_tab(
            self,
            *,
            current_tab_title: str,
            new_tab_title: str,
    ) -> None:
        i_tab = self.__find_tab_title(current_tab_title)
        assert i_tab is not None
        self._w_tab.setTabText(i_tab, new_tab_title)

    def __delete_tab(
            self,
            *,
            tab_title: str,
    ) -> None:
        i_tab = self.__find_tab_title(tab_title)
        assert i_tab is not None
        self._w_tab.removeTab(i_tab)

    def _current_tab_title(self) -> str | None:
        i_tab = self._w_tab.currentIndex()
        if i_tab < 0:
            return None
        return self._w_tab.tabText(i_tab)

    @pyqtSlot(InputFileMapping)
    def set_data(self, input_files: InputFileMapping) -> None:
        """
        このウィジェットに入力ファイルのデータを設定します。

        Args:
            input_files (InputFileMapping): 設定する入力ファイルのデータ。
        """
        self._w_tab.clear()
        for file_id, input_file in input_files.items():
            self.__insert_tab(
                tab_title=self.__file_id_to_tab_title(file_id),
                content_string=input_file.content_string,
            )

    @pyqtSlot()
    def get_data(self) -> InputFileMapping:
        """
        このウィジェットの入力ファイルのデータを返します。

        Returns:
            InputFileMapping: 編集された入力ファイルのデータ。
        """
        input_files = InputFileMapping()
        for i_tab in range(self._w_tab.count()):  # 各タブに対して
            # タイトル
            tab_title = self._w_tab.tabText(i_tab)
            file_id = self.__tab_title_to_file_id(tab_title)
            # 内容
            content_string = self._w_tab.widget(i_tab).toPlainText()
            # データに設定
            input_files[file_id] = InputFile(
                file_id=file_id,
                content=content_string,
            )
        return input_files

    @pyqtSlot()
    def dispatch_action_add_stdin(self):
        if self.__has_tab_title(self.__STDIN_TAB_TITLE):
            QMessageBox.critical(
                self,
                "標準入力の追加",
                "標準入力がすでに存在します。"
            )
            return
        self.__insert_tab(tab_title=self.__STDIN_TAB_TITLE, insert_at=0)

    class _NormalTabTitleValidationResult(IntEnum):
        EMPTY = auto()  # 空の入力
        SPECIAL = auto()  # 通常のファイル名でない
        NAME_EXISTS = auto()  # 既に存在するファイル名
        FILE_ID_CONVERSION_FAILURE = auto()  # FileIDに変換できないファイル名
        VALID = auto()  # 正しいファイル名

    def __validate_normal_tab_title_and_show_message(self, new_tab_title: str) \
            -> _NormalTabTitleValidationResult:  # True if valid
        # 空文字
        if not new_tab_title:
            return self._NormalTabTitleValidationResult.EMPTY
        # 標準入力と同じ名前
        if new_tab_title == self.__STDIN_TAB_TITLE:
            QMessageBox.critical(
                self,
                "ファイルの追加",
                "そのファイル名は追加できません。"
            )
            return self._NormalTabTitleValidationResult.SPECIAL
        # 既に同じ名前のファイルが存在する
        if self.__has_tab_title(new_tab_title):
            QMessageBox.critical(
                self,
                "ファイルの追加",
                f"同じ名前の入力ファイルが存在します。"
            )
            return self._NormalTabTitleValidationResult.NAME_EXISTS
        # 一度FileIDに変換してみる
        try:
            _ = FileID(new_tab_title)
        except ValueError:
            QMessageBox.critical(
                self,
                "ファイル名の変更",
                f"不正なファイル名です。"
            )
            return self._NormalTabTitleValidationResult.FILE_ID_CONVERSION_FAILURE
        return self._NormalTabTitleValidationResult.VALID

    @pyqtSlot()
    def dispatch_action_add_file(self):
        new_tab_title = ""
        while True:
            # 入力を要求する
            new_tab_title, ok = QInputDialog.getText(
                self,
                "ファイルの追加",
                "新しい入力ファイル名を入力してください",
                text=new_tab_title,
            )
            # キャンセルされたら中断
            if not ok:
                return
            # 空白を取り除く
            new_tab_title = new_tab_title.strip()
            # 検証
            validation_result = self.__validate_normal_tab_title_and_show_message(new_tab_title)
            if validation_result == self._NormalTabTitleValidationResult.VALID:
                break
            elif validation_result in [self._NormalTabTitleValidationResult.EMPTY]:
                return
            else:
                continue
        # タブを挿入する
        self.__insert_tab(tab_title=new_tab_title)

    @pyqtSlot(str)
    def dispatch_action_rename(self, tab_title: str):
        # 標準入力をリネームしようとしていたらキャンセル
        if tab_title == self.__STDIN_TAB_TITLE:
            return

        new_tab_title = tab_title
        while True:
            # 入力を要求する
            new_tab_title, ok = QInputDialog.getText(
                self,
                "ファイル名の変更",
                f"「{tab_title}」の新しいファイル名を入力してください",
                text=new_tab_title,
            )
            # キャンセルされたら中断
            if not ok:
                return
            # 空白を取り除く
            new_tab_title = new_tab_title.strip()
            # 検証
            validation_result = self.__validate_normal_tab_title_and_show_message(new_tab_title)
            if validation_result == self._NormalTabTitleValidationResult.VALID:
                break
            elif validation_result in [self._NormalTabTitleValidationResult.EMPTY]:
                return
            else:
                continue
        # リネームする
        self.__rename_tab(current_tab_title=tab_title, new_tab_title=new_tab_title)

    @pyqtSlot(str)
    def dispatch_action_delete(self, tab_title: str):
        res = QMessageBox.critical(
            self,
            "ファイルの削除",
            f"ファイル「{tab_title}」を削除しますか？",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if res != QMessageBox.Yes:
            return
        self.__delete_tab(tab_title=tab_title)

    @pyqtSlot(str)
    def __buttons_triggered(self, name: str):
        if name == "add-stdin":
            self.dispatch_action_add_stdin()
        elif name == "add-file":
            self.dispatch_action_add_file()
        elif name == "rename":
            tab_title = self._current_tab_title()
            if tab_title is None:
                return
            self.dispatch_action_rename(tab_title)
        elif name == "delete":
            tab_title = self._current_tab_title()
            if tab_title is None:
                return
            self.dispatch_action_delete(tab_title)
        else:
            assert False, name
