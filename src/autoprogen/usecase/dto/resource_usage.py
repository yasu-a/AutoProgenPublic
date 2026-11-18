from dataclasses import dataclass


@dataclass
class ResourceUsageGetResult:
    """ステータス表示へ渡すプロセスのリソース使用量。"""

    disk_read_count: int  # プロセスが実行したディスク読み込み回数。
    disk_write_count: int  # プロセスが実行したディスク書き込み回数。
    cpu_percent: int  # プロセスのCPU使用率。
    memory_mega_bytes: int  # プロセスのメモリ使用量（MB）。
