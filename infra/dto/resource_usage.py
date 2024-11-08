from typing import NamedTuple


class ResourceUsage(NamedTuple):
    disk_read_count: int
    disk_write_count: int
    cpu_percent: int
    memory: int
