import random
import zipfile
from pathlib import Path

from PyQt5.QtWidgets import QDialog, QMessageBox

from app.di.state import get_current_project_id_state
from app.di.system import get_manaba_report_archive_io
from app.di.usecase import get_project_update_last_opened_usecase
from feature.projman.handler.interface import IProjectCreateView, IProjectCreateHandler, \
    NewProjectConfigDto
from feature.projman.usecase.interface import (
    IProjectCheckExistByNameUseCase,
    IProjectCreateUseCase,
)
from feature.projman.view.dialog_project_initialize import ProjectInitializeProgressDialog
from shared.domain.interface.state import IDebugModeState
from shared.domain.value.identifier import ProjectID
from shared.handler.interface import INavigator


class ProjectCreateHandler(IProjectCreateHandler):
    """
    ProjectCreateView専任のHandler
    責務: バリデーションとプロジェクト作成処理
    """

    def __init__(
            self,
            *,
            view: IProjectCreateView,
            navigator: INavigator,
            project_check_exist_usecase: IProjectCheckExistByNameUseCase,
            project_create_usecase: IProjectCreateUseCase,
            debug_mode_state: IDebugModeState,
    ):
        self._view = view
        self._navigator = navigator
        self._project_check_exist_usecase = project_check_exist_usecase
        self._project_create_usecase = project_create_usecase
        self._debug_mode_state = debug_mode_state

    # ===== IProjectCreateHandler実装 =====
    def on_view_initialized(self) -> None:
        """View初期化時に呼ばれる"""
        if self._debug_mode_state.get():
            self._view.set_project_name(f"proj-{random.randint(0, 10000)!s}")
            self._view.set_target_number("4")
            self._view.set_submission_archive_path(
                str(Path("~/report_5.zip").expanduser().resolve())
            )

    def on_create_requested(self) -> None:
        """プロジェクト作成要求"""
        # 値の取得
        project_name = self._view.get_project_name()
        target_number_str = self._view.get_target_number()
        archive_path_str = self._view.get_submission_archive_path()

        # バリデーション
        errors = self._validate(
            project_name=project_name,
            target_number_str=target_number_str,
            archive_path_str=archive_path_str,
        )

        if errors:
            self._view.show_validation_errors(errors)
            return

        # UseCaseでプロジェクトを作成
        try:
            archive_path = Path(archive_path_str)
            target_number = int(target_number_str)

            project_id = self._project_create_usecase.execute(
                project_name=project_name,
                target_number=target_number,
                zip_name=archive_path.name,
            )

            # 作成成功をViewに通知
            config = NewProjectConfigDto(
                project_name=project_name,
                target_number=target_number,
                manaba_report_archive_fullpath=archive_path,
            )
            self._view.notify_project_created(config)

            # Stateを更新（アプリケーション層の責務）
            state = get_current_project_id_state()
            assert state.get() is None, "Current project is already set. Failed to set new project."
            state.update(project_id)

            # ドメイン状態を更新（UseCaseの責務）
            get_project_update_last_opened_usecase().execute(project_id)

            # プロジェクト初期化ダイアログを表示（非同期実行）
            dialog = ProjectInitializeProgressDialog(
                manaba_report_archive_fullpath=archive_path,
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

    def _validate(
            self,
            *,
            project_name: str,
            target_number_str: str,
            archive_path_str: str
    ) -> list[str]:
        """入力値のバリデーションを行う"""
        errors = []

        # プロジェクト名のチェック
        project_name = project_name.strip()
        if not project_name:
            errors.append("プロジェクト名が入力されていません")
        else:
            try:
                ProjectID(project_name)
                # プロジェクト名の重複チェック
                if self._project_check_exist_usecase.execute(project_name):
                    errors.append("プロジェクト名はすでに存在します")
            except ValueError:
                errors.append("プロジェクト名に使用できない文字が含まれています")

        # 提出データのチェック
        if not archive_path_str:
            errors.append("提出データが選択されていません")
        else:
            path = Path(archive_path_str)
            if not path.is_absolute():
                errors.append("提出データのパスは絶対パスである必要があります")
            elif not path.exists():
                errors.append("指定された提出データファイルが存在しません")
            elif not zipfile.is_zipfile(path):
                errors.append("選択したファイルはZIP形式ではありません")
            elif not get_manaba_report_archive_io(path).validate_master_excel_exists():
                errors.append("ZIPファイル内に reportlist.xlsx が含まれていません")

        # 設問番号のチェック
        if not target_number_str:
            errors.append("設問番号が入力されていません")
        else:
            try:
                val = int(target_number_str)
                if not (0 <= val <= 99):
                    errors.append("設問番号は0から99の間である必要があります")
            except ValueError:
                errors.append("設問番号には数字を入力してください")

        return errors
