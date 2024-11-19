from typing import Callable

from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt, pyqtSlot
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from controls.widget_progress_icon import ProgressIconWidget
from res.fonts import get_font


class AbstractProgressDialogWorker(QThread):
    message_updated = pyqtSignal(str, name="message_updated")  # message: str

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    def _callback(self, message: str) -> None:
        # noinspection PyUnresolvedReferences
        self.message_updated.emit(message)

    def run(self):
        raise NotImplementedError()


class AbstractProgressDialog(QDialog):
    # プログレスを表示するダイアログ

    def __init__(
            self,
            parent: QObject = None,
            *,
            title: str = None,
            worker_producer: Callable[[], AbstractProgressDialogWorker],
            # ^ parentに渡すインスタンスの親の初期化が終わる前にworkerを作ることができないので遅延評価
    ):
        super().__init__(parent)

        self.__title = title
        self.__worker: AbstractProgressDialogWorker = worker_producer()

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
        self.__worker.message_updated.connect(self.__worker_progress_updated)
        # noinspection PyUnresolvedReferences
        self.__worker.finished.connect(self.__worker_progress_finished)

    def showEvent(self, evt: QShowEvent):
        if not self.__worker.isRunning() and not self.__worker.isFinished():
            self.__worker.start()

    @pyqtSlot(str)
    def __worker_progress_updated(self, progress_title: str):
        self._l_message.setText(progress_title)

    @pyqtSlot()
    def __worker_progress_finished(self):
        self.accept()
