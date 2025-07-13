import uuid
from typing import TypeVar, Generic

from PyQt5.QtCore import pyqtSignal, QObject, Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, \
    QVBoxLayout, QBoxLayout, QPushButton

from controls.widget_button_box import ButtonBox
from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.pattern import AbstractPattern, TextPattern, PatternList, SpacePattern, \
    EOLPattern
from domain.models.values import FileID
from res.fonts import get_font
from res.icons import get_icon


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


class TextRotatablePushButton(QPushButton):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._texts = [""]
        self._state = 0

        self._init_ui()
        self._init_signals()

    def _init_ui(self) -> None:
        pass

    def _init_signals(self) -> None:
        # noinspection PyUnresolvedReferences
        self.clicked.connect(self.__clicked)

    def _update_text(self) -> None:
        self.setText(self._texts[self._state])

    @pyqtSlot()
    def __clicked(self) -> None:
        self._state = (self._state + 1) % len(self._texts)
        self._update_text()

    def set_texts(self, *texts: str) -> None:
        self._texts = texts
        self._state = 0
        self._update_text()

    def get_state(self) -> int:
        return self._state

    def set_state(self, state: int):
        self._state = state
        self._update_text()


_ET = TypeVar("_ET", bound=AbstractPattern)


class AbstractExpectedOutputFileTokenListItemWidget(QWidget, Generic[_ET]):
    control_triggered_for_item = pyqtSignal(str, uuid.UUID)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._id = uuid.uuid4()

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._init_ui_inner(layout)

        self._buttons = ExpectedOutputFileTokenListItemControlButtons(self, parent_id=self._id)
        layout.addWidget(self._buttons)

    def _init_ui_inner(self, layout: QBoxLayout):
        raise NotImplementedError()

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._buttons.triggered_for_item.connect(self.control_triggered_for_item)

    @classmethod
    def _is_acceptable(cls, pattern: AbstractPattern) -> bool:
        raise NotImplementedError()

    def set_data(self, pattern: _ET) -> None:
        raise NotImplementedError()

    def get_data(self, index: int) -> _ET:
        raise NotImplementedError()

    @classmethod
    def create_instance(cls, pattern: AbstractPattern, parent: QObject = None) \
            -> "AbstractExpectedOutputFileTokenListItemWidget":
        for sub_cls in cls.__subclasses__():
            if sub_cls._is_acceptable(pattern):
                obj = sub_cls(parent)
                obj.set_data(pattern)
                return obj
        assert False, pattern

    def has_same_id(self, other_id: uuid.UUID):
        return self._id == other_id


class ExpectedOutputFileTextTokenListItemWidget(
    AbstractExpectedOutputFileTokenListItemWidget[TextPattern],
):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def _init_ui_inner(self, layout: QBoxLayout):
        self._b_is_expected = TextRotatablePushButton(self)
        self._b_is_expected.set_texts("次の文字列が出現しない", "次の文字列が出現する")
        self._b_is_expected.setFont(get_font(small=True))
        layout.addWidget(self._b_is_expected)

        self._le_value = QLineEdit(self)
        self._le_value.setPlaceholderText("文字列を入力")
        layout.addWidget(self._le_value)

        self._b_is_multiple_space_ignored = QPushButton(self)
        self._b_is_multiple_space_ignored.setCheckable(True)
        self._b_is_multiple_space_ignored.setText("␣+")
        self._b_is_multiple_space_ignored.setFixedWidth(40)
        self._b_is_multiple_space_ignored.setFont(get_font(small=True))
        self._b_is_multiple_space_ignored.setToolTip(
            "連続した複数のスペースを１つのスペースとしてマッチングします"
        )
        layout.addWidget(self._b_is_multiple_space_ignored)

        self._b_is_word = QPushButton(self)
        self._b_is_word.setCheckable(True)
        self._b_is_word.setText("W")
        self._b_is_word.setFixedWidth(40)
        self._b_is_word.setFont(get_font(small=True))
        self._b_is_word.setToolTip(
            "単語単位でマッチングします"
        )
        layout.addWidget(self._b_is_word)

    @classmethod
    def _is_acceptable(cls, pattern: AbstractPattern) -> bool:
        return isinstance(pattern, TextPattern)

    def set_data(self, pattern: TextPattern) -> None:
        self._le_value.setText(pattern.text)
        self._b_is_expected.set_state(int(pattern.is_expected))
        self._b_is_multiple_space_ignored.setChecked(pattern.is_multiple_space_ignored)
        self._b_is_word.setChecked(pattern.is_word)

    def get_data(self, index: int) -> TextPattern:
        return TextPattern(
            index=index,
            is_expected=bool(self._b_is_expected.get_state()),
            text=self._le_value.text(),
            is_multiple_space_ignored=self._b_is_multiple_space_ignored.isChecked(),
            is_word=self._b_is_word.isChecked(),
        )


