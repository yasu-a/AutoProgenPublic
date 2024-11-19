from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QThread
from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget, QLabel, QMessageBox, QInputDialog

from application.dependency.usecases import get_compiler_search_usecase
from res.fonts import get_font


class _CompilerSearchWorker(QThread):
    progress_updated = pyqtSignal(Path, name="progress_updated")
    progress_finished = pyqtSignal(list, name="progress_finished")  # list = list[Path]

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._compiler_search_usecase = get_compiler_search_usecase()

        self._stop = False

    def __usecase_progress_callback(self, current_path: Path) -> None:
        # noinspection PyUnresolvedReferences
        self.progress_updated.emit(current_path)

    def __usecase_stop_producer(self) -> bool:
        return self._stop

    def run(self):
        results: list[Path] = self._compiler_search_usecase.execute(
            progress_callback=self.__usecase_progress_callback,
            stop_producer=self.__usecase_stop_producer,
        )
        # noinspection PyUnresolvedReferences
        self.progress_finished.emit(results)

    @pyqtSlot()
    def stop(self):
        self._stop = True


class _CompilerSearchWidget(QWidget):
    finished = pyqtSignal(name="finished")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._search_worker = _CompilerSearchWorker()
        self._path_found: Path | None = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("検索中・・・ "))

        self._l_progress = QLabel(self)
        self._l_progress.setFont(get_font(monospace=True, small=True))
        layout.addWidget(self._l_progress)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._search_worker.progress_updated.connect(self.__search_worker_search_location_changed)
        # noinspection PyUnresolvedReferences
        self._search_worker.progress_finished.connect(self._find_worker_location_found)

    def get_value(self) -> Path | None:
        return self._path_found

    def start_worker(self):
        self._search_worker.start()

    @pyqtSlot()
    def terminate_process(self):
        self._search_worker.stop()
        self._search_worker.wait()

    @pyqtSlot(list)  # list = list[Path]
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
    def __search_worker_search_location_changed(self, path: Path):
        self._l_progress.setText(str(path))


class CompilerSearchDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._path_found: Path | None = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setWindowTitle("開発者ツールの自動検索")
        self.setModal(True)
        self.setFixedSize(1300, 100)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_compiler_search = _CompilerSearchWidget(self)  # type: ignore
        layout.addWidget(self._w_compiler_search)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._w_compiler_search.finished.connect(self.__w_compiler_search_finished)

    @pyqtSlot()
    def __w_compiler_search_finished(self):
        self._path_found = self._w_compiler_search.get_value()
        self.accept()
        self.close()

    def get_value(self) -> Path | None:
        return self._path_found

    def showEvent(self, evt: QShowEvent):
        self._w_compiler_search.start_worker()

    def closeEvent(self, evt: QCloseEvent):
        self._w_compiler_search.terminate_process()
        evt.accept()
