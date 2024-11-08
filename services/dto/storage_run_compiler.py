from dataclasses import dataclass


@dataclass(frozen=True)
class StorageCompileServiceResult:
    output: str
