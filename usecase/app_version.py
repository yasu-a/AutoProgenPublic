from service.app_version import AppVersionGetService


class AppVersionGetTextUseCase:
    def __init__(
            self,
            *,
            app_version_get_service: AppVersionGetService,
    ):
        self._app_version_get_service = app_version_get_service

    def execute(self) -> str:
        app_version = self._app_version_get_service.execute()
        return str(app_version)


class AppVersionCheckIsStableUseCase:
    def __init__(
            self,
            *,
            app_version_get_service: AppVersionGetService,
    ):
        self._app_version_get_service = app_version_get_service

    def execute(self) -> bool:
        app_version = self._app_version_get_service.execute()
        return app_version.is_stable
