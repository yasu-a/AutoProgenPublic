from domain.model.app_version import AppVersion
from infra.io.files.global_ import GlobalCoreIO
from infra.path_provider.global_ import GlobalPathProvider


class AppVersionRepository:
    def __init__(
            self,
            *,
            global_path_provider: GlobalPathProvider,
            global_core_io: GlobalCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._global_core_io = global_core_io

    def get(self) -> AppVersion:
        json_fullpath = self._global_path_provider.app_version_json_fullpath()
        json_body = self._global_core_io.read_json(json_fullpath=json_fullpath)
        return AppVersion.from_json(json_body)
