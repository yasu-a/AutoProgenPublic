from domain.models.settings import GlobalConfig
from files.repositories.global_config import GlobalConfigRepository


class GlobalConfigGetService:
    def __init__(
            self,
            *,
            global_config_repo: GlobalConfigRepository,
    ):
        self._global_config_repo = global_config_repo

    def execute(self) -> GlobalConfig:
        return self._global_config_repo.get()


class GlobalConfigPutService:
    def __init__(
            self,
            *,
            global_config_repo: GlobalConfigRepository,
    ):
        self._global_config_repo = global_config_repo

    def execute(self, global_config: GlobalConfig) -> None:
        self._global_config_repo.put(global_config)
