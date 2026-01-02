from feature.export.usecase.interface import IExportSettingGetUseCase, ExportSettingDto
from shared.infra.repository.setting import SettingRepository


class ExportSettingGetUseCase(IExportSettingGetUseCase):
    def __init__(self, *, setting_repo: SettingRepository):
        self._setting_repo = setting_repo

    def execute(self) -> ExportSettingDto:
        """エクスポート設定を取得"""
        setting = self._setting_repo.get()
        return ExportSettingDto(
            backup_before_export=setting.backup_before_export,
        )
