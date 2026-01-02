from shared.domain.interface.repository import IAppVersionProvider
from shared.domain.value.app_version import AppVersion
from shared.infra.path_provider.global_ import GlobalPathProvider
from shared.infra.system.global_core_io import GlobalCoreIO


class JsonAppVersionProvider(IAppVersionProvider):
    """JSONファイルからアプリケーションバージョンを提供するプロバイダー"""

    def __init__(
            self,
            *,
            global_path_provider: GlobalPathProvider,
            global_core_io: GlobalCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._global_core_io = global_core_io

    def provide(self) -> AppVersion:
        """アプリケーションバージョンを提供"""
        json_fullpath = self._global_path_provider.app_version_json_fullpath()
        json_body = self._global_core_io.read_json(json_fullpath=json_fullpath)
        return AppVersion.from_json(json_body)
