from domain.models.settings import GlobalConfig
from services.global_config import GlobalConfigGetService, GlobalConfigPutService


class GlobalConfigGetUseCase:
    def __init__(
            self,
            *,
            global_config_get_service: GlobalConfigGetService,
    ):
        self._global_config_get_service = global_config_get_service

    def execute(self) -> GlobalConfig:
        return self._global_config_get_service.execute()


class GlobalConfigPutUseCase:
    def __init__(
            self,
            *,
            global_config_put_service: GlobalConfigPutService,
    ):
        self._global_config_put_service = global_config_put_service

    def execute(self, global_config: GlobalConfig) -> None:
        self._global_config_put_service.execute(global_config)
