from typing import Callable, TypeVar, Generic

from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt, pyqtSlot
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from controls.widget_progress_icon import ProgressIconWidget
from res.fonts import get_font

_EO = TypeVar("_EO")  # error object


class AbstractProgressDialogWorker(QThread, Generic[_EO]):
    message_update_requested = pyqtSignal(str, name="message_updated")  # message: str

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._error_object: _EO | None = None

    def _callback(self, message: str) -> None:
        # noinspection PyUnresolvedReferences
        self.message_update_requested.emit(message)

    def set_rejected(self, error_object: _EO):
        self._error_object = error_object

    def is_rejected(self):
        return self._error_object is not None

    def get_error_object(self) -> _EO | None:
        return self._error_object

    def run(self):
        raise NotImplementedError()


class AbstractProgressDialog(QDialog, Generic[_EO]):
    # プログレスを表示するダイアログ

    def __init__(
            self,
            parent: QObject = None,
            *,
            title: str = None,
            worker_producer: Callable[[], AbstractProgressDialogWorker[_EO]],
            # ^ parentに渡すインスタンスの親の初期化が終わる前にworkerを作ることができないので遅延評価
    ):
        super().__init__(parent)

        self.__title = title
        self.__worker: AbstractProgressDialogWorker[_EO] = worker_producer()

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setModal(True)
        self.setMinimumWidth(700)
        # self.setStyleSheet(
        #     "QDialog {"
        #     "   background-color: white;"
        #     "   border: 3px solid;"
        #     "   border-color: black;"
        #     "   border-radius: 10px;"
        #     "}"
        # )
        # self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

        self._w_progress_icon = ProgressIconWidget(self)
        layout.addWidget(self._w_progress_icon)

        layout_message = QVBoxLayout()
        layout.addLayout(layout_message)

        self._l_title = QLabel(self)
        self._l_title.setFont(get_font(bold=True))
        self._l_title.setText(self.__title)
        layout_message.addWidget(self._l_title)

        self._l_message = QLabel(self)
        self._l_message.setWordWrap(True)
        layout_message.addWidget(self._l_message)

        layout_message.addStretch(1)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self.__worker.message_update_requested.connect(self.__worker_message_update_requested)
        # noinspection PyUnresolvedReferences
        self.__worker.finished.connect(self.__worker_progress_finished)

    def showEvent(self, evt: QShowEvent):
        if not self.__worker.isRunning() and not self.__worker.isFinished():
            self.__worker.start()

    @pyqtSlot(str)
    def __worker_message_update_requested(self, message: str):
        self._l_message.setText(message)

    @pyqtSlot()
    def __worker_progress_finished(self):
        if self.__worker.is_rejected():
            self.reject()
        else:
            self.accept()

    def get_error_object(self) -> _EO | None:
        return self.__worker.get_error_object()
