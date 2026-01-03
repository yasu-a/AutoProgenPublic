import psutil

from shared.domain.interface.gateway import IResourceUsageGateway, ResourceUsageDto


class ResourceUsageGateway(IResourceUsageGateway):
    def execute(self) -> ResourceUsageDto:
        process = psutil.Process()
        io_count = process.io_counters()
        return ResourceUsageDto(
            disk_read_count=io_count.read_count,
            disk_write_count=io_count.write_count,
            cpu_percent=int(psutil.cpu_percent()),
            memory=int(process.memory_info().rss),
        )