class ExpectedOutputFileSpaceTokenListItemWidget(
    AbstractExpectedOutputFileTokenListItemWidget[SpacePattern],
):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def _init_ui_inner(self, layout: QBoxLayout):
        self._b_is_expected = TextRotatablePushButton(self)
        self._b_is_expected.set_texts("空白が出現しない", "空白が出現する")
        self._b_is_expected.setFont(get_font(small=True))
        layout.addWidget(self._b_is_expected)

    @classmethod
    def _is_acceptable(cls, pattern: AbstractPattern) -> bool:
        return isinstance(pattern, SpacePattern)

    def set_data(self, pattern: SpacePattern) -> None:
        self._b_is_expected.set_state(int(pattern.is_expected))

    def get_data(self, index: int) -> SpacePattern:
        return SpacePattern(
            index=index,
            is_expected=bool(self._b_is_expected.get_state()),
        )


class ExpectedOutputFileEOLTokenListItemWidget(
    AbstractExpectedOutputFileTokenListItemWidget[EOLPattern],
):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def _init_ui_inner(self, layout: QBoxLayout):
        self._b_is_expected = TextRotatablePushButton(self)
        self._b_is_expected.set_texts("改行が出現しない", "改行が出現する")
        self._b_is_expected.setFont(get_font(small=True))
        layout.addWidget(self._b_is_expected)

    @classmethod
    def _is_acceptable(cls, pattern: AbstractPattern) -> bool:
        return isinstance(pattern, EOLPattern)

    def set_data(self, pattern: EOLPattern) -> None:
        self._b_is_expected.set_state(int(pattern.is_expected))

    def get_data(self, index: int) -> EOLPattern:
        return EOLPattern(
            index=index,
            is_expected=bool(self._b_is_expected.get_state()),
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

    def __insert_item(self, i: int, pattern: AbstractPattern):
        # 項目のウィジェットを初期化
        item_widget = (
            AbstractExpectedOutputFileTokenListItemWidget
            .create_instance(pattern, self)
        )
        item_widget.set_data(pattern)
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

    def __pop_item(self, i: int) -> AbstractPattern:
        list_item = self.item(i)
        item_widget = self.itemWidget(list_item)
        assert isinstance(item_widget, AbstractExpectedOutputFileTokenListItemWidget), \
            item_widget
        pattern = item_widget.get_data(index=i)
        self.removeItemWidget(list_item)
        # noinspection PyUnresolvedReferences
        item_widget.control_triggered_for_item.disconnect(self.__item_widget_control_triggered)
        self.takeItem(i)
        return pattern

    def __find_row_by_id(self, item_id: uuid.UUID):
        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, AbstractExpectedOutputFileTokenListItemWidget), \
                item_widget
            if item_widget.has_same_id(item_id):
                return i
        raise IndexError(f"Could not find row with id={item_id!s}")

    def set_data(self, pattern_list: PatternList):
        self.clear()

        for i, pattern in enumerate(pattern_list):
            self.__insert_item(i, pattern)
        # 幅を内容に合わせて調整
        self.setMinimumWidth(self.sizeHintForColumn(0) + 20)

    def get_data(self) -> PatternList:
        patterns: list[AbstractPattern] = []

        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, AbstractExpectedOutputFileTokenListItemWidget), \
                item_widget
            patterns.append(item_widget.get_data(index=i))

        return PatternList(patterns)

    def perform_create_text(self):
        # トークンのモデルインスタンスを生成
        token = TextPattern.create_default(index=self.count())
        # 項目を追加
        self.__insert_item(self.count(), token)
        # 下までスクロール
        self.scrollToBottom()

    def perform_create_space(self):
        # トークンのモデルインスタンスを生成
        token = SpacePattern.create_default(index=self.count())
        # 項目を追加
        self.__insert_item(self.count(), token)
        # 下までスクロール
        self.scrollToBottom()

    def perform_create_eol(self):
        # トークンのモデルインスタンスを生成
        token = EOLPattern.create_default(index=self.count())
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
        self._w_buttons.add_button("空白を追加", "add-space")
        self._w_buttons.add_button("改行を追加", "add-eol")
        layout.addWidget(self._w_buttons)

    def _init_signals(self):
        self._w_buttons.triggered.connect(self._w_buttons_triggered)

    def set_data(self, expected_output_file: ExpectedOutputFile) -> None:
        self._w_token_list.set_data(expected_output_file.patterns)

    def get_data(self, file_id: FileID) -> ExpectedOutputFile:
        expected_output_file = ExpectedOutputFile(
            file_id=file_id,
            patterns=self._w_token_list.get_data(),
        )
        return expected_output_file

    @pyqtSlot(str)
    def _w_buttons_triggered(self, name: str):
        if name == "add-text":
            self._w_token_list.perform_create_text()
        elif name == "add-space":
            self._w_token_list.perform_create_space()
        elif name == "add-eol":
            self._w_token_list.perform_create_eol()
        else:
            assert False, name
