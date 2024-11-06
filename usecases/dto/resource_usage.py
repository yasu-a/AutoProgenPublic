from dataclasses import dataclass


@dataclass
class ResourceUsageGetResult:
    disk_read_count: int
    disk_write_count: int
    cpu_percent: int
    memory_mega_bytes: int
