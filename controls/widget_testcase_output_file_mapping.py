import uuid
from enum import IntEnum, auto
from typing import TypeVar, Generic

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QHBoxLayout, QMessageBox, QInputDialog, QWidget, QListWidget, QLineEdit, QLabel,
    QListWidgetItem, QVBoxLayout
)
from PyQt5.QtWidgets import QTabWidget

from controls.widget_button_box import ButtonBox
from domain.models.testcase import InputFileMapping, ExpectedTokenList, \
    AbstractExpectedToken, FloatExpectedToken, TextExpectedToken, ExpectedOutputFile, \
    ExpectedOutputFileMapping
from domain.models.values import FileID, SpecialFileType
from icons import icon

_ET = TypeVar("_ET", bound=AbstractExpectedToken)


class AbstractExpectedOutputFileTokenListItemWidget(QWidget, Generic[_ET]):
    control_triggered_for_item = pyqtSignal(str, uuid.UUID)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._id = uuid.uuid4()

    @classmethod
    def _accept(cls, expected_token: AbstractExpectedToken) -> bool:
        raise NotImplementedError()

    def set_data(self, expected_token: _ET) -> None:
        raise NotImplementedError()

    def get_data(self) -> _ET:
        raise NotImplementedError()

    @classmethod
    def create_instance(cls, expected_token: AbstractExpectedToken, parent: QObject = None) \
            -> "AbstractExpectedOutputFileTokenListItemWidget":
        for sub_cls in cls.__subclasses__():
            if sub_cls._accept(expected_token):
                obj = sub_cls(parent)
                obj.set_data(expected_token)
                return obj
        assert False, expected_token

    def has_same_id(self, other_id: uuid.UUID):
        return self._id == other_id


class ExpectedOutputFileTokenListItemControlButtons(ButtonBox):
    triggered_for_item = pyqtSignal(str, uuid.UUID)

    def __init__(self, parent: QObject = None, *, parent_id: uuid.UUID):
        super().__init__(parent, orientation=Qt.Horizontal)

        self._parent_id = parent_id

        self._init_signals()

    def _init_ui(self):
        super()._init_ui()
        self.add_button("", "move-up", icon=icon("up"))
        self.add_button("", "move-down", icon=icon("down"))
        self.add_button("", "remove", icon=icon("delete"))
        self.setFixedWidth(self.sizeHint().width())

    def _init_signals(self):
        self.triggered.connect(self.__triggered)

    @pyqtSlot(str)
    def __triggered(self, name: str):
        # noinspection PyUnresolvedReferences
        self.triggered_for_item.emit(name, self._parent_id)


class ExpectedOutputFileTextTokenListItemWidget(
    AbstractExpectedOutputFileTokenListItemWidget[TextExpectedToken],
):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("文字列："))

        self._le_value = QLineEdit(self)
        self._le_value.setPlaceholderText("マッチングさせたい文字列を入力してください")
        layout.addWidget(self._le_value)

        self._buttons = ExpectedOutputFileTokenListItemControlButtons(self, parent_id=self._id)
        layout.addWidget(self._buttons)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._buttons.triggered_for_item.connect(self.control_triggered_for_item)

    @classmethod
    def _accept(cls, expected_token: AbstractExpectedToken) -> bool:
        return isinstance(expected_token, TextExpectedToken)

    def set_data(self, expected_token: TextExpectedToken) -> None:
        self._le_value.setText(expected_token.value)

    def get_data(self) -> TextExpectedToken:
        return TextExpectedToken(
            value=self._le_value.text(),
        )


class ExpectedOutputFileFloatTokenListItemWidget(
    AbstractExpectedOutputFileTokenListItemWidget[FloatExpectedToken],
):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("実数値："))

        self._le_value = QLineEdit(self)
        self._le_value.setPlaceholderText("マッチングさせたい実数値を入力してください")
        validator = QDoubleValidator(self)
        validator.setDecimals(6)
        validator.setNotation(QDoubleValidator.ScientificNotation)
        self._le_value.setValidator(validator)
        layout.addWidget(self._le_value)

        self._buttons = ExpectedOutputFileTokenListItemControlButtons(self, parent_id=self._id)
        layout.addWidget(self._buttons)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._buttons.triggered_for_item.connect(self.control_triggered_for_item)

    @classmethod
    def _accept(cls, expected_token: AbstractExpectedToken) -> bool:
        return isinstance(expected_token, FloatExpectedToken)

    def set_data(self, expected_token: FloatExpectedToken) -> None:
        self._le_value.setText(str(expected_token.value))

    def get_data(self) -> FloatExpectedToken:
        return FloatExpectedToken(
            value=float(self._le_value.text()),
        )


