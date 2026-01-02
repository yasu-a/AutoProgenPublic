from PyQt5.QtWidgets import QDialog, QMessageBox

from app.di.state import get_current_project_id_state
from app.di.usecase import get_project_update_last_opened_usecase
from feature.projman.handler.interface import IProjectCreateView, IProjectCreateHandler
from feature.projman.usecase.interface import (
    IProjectCheckExistByNameUseCase,
    IProjectCreateUseCase,
)
from feature.projman.view.dialog_project_initialize import ProjectInitializeProgressDialog
from shared.handler.interface import INavigator


class ProjectCreateHandler(IProjectCreateHandler):
    """
    ProjectCreateView専任のHandler
    責務: バリデーションとプロジェクト作成処理
    Dialog Handlerとは無関係（独立性の原則）
    """

    def __init__(
            self,
            *,
            view: IProjectCreateView,
            navigator: INavigator,
            project_check_exist_usecase: IProjectCheckExistByNameUseCase,
            project_create_usecase: IProjectCreateUseCase,
    ):
        self._view = view
        self._navigator = navigator
        self._project_check_exist_usecase = project_check_exist_usecase
        self._project_create_usecase = project_create_usecase

    # ===== IProjectCreateHandler実装 =====
    def on_create_requested(self) -> None:
        """プロジェクト作成要求"""
        # バリデーション（View内のフィールドバリデーション）
        errors = self._view.validate_and_get_errors()

        # プロジェクト名の重複チェック（UseCaseレベル）
        if not errors:
            project_name = self._view.get_project_name()
            if self._project_check_exist_usecase.execute(project_name):
                errors.append("プロジェクト名はすでに存在します")

        if errors:
            self._view.show_validation_errors(errors)
            return

        # バリデーション済み結果を取得
        config = self._view.get_create_result()
        if config is None:
            return

        # UseCaseでプロジェクトを作成
        try:
            project_id = self._project_create_usecase.execute(
                project_name=config.project_name,
                target_number=config.target_number,
                zip_name=config.manaba_report_archive_fullpath.name,
            )

            # 作成成功をViewに通知
            self._view.notify_project_created(config)

            # Stateを更新（アプリケーション層の責務）
            state = get_current_project_id_state()
            assert state.get() is None, state.get()
            state.update(project_id)

            # ドメイン状態を更新（UseCaseの責務）
            get_project_update_last_opened_usecase().execute(project_id)

            # プロジェクト初期化ダイアログを表示（非同期実行）
            dialog = ProjectInitializeProgressDialog(
                manaba_report_archive_fullpath=config.manaba_report_archive_fullpath,
            )
            if dialog.exec_() != QDialog.Accepted:
                QMessageBox.critical(
                    dialog,
                    "プロジェクトの初期化",
                    dialog.get_error_object().message,
                    QMessageBox.Ok,
                )
                # 初期化失敗時はStateをクリア
                state.clear()
                return

            # 初期化完了後、Navigatorで画面遷移
            self._navigator.navigate_to_main_window(project_id)

        except Exception as e:
            self._view.show_validation_errors([f"プロジェクト作成に失敗しました: {e}"])
