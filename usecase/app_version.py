from infra.repository.app_version import AppVersionRepository


class AppVersionGetTextUseCase:
    def __init__(
            self,
            *,
            app_version_repo: AppVersionRepository,
    ):
        self._app_version_repo = app_version_repo

    def execute(self) -> str:
        app_version = self._app_version_repo.get()
        return str(app_version)


class AppVersionCheckIsStableUseCase:
    def __init__(
            self,
            *,
            app_version_repo: AppVersionRepository,
    ):
        self._app_version_repo = app_version_repo

    def execute(self) -> bool:
        app_version = self._app_version_repo.get()
        return app_version.is_stable
