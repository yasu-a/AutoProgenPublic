from files.core.project import ProjectCoreIO
from files.path_providers.global_ import GlobalPathProvider


class TestRunSourceRepository:
    def __init__(
            self,
            *,
            global_path_provider: GlobalPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._project_core_io = project_core_io

    def get(self) -> bytes:
        source_file_fullpath = self._global_path_provider.test_source_file_fullpath()
        return self._project_core_io.read_file_content_bytes(
            file_fullpath=source_file_fullpath,
        )
