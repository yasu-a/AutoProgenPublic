from pathlib import Path

from shared.domain.interface.repository import IAppVersionProvider
from shared.domain.interface.system import IGlobalCoreIO
from shared.domain.value.app_version import AppVersion


class JsonAppVersionProvider(IAppVersionProvider):
    """JSONファイルからアプリケーションバージョンを提供するプロバイダー"""

    def __init__(
            self,
            *,
            app_version_json_fullpath: Path,
            global_core_io: IGlobalCoreIO,
    ):
        self._app_version_json_fullpath = app_version_json_fullpath
        self._global_core_io = global_core_io

    def provide(self) -> AppVersion:
        """アプリケーションバージョンを提供"""
        json_body = self._global_core_io.read_json(json_fullpath=self._app_version_json_fullpath)
        return AppVersion.from_json(json_body)
