from feature.workspace.usecase.dto import ResourceUsageGetResult
from feature.workspace.usecase.interface import IResourceUsageGetUseCase
from shared.infra.system.resource_usage import ResourceUsageIO


class ResourceUsageGetUseCase(IResourceUsageGetUseCase):
    def __init__(
            self,
            *,
            resource_usage_io: ResourceUsageIO,
    ):
        self._resource_usage_io = resource_usage_io

    def execute(self) -> ResourceUsageGetResult:
        usage = self._resource_usage_io.get_stat()
        return ResourceUsageGetResult(
            disk_read_count=usage.disk_read_count,
            disk_write_count=usage.disk_write_count,
            cpu_percent=usage.cpu_percent,
            memory_mega_bytes=usage.memory // (1 << 20),
        )
