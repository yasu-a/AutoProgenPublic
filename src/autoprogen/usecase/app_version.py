from autoprogen.infra.repository.app_version import AppVersionRepository


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
