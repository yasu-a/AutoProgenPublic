from feature.workspace.usecase.interface import IResourceUsageGetUseCase, ResourceUsageGetResultDto
from shared.domain.interface.gateway import IResourceUsageGateway


class ResourceUsageGetUseCase(IResourceUsageGetUseCase):
    def __init__(
            self,
            *,
            resource_usage_gateway: IResourceUsageGateway,
    ):
        self._resource_usage_gateway = resource_usage_gateway

    def execute(self) -> ResourceUsageGetResultDto:
        usage = self._resource_usage_gateway.execute()
        return ResourceUsageGetResultDto(
            disk_read_count=usage.disk_read_count,
            disk_write_count=usage.disk_write_count,
            cpu_percent=usage.cpu_percent,
            memory_mega_bytes=usage.memory // (1 << 20),
        )
