from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QThread
from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget, QLabel, QMessageBox, QInputDialog

from app_logging import create_logger
from service_provider import get_compiler_location_search_service


class _CompilerSearchWorker(QThread):
    _logger = create_logger()

    location_found = pyqtSignal(list, name="location_found")
    search_location_changed = pyqtSignal(Path, name="search_location_changed")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._search_service = get_compiler_location_search_service()
        self._search_service.reset_search()

        self._stop = False

    def run(self):
        self._logger.debug("Thread start")
        self._search_service.reset_search()
        while not self._stop:
            # noinspection PyUnresolvedReferences
            self.search_location_changed.emit(self._search_service.get_current_search_location())
            if not self._search_service.search_next():
                break
        # noinspection PyUnresolvedReferences
        self.location_found.emit(self._search_service.get_paths_found())
        self._logger.debug("Thread end")

    @pyqtSlot()
    def stop(self):
        self._stop = True
        self._logger.debug("Stop signal sent")


class _CompilerSearchWidget(QWidget):
    finished = pyqtSignal(name="finished")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._find_worker = _CompilerSearchWorker()
        self._path_found: Path | None = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("検索中・・・ "))

        self._l_progress = QLabel(self)
        layout.addWidget(self._l_progress)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._find_worker.location_found.connect(self._find_worker_location_found)
        # noinspection PyUnresolvedReferences
        self._find_worker.search_location_changed.connect(self._find_worker_search_location_changed)

    def get_value(self) -> Path | None:
        return self._path_found

    @pyqtSlot()
    def terminate_process(self):
        self._find_worker.stop()
        self._find_worker.wait()

    @pyqtSlot(list)
    def _find_worker_location_found(self, paths: list[Path]):
        self._l_progress.setText("")
        if len(paths) == 0:
            QMessageBox.warning(
                self,
                "開発者ツールの自動検索",
                "VsDevCmd.batが見つかりませんでした。手動で指定してください。",
            )
        else:
            path_str_chosen, ok = QInputDialog.getItem(
                self,
                "開発者ツールの自動検索",
                "以下のパスが見つかりました。使用するパスを選択してください。",
                list(map(str, paths)),
                editable=False,
            )
            if ok:
                self._path_found = Path(path_str_chosen)
        # noinspection PyUnresolvedReferences
        self.finished.emit()

    @pyqtSlot(Path)
    def _find_worker_search_location_changed(self, path: Path):
        self._l_progress.setText(str(path))

    def showEvent(self, evt: QShowEvent):
        self._find_worker.start()


class CompilerSearchDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._path_found: Path | None = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setWindowTitle("開発者ツールの自動検索")
        self.setModal(True)
        self.setFixedSize(900, 100)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_auto_find = _CompilerSearchWidget(self)  # type: ignore
        layout.addWidget(self._w_auto_find)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._w_auto_find.finished.connect(self._auto_find_finished)

    @pyqtSlot()
    def _auto_find_finished(self):
        self._path_found = self._w_auto_find.get_value()
        self.accept()
        self.close()

    def get_value(self) -> Path | None:
        return self._path_found

    def closeEvent(self, evt: QCloseEvent):
        self._w_auto_find.terminate_process()
        evt.accept()
