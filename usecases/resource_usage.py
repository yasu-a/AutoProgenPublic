from infra.io.resource_usage import ResourceUsageIO
from usecases.dto.resource_usage import ResourceUsageGetResult


class ResourceUsageGetUseCase:
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
