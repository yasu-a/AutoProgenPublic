from domain.model.app_version import AppVersion
from infra.io.files.global_ import GlobalCoreIO
from infra.path_layout import AppPathLayout


class AppVersionRepository:
    def __init__(
            self,
            *,
            app_path_layout: AppPathLayout,
            global_core_io: GlobalCoreIO,
    ):
        self._app_path_layout = app_path_layout
        self._global_core_io = global_core_io

    def get(self) -> AppVersion:
        json_fullpath = self._app_path_layout.app_version_json
        json_body = self._global_core_io.read_json(json_fullpath=json_fullpath)
        return AppVersion.from_json(json_body)
