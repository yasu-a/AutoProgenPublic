from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from autoprogen.control.widget_project_settings import ProjectSettingsEditWidget
from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.source_code_check import SourceCodeCheckCatalog
from autoprogen.usecase.project_settings import ProjectSettingsGetUseCase, ProjectSettingsPutUseCase
from autoprogen.util.app_logging import create_logger


class ProjectSettingsEditDialog(QDialog):
    """プロジェクト設定を読み込み、保存を明示したときだけ書き込む。"""

    _logger = create_logger()

    def __init__(
            self,
            parent: QWidget = None,
            *,
            catalog: SourceCodeCheckCatalog,
            project_settings_get_usecase: ProjectSettingsGetUseCase,
            project_settings_put_usecase: ProjectSettingsPutUseCase,
    ) -> None:
        """現在のプロジェクト設定を表示する。"""
        super().__init__(parent)
        self._get_usecase = project_settings_get_usecase
        self._put_usecase = project_settings_put_usecase
        self._initial_settings: ProjectSettings = self._get_usecase.execute()
        self._has_changes = False

        self.setWindowTitle("プロジェクト設定")
        self.setModal(True)
        self.resize(1130, 680)
        layout = QVBoxLayout(self)
        self._settings_view = ProjectSettingsEditWidget(self, catalog=catalog)
        self._settings_view.set_data(self._initial_settings)
        layout.addWidget(self._settings_view)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel, parent=self,
        )
        self._buttons.button(QDialogButtonBox.Save).setText("保存")
        self._buttons.button(QDialogButtonBox.Cancel).setText("キャンセル")
        self._buttons.button(QDialogButtonBox.Save).clicked.connect(self._save)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    @property
    def has_changes(self) -> bool:
        """保存済みの変更が存在するかを返す。"""
        return self._has_changes

    def _save(self) -> None:
        """変更がある場合だけRepositoryへ保存する。"""
        try:
            settings = self._settings_view.get_data()
            if settings != self._initial_settings:
                self._put_usecase.execute(settings)
                self._has_changes = True
        except Exception as error:
            self._logger.exception("プロジェクト設定の保存に失敗しました")
            QMessageBox.critical(self, "プロジェクト設定", f"設定を保存できませんでした。\n{error}")
            return
        self.accept()
