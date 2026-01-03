import sys
from unittest.mock import MagicMock, patch

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog

from app.qt_style import apply_qt_style
from feature.projman.handler.project_create import ProjectCreateHandler
from feature.projman.view.project_create_view import ProjectCreateView
from shared.domain.interface.state import IDebugModeState, ICurrentProjectIDState
from shared.domain.value.identifier import ProjectID
from shared.handler.interface import INavigator


def main():
    """
    ProjectCreateViewを単体で表示し、動作確認を行うスクリプト
    """
    app = QApplication(sys.argv)
    apply_qt_style(app, set_app_info=False)

    # 1. Navigatorのモック作成
    # 画面遷移の代わりにメッセージボックスを表示する
    mock_navigator = MagicMock(spec=INavigator)

    def mock_navigate(project_id: ProjectID):
        QMessageBox.information(
            None,
            "確認",
            f"プロジェクト作成プロセスが完了しました。\n"
            f"ProjectID: {project_id}\n\n"
            f"（実際にはここでメイン画面へ遷移します）"
        )
        # ダイアログを閉じずにそのまま継続（再度作成可能）

    mock_navigator.navigate_to_main_window.side_effect = mock_navigate

    # 2. UseCaseのモック作成
    # プロジェクト名重複チェック: 常に False (重複なし) を返す
    mock_check_exist = MagicMock()
    mock_check_exist.execute.return_value = False

    # プロジェクト作成: ダミーのIDを返す
    mock_create = MagicMock()
    mock_create.execute.return_value = ProjectID("test_proj_001")

    # 3. Stateのモック作成 (デバッグモード有効)
    # リファクタリングで追加された自動入力機能を確認するためTrueにする
    mock_debug_state = MagicMock(spec=IDebugModeState)
    mock_debug_state.get.return_value = True

    mock_cpi_state = MagicMock(spec=ICurrentProjectIDState)
    mock_cpi_state.update.return_value = None
    mock_cpi_state.get.return_value = None

    # 4. Handler内で使用されるグローバルDI関数やクラスのパッチ
    # これを行わないと、裏で本物のファイル操作やDB接続が走ったりエラーになったりする
    with patch(
            'feature.projman.handler.project_create.get_project_update_last_opened_usecase') as mock_update_getter, \
            patch(
                'feature.projman.handler.project_create.ProjectInitializeProgressDialog') as MockDialogClass:
        # UseCase.execute() のモック
        mock_update_usecase = MagicMock()
        mock_update_getter.return_value = mock_update_usecase

        # 初期化ダイアログのモック（成功したことにして即座に閉じる）
        mock_dialog_instance = MockDialogClass.return_value
        mock_dialog_instance.exec_.return_value = QDialog.Accepted

        # 5. ViewとHandlerの構築
        view = ProjectCreateView()

        handler = ProjectCreateHandler(
            view=view,
            navigator=mock_navigator,
            project_check_exist_usecase=mock_check_exist,
            project_create_usecase=mock_create,
            debug_mode_state=mock_debug_state,
        )
        view.set_handler(handler)

        # 6. 表示
        view.setWindowTitle("Project Create View (Test Mode)")
        view.resize(600, 400)
        view.show()

        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
