from PyQt5.QtWidgets import (
    QWidget,
)

from autoprogen.control.dialog_settings_edit import AbstractSettingsEditDialog
from autoprogen.control.widget_project_settings import ProjectSettingsEditWidget
from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.source_code_check import SourceCodeCheckCatalog
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.project_settings import ProjectSettingsGetUseCase, ProjectSettingsPutUseCase


class ProjectSettingsEditDialog(AbstractSettingsEditDialog[ProjectSettings]):
    """プロジェクト設定を読み込み、保存を明示したときだけ書き込む。"""

    def __init__(
            self,
            parent: QWidget = None,
            *,
            catalog: SourceCodeCheckCatalog,
            student_names: dict[StudentID, str],
            project_settings_get_usecase: ProjectSettingsGetUseCase,
            project_settings_put_usecase: ProjectSettingsPutUseCase,
    ) -> None:
        """現在のプロジェクト設定を表示する。"""
        super().__init__(parent)
        self._get_usecase = project_settings_get_usecase
        self._put_usecase = project_settings_put_usecase
        self.setWindowTitle("プロジェクト設定")
        self.setModal(True)
        self.resize(1130, 680)
        self._settings_view = ProjectSettingsEditWidget(
            self,
            catalog=catalog,
            student_names=student_names,
        )
        self.content_layout.addWidget(self._settings_view)
        self.add_standard_buttons()
        self.set_data(self._get_usecase.execute())

    def _set_data(self, data: ProjectSettings) -> None:
        """プロジェクト設定を編集Widgetへ反映する。"""
        self._settings_view.set_data(data)

    def get_data(self) -> ProjectSettings:
        """編集Widgetから現在のプロジェクト設定を返す。"""
        return self._settings_view.get_data()

    def save_data(self, data: ProjectSettings) -> None:
        """プロジェクト設定をUseCase経由で保存する。"""
        self._put_usecase.execute(data)
