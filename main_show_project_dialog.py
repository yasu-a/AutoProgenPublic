import sys
from unittest.mock import MagicMock, patch

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog

from app.qt_style import apply_qt_style
from feature.projman.handler.project_create import ProjectCreateHandler
from feature.projman.view.project_create_view import ProjectCreateView
from shared.domain.interface.state import IDebugModeState
from shared.domain.value.identifier import ProjectID
from shared.handler.interface import INavigator


def main():
    """
    ProjectCreateViewを単体表示し、動作確認を行うスクリプト。
    Workspaceのリファクタリング方針に基づき、DIと型定義を整理しています。
    """
    app = QApplication(sys.argv)

    # 共通のスタイル適用（app_infoをセットしないことで単体テスト時の副作用を抑制）
    apply_qt_style(app, set_app_info=False)

    # 1. Navigatorのモック（遷移の代わりにダイアログで確認）
    mock_navigator = MagicMock(spec=INavigator)

    def on_navigate_success(project_id: ProjectID):
        # 型チェックの確認（リファクタリングで厳格化したため）
        if not isinstance(project_id, ProjectID):
            print(f"Error: Invalid type for project_id: {type(project_id)}")
            return

        QMessageBox.information(
            None,
            "Success",
            f"プロジェクト作成完了通知を受け取りました。\n"
            f"Target ProjectID: {project_id!s}\n\n"
            f"実際にはここからメイン画面へ遷移します。"
        )

    mock_navigator.navigate_to_main_window.side_effect = on_navigate_success

    # 2. UseCaseのモック（重複チェック、作成、最終更新日更新）
    mock_check_exist = MagicMock()
    mock_check_exist.execute.return_value = False  # 重複なし

    mock_create = MagicMock()
    # 常に新しいProjectIDを返すように設定
    mock_create.execute.return_value = ProjectID("test-project-2026")

    mock_update_last_open = MagicMock()
    # メソッド名がsaveからupdateに変更された場合を考慮したモック
    if hasattr(mock_update_last_open, 'update'):
        mock_update_last_open.update.return_value = None
    else:
        mock_update_last_open.execute.return_value = None

    # 3. Stateのモック（自動入力機能を確認するためDebugモードをON）
    mock_debug_state = MagicMock(spec=IDebugModeState)
    mock_debug_state.get.return_value = True

    # 4. 外部ダイアログと依存取得関数のパッチ
    # プログレスダイアログなどの「重いUI」や「グローバルなDI取得」を差し替える
    patch_path_progress = 'feature.projman.handler.project_create.ProjectInitializeProgressDialog'
    patch_path_usecase_getter = 'feature.projman.handler.project_create.get_project_update_last_opened_usecase'

    with patch(patch_path_progress) as MockProgressDialog, \
            patch(patch_path_usecase_getter) as mock_getter:

        # get_xxx() 関数がモックを返すように設定
        mock_getter.return_value = mock_update_last_open

        # プログレスダイアログが即座に成功を返すように設定
        mock_dialog_instance = MockProgressDialog.return_value
        mock_dialog_instance.exec_.return_value = QDialog.Accepted

        # 5. ViewとHandlerの構築 (Constructor DI)
        view = ProjectCreateView()

        # Workspaceでの方針（明示的なフィールド、StagePathの廃止）に倣い、
        # 引数の意図が明確になるように配置
        handler = ProjectCreateHandler(
            view=view,
            navigator=mock_navigator,
            project_check_exist_usecase=mock_check_exist,
            project_create_usecase=mock_create,
            project_update_last_open_usecase=mock_update_last_open,
            debug_mode_state=mock_debug_state,
        )
        view.set_handler(handler)

        # 6. ウィンドウ表示
        # noinspection PyUnresolvedReferences
        view.setWindowTitle("Unit Test - ProjectCreateView")
        view.resize(650, 450)
        # noinspection PyUnresolvedReferences
        view.show()

        print("ProjectCreateView test script is running...")
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()