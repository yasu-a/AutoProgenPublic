import psutil

from infra.dto.resource_usage import ResourceUsage


class ResourceUsageIO:
    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic
    def get_stat(self) -> ResourceUsage:
        process = psutil.Process()
        io_count = process.io_counters()
        return ResourceUsage(
            disk_read_count=io_count.read_count,
            disk_write_count=io_count.write_count,
            cpu_percent=int(process.cpu_percent()),
            memory=int(process.memory_info().rss),
        )
