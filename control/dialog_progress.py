from typing import Callable, TypeVar, Generic

from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt, pyqtSlot
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from control.widget_progress_icon import ProgressIconWidget
from res.font import get_font

_EO = TypeVar("_EO")  # error object


class AbstractProgressDialogWorker(QThread, Generic[_EO]):
    message_update_requested = pyqtSignal(str, name="message_updated")  # message: str

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._result_object: _EO | None = None
        self._error: Exception | None = None

    def _callback(self, message: str) -> None:
        # noinspection PyUnresolvedReferences
        self.message_update_requested.emit(message)

    def set_result_object(self, result_object: _EO):
        self._result_object = result_object

    def get_result_object(self) -> _EO | None:
        return self._result_object

    def set_error(self, error: Exception) -> None:
        self._error = error

    def get_error(self) -> Exception | None:
        return self._error

    def run(self):
        raise NotImplementedError()


class CallbackTaskProgressWorker(AbstractProgressDialogWorker[_EO]):
    """
    コールバックで進捗通知を行うブロッキング処理向けの汎用 Progress Worker。

    `task_func` は進捗通知用 callback を 1 つ受け取り、結果オブジェクトを返す。
    callback 経由のメッセージはダイアログのラベルに反映される。
    結果は get_result_object() から参照できる。
    """
    def __init__(
            self,
            parent: QObject = None,
            *,
            task_func: Callable[..., _EO],
            task_kwargs: dict | None = None,
    ):
        super().__init__(parent)
        self._task_func = task_func
        self._task_kwargs = task_kwargs or {}

    def run(self):
        try:
            kwargs = dict(self._task_kwargs)
            result = self._task_func(progress_callback=self._callback, **kwargs)
            self.set_result_object(result)
        except Exception as e:
            self.set_error(e)


class AbstractProgressDialog(QDialog, Generic[_EO]):
    # プログレスを表示するダイアログ

    def __init__(
            self,
            parent: QObject = None,
            *,
            title: str = None,
            initial_message: str = "",
            worker_producer: Callable[[], AbstractProgressDialogWorker[_EO]],
            # ^ parentに渡すインスタンスの親の初期化が終わる前にworkerを作ることができないので遅延評価
    ):
        super().__init__(parent)

        self.__title = title
        self.__initial_message = initial_message
        self.__worker: AbstractProgressDialogWorker[_EO] = worker_producer()

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setModal(True)
        self.setMinimumWidth(700)
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
        self._l_message.setText(self.__initial_message)
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
        self.accept()

    def get_result_object(self) -> _EO | None:
        return self.__worker.get_result_object()

    def get_error(self) -> Exception | None:
        return self.__worker.get_error()

    @classmethod
    def run_blocking_task(
            cls,
            parent: QObject,
            *,
            title: str,
            initial_message: str,
            task_func: Callable[..., _EO],
            **task_kwargs,
    ) -> _EO:
        """
        進捗ダイアログを表示しながらブロッキングタスクを実行し、結果を返す。

        `task_func` には `progress_callback` がキーワード引数として渡される。
        タスク内で例外が発生した場合は Worker が保持し、終了後にここで再送出する。
        """
        dialog = cls(
            parent,
            title=title,
            initial_message=initial_message,
            worker_producer=lambda: CallbackTaskProgressWorker(
                None,
                task_func=task_func,
                task_kwargs=task_kwargs,
            ),
        )
        _ = dialog.exec_()
        error = dialog.get_error()
        if error is not None:
            raise error
        result = dialog.get_result_object()
        return result
