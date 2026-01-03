from pathlib import Path
from typing import TypeVar, Callable

from PyQt5.QtCore import QEventLoop, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QMainWindow

import app.di.handler as di_handler
import app.di.state as di_state
import app.di.system as di_system
from app.di.usecase import get_project_list_recent_summary_usecase
from feature.projman.handler.project_launcher import ProjectLauncherHandler
from feature.projman.view.project_create_view import ProjectCreateView
from feature.projman.view.project_launcher import ProjectLauncherDialog
from feature.projman.view.project_list_view import ProjectListView
from shared.domain.value.identifier import ProjectID, TargetID
from shared.handler.interface import INavigator
from shared.view.dialog_wait import WaitDialog
# Import specific features only here to act as Composition Root
from shared.view.style.icon import get_icon

T = TypeVar('T')


class Navigator(INavigator):
    """
    画面遷移の実装クラス（Composition Root）
    ここで初めて feature 層のView/Handlerや、domain/infra 層の依存関係（DI）を結合する
    ウィンドウのライフサイクルも管理する
    
    状態遷移型（State Machine）として実装：
    - Launcher (プロジェクト選択) <-> Workspace (メイン画面)
    """

    def __init__(self):
        self._current_window: QMainWindow | None = None
        # 遷移中フラグ: ウィンドウをプログラムで閉じている最中に、
        # アプリ終了判定が誤爆しないようにするガード
        self._is_transitioning = False

    def start(self) -> None:
        """Entry Point"""
        self._switch_window(self._create_launcher_window)

    def navigate_to_main_window(self, project_id: ProjectID) -> None:
        """
        メインウィンドウへの遷移トリガー
        INavigatorインターフェースの実装
        
        役割: Workspaceへ遷移する
        注意: Stateの更新は呼び出し元（Handler）で既に行われている
        """
        # Workspaceへ遷移
        self._switch_window(self._create_workspace_window)

    # --- Internal Helpers ---

    def _switch_window(self, factory_func):
        """ウィンドウ切り替えの共通ロジック"""
        self._is_transitioning = True

        # 1. 古いウィンドウを閉じる
        if self._current_window:
            self._current_window.close()
            self._current_window.deleteLater()

        # 2. 新しいウィンドウを作る
        self._current_window = factory_func()
        self._current_window.show()

        self._is_transitioning = False

    def _create_launcher_window(self) -> QMainWindow:
        """ランチャーウィンドウを作成"""
        # 古い window_launcher.py ではなく新しい dialog を使用
        window = ProjectLauncherDialog()  # TODO: use container

        # --- (DIとHandlerの設定) ---
        launcher_handler = ProjectLauncherHandler(  # TODO: use container
            view=window,
            navigator=self,  # selfを渡す
            project_list_usecase=get_project_list_recent_summary_usecase(),
        )
        window.set_handler(launcher_handler)

        # Create Tab (中身のView/Handlerは既存のものを再利用)
        create_view = ProjectCreateView()
        create_handler = di_handler.get_project_create_handler(
            view=create_view,
            navigator=self,
        )
        create_view.set_handler(create_handler)

        # 新しいインターフェースメソッド add_tab を使用
        window.add_tab(
            create_view,
            "新しいプロジェクト",
            get_icon("plus", rotate=90),
        )

        # List Tab
        list_view = ProjectListView()
        list_handler = di_handler.get_project_list_handler(
            view=list_view,
            navigator=self,
        )
        list_view.set_handler(list_handler)

        # 設定ボタンのシグナル接続
        # list_view内の設定ボタンが押されたら、launcher_handlerの設定処理を呼ぶ
        list_view.settings_requested.connect(launcher_handler.on_setting_requested)

        window.add_tab(
            list_view,
            "最近のプロジェクト",
            get_icon("article", rotate=90),
        )
        # ---------------------------------------

        window.closed.connect(self._on_launcher_closed)
        return window

    def _create_workspace_window(self) -> QMainWindow:
        """ワークスペースウィンドウを作成"""
        # Import here to avoid circular dependency
        from feature.workspace.view.workspace_window import WorkspaceWindow
        from app.di import app as di_app

        window = WorkspaceWindow()

        # Handlerを生成して注入
        handler = di_handler.get_workspace_window_handler(
            view=window,
            navigator=di_app.get_navigator(),
        )
        window.set_handler(handler)

        # ワークスペースの「×」ボタンはランチャーへの戻りを意味する
        window.closed.connect(self._on_workspace_closed)
        return window

    # --- Signal Slots ---

    def _on_launcher_closed(self):
        """ランチャーが閉じられたとき"""
        # 遷移中(Workspaceへの遷移実行中)にclose()が呼ばれた場合は無視する
        if not self._is_transitioning:
            import sys
            sys.exit(0)

    def _on_workspace_closed(self):
        """ワークスペースが閉じられたとき"""
        # 遷移中でなければ、タスク停止などを経てランチャーに戻る
        if not self._is_transitioning:
            # 1. タスク停止
            self._wait_for_task_termination()

            # 2. ステートの初期化
            di_state.get_current_project_id_state().clear()

            # 3. ランチャーへ戻る
            self._switch_window(self._create_launcher_window)

    def _wait_for_task_termination(self) -> None:
        """
        実行中のタスクの終了を待機する
        """
        task_manager = di_system.get_task_manager()
        if task_manager.count_active() == 0:
            return

        # 1. ダイアログを表示（以前のStopTasksDialogと同じ見た目）
        dialog = WaitDialog(
            self._current_window,
            title="タスクの停止",
            message="実行中のタスクを終了しています...",
        )
        dialog.show()

        # 2. 別スレッドでterminate()を実行
        class TerminateWorker(QThread):
            finished_signal = pyqtSignal()
            message_signal = pyqtSignal(str)

            def __init__(self, task_manager):
                super().__init__()
                self._task_manager = task_manager

            def run(self):
                def callback(msg: str):
                    # noinspection PyUnresolvedReferences
                    self.message_signal.emit(msg)

                self._task_manager.terminate(callback)
                # noinspection PyUnresolvedReferences
                self.finished_signal.emit()

        worker = TerminateWorker(task_manager)
        # noinspection PyUnresolvedReferences
        worker.message_signal.connect(dialog.set_message)

        # 3. EventLoopで待機
        loop = QEventLoop()
        # noinspection PyUnresolvedReferences
        worker.finished_signal.connect(loop.quit)
        worker.start()

        # タスクが終了するまで待機
        loop.exec_()

        # 4. クリーンアップ
        worker.wait()
        dialog.close()

    def open_compiler_search_dialog(self, parent: QObject) -> Path | None:
        """
        コンパイラ検索ダイアログを開く
        戻り値: 選択されたパス、キャンセル時はNone
        """
        from feature.setting.view.dialog_compiler_search import CompilerSearchDialog

        # Handlerを生成（Viewは後で設定される）
        handler = di_handler.get_compiler_search_handler()

        # Dialogを生成（Handlerを注入）
        dialog = CompilerSearchDialog(
            parent,
            handler=handler,
        )

        # Navigatorがset_viewを呼ぶ（循環参照を避けるため、View生成後に設定）
        handler.set_view(dialog)

        dialog.exec_()

        # Handlerから結果を取得
        return handler.result_path

    def run_blocking_task(
            self,
            parent: QObject,
            title: str,
            initial_message: str,
            task_func: Callable[..., T],
            **task_kwargs
    ) -> T:
        """
        ブロッキングタスクを実行する（WaitDialogで進捗表示）
        
        Args:
            parent: 親ウィジェット
            title: ダイアログタイトル
            initial_message: 初期メッセージ
            task_func: 実行する関数
                - 必ずprogress_callback: Callable[[str], None]をキーワード引数として受け取ること
                - progress_callbackは進捗メッセージ（str）を受け取り、何も返さない
            **task_kwargs: task_funcに渡す追加のキーワード引数
        
        Returns:
            task_funcの戻り値
        
        Raises:
            task_func内で発生した例外
        """
        from PyQt5.QtCore import QEventLoop
        from shared.view.dialog_wait import WaitDialog
        from shared.view.task_runner import BlockingTaskWorker

        # noinspection PyTypeChecker
        dialog = WaitDialog(parent, title=title, message=initial_message)
        dialog.show()

        worker = BlockingTaskWorker(parent=dialog, task_func=task_func, **task_kwargs)
        worker.progress_updated.connect(dialog.set_message)

        loop = QEventLoop()
        worker.finished.connect(loop.quit)
        worker.start()

        loop.exec_()
        worker.wait()
        dialog.close()

        error = worker.get_error()
        if error:
            raise error

        result = worker.get_result()
        return result

    def open_setting_dialog(self, parent: QObject) -> None:
        """設定ダイアログを開く"""
        from feature.setting.view.dialog_setting import SettingEditDialog
        from app.di import app as di_app

        # Handlerを生成（Viewは後で設定される）
        handler = di_handler.get_setting_edit_handler(
            navigator=di_app.get_navigator(),
        )

        # Dialogを生成（Handlerを注入）
        dialog = SettingEditDialog(
            parent,
            handler=handler,
        )

        # Navigatorがset_viewを呼ぶ（循環参照を避けるため、View生成後に設定）
        handler.set_view(dialog.settings_edit_widget)

        dialog.exec_()

    def open_about_dialog(self, parent: QObject) -> None:
        """Aboutダイアログを開く"""
        from feature.about.view.dialog_about import AboutDialog

        # Handlerを生成（Viewは後で設定される）
        handler = di_handler.get_about_dialog_handler()

        # Dialogを生成（Handlerを注入）
        dialog = AboutDialog(
            parent,
            handler=handler,
        )

        # Navigatorがset_viewを呼ぶ（循環参照を避けるため、View生成後に設定）
        handler.set_view(dialog)

        dialog.exec_()

    def open_score_export_dialog(self, parent: QObject, target_id: TargetID) -> None:
        """点数エクスポートダイアログを開く"""
        from feature.export.view.dialog_score_export import ScoreExportDialog
        from feature.export.view.component.tab_simple import SimpleScoreExportTab
        from feature.export.view.component.tab_excel import ExcelScoreExportTab

        # View（タブ）を生成
        simple_tab = SimpleScoreExportTab(parent)
        excel_tab = ExcelScoreExportTab(parent)

        # Handlerを生成（Viewは後で設定される）
        simple_handler = di_handler.get_simple_score_export_tab_handler(view=None)
        excel_handler = di_handler.get_excel_score_export_tab_handler(
            view=None,
            target_id=target_id,
        )

        # Dialogを生成（Handlerを注入）
        dialog = ScoreExportDialog(
            parent,
            simple_tab=simple_tab,
            excel_tab=excel_tab,
            simple_handler=simple_handler,
            excel_handler=excel_handler,
        )

        # HandlerにViewを設定
        simple_handler.set_view(dialog)
        excel_handler.set_view(dialog)

        dialog.exec_()

    def open_scoring_dialog(self, parent: QObject) -> None:
        """採点ダイアログを開く（最初の生徒）"""
        from feature.scoring.view.dialog_scoring import ScoringDialog

        # Dialogを生成（Handlerは使用しない）
        dialog = ScoringDialog(parent)

        # 最初の生徒の状態を設定
        dialog.set_state(dialog.states.create_state_of_first_student())

        dialog.exec_()

    def open_scoring_dialog_with_student(self, parent: QObject, student_id) -> None:
        """採点ダイアログを開く（指定された生徒）"""
        from feature.scoring.view.dialog_scoring import ScoringDialog

        # Dialogを生成（Handlerは使用しない）
        dialog = ScoringDialog(parent)

        # 指定された生徒の状態を設定
        dialog.set_state(dialog.states.create_state_by_student_id(student_id))

        dialog.exec_()

    def open_testcase_list_edit_dialog(self, parent: QObject) -> None:
        """テストケース編集ダイアログを開く"""
        from feature.testcase.view.dialog_testcase_list_edit import TestCaseListEditDialog

        # Dialogを生成（Handlerは使用しない）
        dialog = TestCaseListEditDialog(parent)
        dialog.exec_()
