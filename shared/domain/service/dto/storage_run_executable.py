from dataclasses import dataclass


@dataclass(frozen=True)
class StorageExecuteServiceResult:
    stdout_text: str
