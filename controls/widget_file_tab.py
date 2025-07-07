from abc import ABC, abstractmethod

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, Qt, QPoint
from PyQt5.QtGui import QIcon, QPaintEvent, QPainter, QMouseEvent
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, QMenu, QTabWidget

from domain.models.values import FileID
from res.icons import get_icon


class AbstractFileTabWidgetDelegator(ABC):
    @abstractmethod
    def add_button_context_menu_titles(self, tab_widget: "FileTabWidget") \
            -> dict[str, tuple[str, QIcon | None]]:  # action-name -> (title, icon)
        raise NotImplementedError()

    @abstractmethod
    def perform_add(self, action_name: str, tab_widget: "FileTabWidget") -> None:
        raise NotImplementedError()

    @abstractmethod
    def perform_rename(self, index: int, tab_widget: "FileTabWidget") -> None:
        raise NotImplementedError()

    @abstractmethod
    def perform_delete(self, index: int, tab_widget: "FileTabWidget") -> None:
        raise NotImplementedError()

    @abstractmethod
    def file_id_to_tab_title(self, file_id: FileID) -> str:
        raise NotImplementedError()

    @abstractmethod
    def file_id_to_tab_icon(self, file_id: FileID) -> QIcon | None:
        raise NotImplementedError()


class FileTabCornerWidget(QWidget):
    add_action_triggered = pyqtSignal(str, name="add_action_triggered")  # str: action-name

    def __init__(self, parent: QObject = None, *, delegator: AbstractFileTabWidgetDelegator):
        super().__init__(parent)

        self._delegator = delegator

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        self.add_button = QToolButton(self)
        self.add_button.setIcon(get_icon("plus"))
        self.add_button.setFixedWidth(30)
        self.add_button.setFixedHeight(30)
        layout.addWidget(self.add_button)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self.add_button.clicked.connect(self.__add_button_clicked)

    @pyqtSlot()
    def __add_button_clicked(self):
        menu = QMenu(self)

        tab_widget = self.parent()
        assert isinstance(tab_widget, FileTabWidget)

        for action_name, (title, icon) \
                in self._delegator.add_button_context_menu_titles(tab_widget).items():
            action = menu.addAction(title)
            if icon is not None:
                action.setIcon(icon)
            action.setObjectName(action_name)
            # noinspection PyUnresolvedReferences
            action.triggered.connect(self.__add_action_triggered)

        # メニューを表示
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        # コンテキストメニューをボタンの下に表示
        menu.popup(
            self.mapToGlobal(
                self.add_button.pos()
                + QPoint(self.add_button.width(), self.add_button.height()) / 2
            )
        )

    @pyqtSlot()
    def __add_action_triggered(self):
        action_name = self.sender().objectName()
        # noinspection PyUnresolvedReferences
        self.add_action_triggered.emit(action_name)


class FileTabWidget(QTabWidget):
    def __init__(self, parent: QObject = None, *, delegator: AbstractFileTabWidgetDelegator):
        super().__init__(parent)

        self.__delegator = delegator

        self._init_ui()
        self._init_signals()

        self._file_ids: list[FileID] = []

    def _init_ui(self):
        self.setTabsClosable(True)

        self.corner_widget = FileTabCornerWidget(self, delegator=self.__delegator)
        # タブが無くてもcorner-widgetが消えないようにする
        # https://stackoverflow.com/questions/31116295/cornerwidget-disappears-when-there-isnt-any-tab
        self.corner_widget.setMinimumSize(self.corner_widget.sizeHint())
        self.setCornerWidget(self.corner_widget, Qt.TopRightCorner)

        self.tabBar().setCursor(Qt.PointingHandCursor)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self.corner_widget.add_action_triggered.connect(self.__add_action_triggered)
        # noinspection PyUnresolvedReferences
        self.tabBarDoubleClicked.connect(self.__tab_bar_double_clicked)
        # noinspection PyUnresolvedReferences
        self.tabCloseRequested.connect(self.__tab_close_requested)

    @pyqtSlot(str)
    def __add_action_triggered(self, action_name: str):
        self.__delegator.perform_add(action_name, self)

    @pyqtSlot(int)
    def __tab_bar_double_clicked(self, index: int):
        self.__delegator.perform_rename(index, self)

    @pyqtSlot(int)
    def __tab_close_requested(self, index: int):
        self.__delegator.perform_delete(index, self)

    def paintEvent(self, evt: QPaintEvent):
        super().paintEvent(evt)
        # タブがないときにメッセージを表示する
        if self.count() == 0:
            painter = QPainter(self)
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "表示する項目がありません\n右上のアイコンをクリックして項目を追加します",
            )

    def mousePressEvent(self, evt: QMouseEvent):
        super().mousePressEvent(evt)
        # タブがないときにクリックすると項目追加アイコンを駆動してユーザーを誘導する
        if self.count() == 0:
            self.corner_widget.add_button.click()

    def item_insert(self, index: int, file_id: FileID, widget: QWidget) -> None:
        if file_id in self._file_ids:
            raise ValueError()
        title = self.__delegator.file_id_to_tab_title(file_id)
        self.insertTab(index, widget, title)
        icon = self.__delegator.file_id_to_tab_icon(file_id)
        if icon is not None:
            self.setTabIcon(index, icon)
        self._file_ids.insert(index, file_id)

    def item_count(self) -> int:
        return len(self._file_ids)

    def item_append(self, file_id: FileID, widget: QWidget) -> None:
        self.item_insert(self.item_count(), file_id, widget)

    def item_index(self, file_id: FileID) -> int | None:
        try:
            return self._file_ids.index(file_id)
        except ValueError:
            return None

    def item_has_file_id(self, file_id: FileID) -> bool:
        return self.item_index(file_id) is not None

    def item_widget(self, index: int) -> QWidget:
        if index is None:
            raise ValueError()
        return self.widget(index)

    def item_set_file_id(self, index: int, file_id: FileID) -> None:
        if file_id in self._file_ids:
            raise ValueError()
        title = self.__delegator.file_id_to_tab_title(file_id)
        self.setTabText(index, title)
        icon = self.__delegator.file_id_to_tab_icon(file_id)
        if icon is not None:
            self.setTabIcon(index, icon)
        self._file_ids[index] = file_id

    def item_get_file_id(self, index: int) -> FileID:
        assert 0 <= index < len(self._file_ids), (
            f"invalid index: {index}, total number of file tabs: {len(self._file_ids)}"
        )
        return self._file_ids[index]

    def item_delete(self, index: int) -> None:
        self.removeTab(index)
        self._file_ids.pop(index)

    def item_clear(self) -> None:
        self.clear()
        self._file_ids.clear()

    def get_current_file_id(self) -> FileID | None:
        index: int = self.currentIndex()
        if index < 0:
            return None
        return self.item_get_file_id(index)
