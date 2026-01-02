import time
from collections import deque
from contextlib import contextmanager
from typing import List

from PyQt5.QtCore import QThread, QMutex, pyqtSignal

from app.di.state import get_current_project_id_state
from feature.projman.handler.interface import IProjectListView, IProjectListHandler
from feature.projman.usecase.interface import (
    IProjectListRecentSummaryUseCase,
    IProjectUpdateLastOpenedUseCase,
    IProjectFolderShowUseCase,
    IProjectDeleteUseCase,
    IProjectBaseFolderShowUseCase,
    IProjectGetSizeQueryUseCase,
)
from shared.domain.value.identifier import ProjectID
from shared.view.dialog_progress import AbstractProgressDialog, AbstractProgressDialogWorker
from shared.handler.interface import INavigator


class _ProjectSizeGetWorker(QThread):
    """プロジェクトサイズ取得用Worker"""
    size_acquired = pyqtSignal(ProjectID, int, name="size_acquired")

    def __init__(self, parent=None, *, project_get_size_usecase: IProjectGetSizeQueryUseCase):
        super().__init__(parent)
        self.__stop = False
        self._lock = QMutex()
        self._q: deque[ProjectID] = deque()
        self._project_get_size_usecase = project_get_size_usecase

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def stop(self) -> None:
        self.__stop = True

    def clear_queue(self) -> None:
        with self.__lock():
            self._q.clear()

    def set_queue(self, project_ids: List[ProjectID]) -> None:
        with self.__lock():
            self._q.extend(project_ids)

    def run(self):
        while True:
            if self.__stop:
                break
            with self.__lock():
                if not self._q:
                    time.sleep(1)
                    continue
                project_id = self._q.popleft()
            size = self._project_get_size_usecase.execute(project_id=project_id)
            self.size_acquired.emit(project_id, size)
            time.sleep(0.05)


class _ProjectDeleteWorker(AbstractProgressDialogWorker):
    """プロジェクト削除用Worker"""

    def __init__(self, parent=None, *, project_id: ProjectID,
                 project_delete_usecase: IProjectDeleteUseCase):
        super().__init__(parent)
        self._project_delete_usecase = project_delete_usecase
        self._project_id = project_id

    def run(self):
        self._callback("プロジェクトを削除しています・・・")
        self._project_delete_usecase.execute(self._project_id)
        time.sleep(0.5)  # プロジェクトのサイズが小さいとUIが一瞬で消えるので少し待つ


class ProjectDeleteProgressDialog(AbstractProgressDialog):
    """プロジェクト削除プログレスダイアログ"""

    def __init__(self, parent=None, *, project_id: ProjectID,
                 project_delete_usecase: IProjectDeleteUseCase):
        super().__init__(
            parent,
            title="プロジェクトの削除",
            worker_producer=lambda: _ProjectDeleteWorker(
                self,  # type: ignore
                project_id=project_id,
                project_delete_usecase=project_delete_usecase,
            ),
        )


class ProjectListHandler(IProjectListHandler):
    """
    ProjectListView専任のHandler
    責務: プロジェクトリストの初期化とデータロード、ユーザーアクション処理
    Dialog Handlerとは無関係（独立性の原則）
    """

    def __init__(
            self,
            *,
            view: IProjectListView,
            navigator: INavigator,
            project_list_usecase: IProjectListRecentSummaryUseCase,
            project_update_last_opened_usecase: IProjectUpdateLastOpenedUseCase,
            project_folder_show_usecase: IProjectFolderShowUseCase,
            project_delete_usecase: IProjectDeleteUseCase,
            project_base_folder_show_usecase: IProjectBaseFolderShowUseCase,
            project_get_size_usecase: IProjectGetSizeQueryUseCase,
    ):
        self._view = view
        self._navigator = navigator
        self._project_list_usecase = project_list_usecase
        self._project_update_last_opened_usecase = project_update_last_opened_usecase
        self._project_folder_show_usecase = project_folder_show_usecase
        self._project_delete_usecase = project_delete_usecase
        self._project_base_folder_show_usecase = project_base_folder_show_usecase
        self._project_get_size_usecase = project_get_size_usecase

        # Worker初期化
        self._size_worker = _ProjectSizeGetWorker(
            parent=None,
            project_get_size_usecase=project_get_size_usecase,
        )
        # Workerのシグナル接続
        self._size_worker.size_acquired.connect(self.__on_size_acquired)

    def __on_size_acquired(self, project_id: ProjectID, size: int) -> None:
        """サイズ取得完了時のコールバック"""
        self._view.update_project_size(project_id, size)

    # ===== IProjectListHandler実装 =====
    def on_view_initialized(self) -> None:
        """View初期化時に呼ばれる（showEventから）"""
        self._load_project_list()
        self._start_size_loading()

    def on_open_project_requested(self, project_id: ProjectID) -> None:
        """プロジェクトを開く"""
        # 1. Stateを更新（アプリケーション層の責務）
        state = get_current_project_id_state()
        assert state.get() is None, state.get()
        state.update(project_id)

        # 2. ドメイン状態を更新（UseCaseの責務）
        self._project_update_last_opened_usecase.execute(project_id)

        # 3. 画面遷移（Navigatorに依頼）
        self._navigator.navigate_to_main_window(project_id)

    def on_open_folder_requested(self, project_id: ProjectID) -> None:
        """プロジェクトフォルダを開く"""
        self._project_folder_show_usecase.execute(project_id)

    def on_delete_project_requested(self, project_id: ProjectID) -> None:
        """プロジェクト削除"""
        # Viewで確認ダイアログを表示
        if not self._view.show_delete_confirmation(project_id):
            return

        # 削除実行
        dialog = ProjectDeleteProgressDialog(
            project_id=project_id,
            project_delete_usecase=self._project_delete_usecase,
        )
        dialog.exec_()

        # リストを再読み込み
        self._load_project_list()

    def on_open_base_folder_requested(self) -> None:
        """プロジェクト管理フォルダを開く"""
        self._project_base_folder_show_usecase.execute()

    def on_refresh_requested(self) -> None:
        """プロジェクトリストの再読み込み"""
        self._load_project_list()
        self._start_size_loading()

    # ===== 内部メソッド =====
    def _load_project_list(self) -> None:
        """プロジェクトリストを読み込んでViewに通知"""
        try:
            projects = self._project_list_usecase.execute()
            self._view.update_project_list(projects)
        except Exception as e:
            self._view.show_error_message(f"プロジェクトリストの読み込みに失敗しました: {e}")

    def _start_size_loading(self) -> None:
        """サイズ取得Workerを開始"""
        self._view.start_size_loading()
        # 現在のプロジェクトリストから有効なproject_idを取得してキューに追加
        # Viewから取得する必要があるが、インターフェースに追加するか、別の方法を検討
        # 暫定的に、WorkerキューはView側で設定する前提

    def stop_size_loading(self) -> None:
        """サイズ取得Workerを停止"""
        self._size_worker.stop()
        self._size_worker.wait()
        self._view.stop_size_loading()

    def set_size_queue(self, project_ids: List[ProjectID]) -> None:
        """サイズ取得キューを設定（Viewから呼ばれる）"""
        self._size_worker.clear_queue()
        self._size_worker.set_queue(project_ids)
        if not self._size_worker.isRunning():
            self._size_worker.start()

    def stop_size_loading(self) -> None:
        """サイズ取得Workerを停止（ViewのhideEventから呼ばれる）"""
        self._size_worker.stop()
        if self._size_worker.isRunning():
            self._size_worker.wait()
        self._view.stop_size_loading()
