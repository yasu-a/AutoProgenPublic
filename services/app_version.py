from domain.models.app_version import AppVersion
from infra.repositories.app_version import AppVersionRepository


class AppVersionGetService:
    def __init__(
            self,
            *,
            app_version_repo: AppVersionRepository,
    ):
        self._app_version_repo = app_version_repo

    def execute(self) -> AppVersion:
        return self._app_version_repo.get()
