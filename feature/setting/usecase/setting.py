from feature.setting.usecase.interface import ISettingGetUseCase, ISettingPutUseCase
from shared.domain.value.setting import Setting
from shared.infra.repository.setting import SettingRepository


class SettingGetUseCase(ISettingGetUseCase):
    def __init__(
            self,
            *,
            setting_repo: SettingRepository,
    ):
        self._setting_repo = setting_repo

    def execute(self) -> Setting:
        return self._setting_repo.get()


class SettingPutUseCase(ISettingPutUseCase):
    def __init__(
            self,
            *,
            setting_repo: SettingRepository,
    ):
        self._setting_repo = setting_repo

    def execute(self, setting: Setting) -> None:
        self._setting_repo.put(setting)
