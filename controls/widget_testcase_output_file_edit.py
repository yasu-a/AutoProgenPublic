import uuid
from typing import TypeVar, Generic

from PyQt5.QtCore import pyqtSignal, QObject, Qt, pyqtSlot
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, \
    QVBoxLayout

from controls.res.icons import get_icon
from controls.widget_button_box import ButtonBox
from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.expected_token import AbstractExpectedToken, TextExpectedToken, \
    FloatExpectedToken, ExpectedTokenList
from domain.models.values import FileID

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
        self.add_button("", "move-up", icon=get_icon("up"), tab_focus=False)
        self.add_button("", "move-down", icon=get_icon("down"), tab_focus=False)
        self.add_button("", "remove", icon=get_icon("trash"), tab_focus=False)
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
