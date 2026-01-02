from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject

from feature.setting.handler.interface import ICompilerSearchHandler, \
    ICompilerSearchView
from feature.setting.usecase.interface import ICompilerSearchUseCase


class _Worker(QThread):
    """コンパイラ検索用Worker"""
    progress_updated = pyqtSignal(Path, name="progress_updated")
    progress_finished = pyqtSignal(
        list, name="progress_finished")  # list = list[Path]

    def __init__(self, parent: QObject = None, *, compiler_search_usecase: ICompilerSearchUseCase):
        super().__init__(parent)
        self._compiler_search_usecase = compiler_search_usecase
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


class CompilerSearchHandler(ICompilerSearchHandler):
    """コンパイラ検索専任のHandler"""

    def __init__(
            self,
            *,
            view: ICompilerSearchView | None,
            compiler_search_usecase: ICompilerSearchUseCase,
    ):
        self._view: ICompilerSearchView | None = view
        self._compiler_search_usecase = compiler_search_usecase
        self._search_worker: _Worker | None = None
        self._result_path: Path | None = None

    def set_view(self, view: ICompilerSearchView) -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        self._view = view

    @property
    def result_path(self) -> Path | None:
        """検索結果のパスを取得"""
        return self._result_path

    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる（検索開始）"""
        # Workerを生成して開始
        # parentはViewの親ウィジェットを使用（QObjectが必要なため）
        self._search_worker = _Worker(
            parent=self._view.get_parent_widget(),
            compiler_search_usecase=self._compiler_search_usecase,
        )

        # シグナル接続
        # noinspection PyUnresolvedReferences
        self._search_worker.progress_updated.connect(
            self.on_search_progress_updated)
        # noinspection PyUnresolvedReferences
        self._search_worker.progress_finished.connect(self.on_search_finished)

        # 検索開始
        self._search_worker.start()

    def on_search_progress_updated(self, current_path: Path) -> None:
        """検索の進捗が更新されたとき"""
        self._view.set_progress_text(str(current_path))

    def on_search_finished(self, paths: list[Path]) -> None:
        """検索が完了したとき"""
        # 進捗テキストをクリア
        self._view.set_progress_text("")

        if len(paths) == 0:
            # パスが見つからなかった場合
            self._view.show_not_found_message()
            self._result_path = None
        else:
            # パスが見つかった場合、選択ダイアログを表示
            selected_path = self._view.show_path_selection(paths)
            self._result_path = selected_path

        # ダイアログを閉じる
        self._view.accept_dialog()

    def on_close_requested(self) -> None:
        """Viewが閉じられようとしたとき（検索の停止）"""
        if self._search_worker is not None:
            self._search_worker.stop()
            self._search_worker.wait()
