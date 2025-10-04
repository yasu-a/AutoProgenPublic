from dataclasses import dataclass
from functools import cached_property
from typing import TypeVar


@dataclass(frozen=True)
class SourceFileItem:
    content_bytes: bytes
    encoding: str

    @cached_property
    def content_text(self) -> str:
        return self.content_bytes.decode(self.encoding)


@dataclass(frozen=True)
class ExecutableFileItem:
    content_bytes: bytes


StudentDynamicFileItemType = TypeVar(
    "StudentDynamicFileItemType",
    bound=SourceFileItem | ExecutableFileItem,
)