class ExpectedOutputFileTokenListWidget(QListWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        pass

    def _init_signals(self):
        pass

    def __insert_item(self, i: int, expected_token: AbstractExpectedToken):
        # 項目のウィジェットを初期化
        item_widget = (
            AbstractExpectedOutputFileTokenListItemWidget
            .create_instance(expected_token, self)
        )
        item_widget.set_data(expected_token)
        # Qtのリスト項目を初期化
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        list_item.setFlags(list_item.flags() & ~Qt.ItemIsSelectable)
        # リストに追加
        self.insertItem(i, list_item)
        # 項目のウィジェットとQtのリスト項目を関連付ける
        self.setItemWidget(list_item, item_widget)
        # シグナルをつなげる
        # noinspection PyUnresolvedReferences
        item_widget.control_triggered_for_item.connect(self.__item_widget_control_triggered)

    def __pop_item(self, i: int) -> AbstractExpectedToken:
        list_item = self.item(i)
        item_widget = self.itemWidget(list_item)
        assert isinstance(item_widget, AbstractExpectedOutputFileTokenListItemWidget), \
            item_widget
        expected_token = item_widget.get_data()
        self.removeItemWidget(list_item)
        # noinspection PyUnresolvedReferences
        item_widget.control_triggered_for_item.disconnect(self.__item_widget_control_triggered)
        self.takeItem(i)
        return expected_token

    def __find_row_by_id(self, item_id: uuid.UUID):
        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, AbstractExpectedOutputFileTokenListItemWidget), \
                item_widget
            if item_widget.has_same_id(item_id):
                return i
        raise IndexError(f"Could not find row with id={item_id!s}")

    def set_data(self, expected_token_list: ExpectedTokenList):
        self.clear()

        for i, expected_token in enumerate(expected_token_list):
            self.__insert_item(i, expected_token)
        # 幅を内容に合わせて調整
        self.setMinimumWidth(self.sizeHintForColumn(0) + 20)

    def get_data(self) -> ExpectedTokenList:
        expected_tokens = ExpectedTokenList()

        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, AbstractExpectedOutputFileTokenListItemWidget), \
                item_widget
            expected_tokens.append(item_widget.get_data())

        return expected_tokens

    def perform_create_text(self):
        # トークンのモデルインスタンスを生成
        token = TextExpectedToken.create_default()
        # 項目を追加
        self.__insert_item(self.count(), token)
        # 下までスクロール
        self.scrollToBottom()

    def perform_create_float(self):
        # トークンのモデルインスタンスを生成
        token = FloatExpectedToken.create_default()
        # 項目を追加
        self.__insert_item(self.count(), token)
        # 下までスクロール
        self.scrollToBottom()

    def perform_delete(self, item_id: uuid.UUID):
        i = self.__find_row_by_id(item_id)
        self.__pop_item(i)

    def perform_move_up(self, item_id: uuid.UUID):
        i = self.__find_row_by_id(item_id)
        if i > 0:
            self.__insert_item(i - 1, self.__pop_item(i))

    def perform_move_down(self, item_id: uuid.UUID):
        i = self.__find_row_by_id(item_id)
        if i < self.count() - 1:
            self.__insert_item(i + 1, self.__pop_item(i))

    @pyqtSlot(str, uuid.UUID)
    def __item_widget_control_triggered(
            self,
            name: str,
            item_id: uuid.UUID,
    ):
        if name == "remove":
            self.perform_delete(item_id)
        elif name == "move-up":
            self.perform_move_up(item_id)
        elif name == "move-down":
            self.perform_move_down(item_id)
        else:
            assert False, name


class ExpectedOutputFileEditWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel(
            "出力にマッチするトークンの集合を編集します。"
            "ここでトークンの追加・削除・編集・並び替えができます。"
            "マッチ方法については自動テストのオプションも参照して下さい。",
            self,
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        self._w_token_list = ExpectedOutputFileTokenListWidget(self)
        layout.addWidget(self._w_token_list)

        self._w_buttons = ButtonBox(self, orientation=Qt.Horizontal)
        self._w_buttons.add_button("文字列を追加", "add-text")
        self._w_buttons.add_button("実数を追加", "add-float")
        layout.addWidget(self._w_buttons)

    def _init_signals(self):
        self._w_buttons.triggered.connect(self._w_buttons_triggered)

    def set_data(self, expected_output_file: ExpectedOutputFile) -> None:
        self._w_token_list.set_data(expected_output_file.expected_tokens)

    def get_data(self, file_id: FileID) -> ExpectedOutputFile:
        expected_output_file = ExpectedOutputFile(
            file_id=file_id,
            expected_tokens=self._w_token_list.get_data(),
        )
        return expected_output_file

    @pyqtSlot(str)
    def _w_buttons_triggered(self, name: str):
        if name == "add-text":
            self._w_token_list.perform_create_text()
        elif name == "add-float":
            self._w_token_list.perform_create_float()
        else:
            assert False, name


class TestCaseExpectedOutputFileMappingEditWidget(QTabWidget):

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
        self._buttons.add_button("標準出力の追加", "add_stdout")
        self._buttons.add_button("ファイルの追加", "add-file")
        self._buttons.add_button("ファイル名の変更", "rename")
        self._buttons.add_button("削除", "delete")
        layout.addWidget(self._buttons)

    def _init_signals(self):
        self._buttons.triggered.connect(self.__buttons_triggered)

    __STDOUT_TAB_TITLE = "[標準出力]"

    @classmethod
    def __file_id_to_tab_title(cls, file_id: FileID) -> str:
        if file_id.is_special:
            assert file_id.special_file_type == SpecialFileType.STDOUT, file_id
            tab_title = cls.__STDOUT_TAB_TITLE
        else:
            tab_title = str(file_id)
        return tab_title

    @classmethod
    def __tab_title_to_file_id(cls, tab_title: str) -> FileID:
        if tab_title == cls.__STDOUT_TAB_TITLE:
            return FileID.STDOUT
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
            expected_output_file: ExpectedOutputFile = None,
    ) -> None:
        if insert_at is None:
            insert_at = self._w_tab.count()
        # noinspection PyTypeChecker
        te = ExpectedOutputFileEditWidget(self)
        if expected_output_file is None:
            expected_output_file = ExpectedOutputFile.create_default(file_id=FileID(tab_title))
        te.set_data(expected_output_file)
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
    def set_data(self, input_files: ExpectedOutputFileMapping) -> None:
        """
        このウィジェットに出力ファイルのデータを設定する

        Args:
            input_files (ExpectedOutputFileMapping): 設定する入力ファイルのデータ
        """
        self._w_tab.clear()
        for file_id, output_file in input_files.items():
            self.__insert_tab(
                tab_title=self.__file_id_to_tab_title(file_id),
                expected_output_file=output_file,
            )

    @pyqtSlot()
    def get_data(self) -> ExpectedOutputFileMapping:
        """
        このウィジェットの入力ファイルのデータを返す

        Returns:
            InputFileMapping: 編集された入力ファイルのデータ
        """
        output_files = ExpectedOutputFileMapping()
        for i_tab in range(self._w_tab.count()):  # 各タブに対して
            # タイトル
            tab_title = self._w_tab.tabText(i_tab)
            file_id = self.__tab_title_to_file_id(tab_title)
            # 内容
            widget_expected_output_file_edit: ExpectedOutputFileEditWidget \
                = self._w_tab.widget(i_tab)
            # データに設定
            output_files[file_id] = widget_expected_output_file_edit.get_data(file_id)
        return output_files

    @pyqtSlot()
    def dispatch_action_add_stdout(self):
        if self.__has_tab_title(self.__STDOUT_TAB_TITLE):
            QMessageBox.critical(
                self,
                "標準出力の追加",
                "標準出力がすでに存在します。"
            )
            return
        self.__insert_tab(tab_title=self.__STDOUT_TAB_TITLE, insert_at=0)

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
        # 標準出力と同じ名前
        if new_tab_title == self.__STDOUT_TAB_TITLE:
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
        # 標準出力をリネームしようとしていたらキャンセル
        if tab_title == self.__STDOUT_TAB_TITLE:
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
        if name == "add_stdout":
            self.dispatch_action_add_stdout()
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
