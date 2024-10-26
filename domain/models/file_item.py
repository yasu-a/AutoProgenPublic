from dataclasses import dataclass
from typing import TypeVar


#
# class AbstractFileItem:
#     @classmethod
#     def _validate_path(cls, path: Path) -> bool:
#         raise NotImplementedError()
#
#     def __init__(self, path: Path):
#         if not self._validate_path(path):
#             raise ValueError(f"Invalid path for file item class {type(self).__name__}: {path!s}")
#         self._path = path
#
#     @property
#     def path(self):
#         return self._path
#
#     @property
#     def content_bytes(self) -> bytes:
#         raise NotImplementedError()
#
#
# class AbstractTextFileItem(AbstractFileItem):
#     def __init__(self, path: Path, content_text: str):
#         super().__init__(path)
#         self._content_text = content_text
#
#     @property
#     def content_bytes(self) -> bytes:
#         return self._content_text.encode("utf-8")
#
#     @property
#     def content_text(self) -> str:
#         return self._content_text
#
#
# class AbstractBinaryFileItem(AbstractFileItem):
#     def __init__(self, path: Path, content_bytes: bytes):
#         super().__init__(path)
#         self._content_bytes = content_bytes
#
#     @property
#     def content_bytes(self) -> bytes:
#         return self._content_bytes
#

@dataclass(frozen=True)
class SourceFileItem:
    content_text: str


@dataclass(frozen=True)
class ExecutableFileItem:
    content_bytes: bytes


StudentDynamicFileItemType = TypeVar(
    "StudentDynamicFileItemType",
    bound=SourceFileItem | ExecutableFileItem,
)
#
#
# @dataclass(frozen=True)
# class IOSessionFileItem:
#     path: Path
#     content_bytes: bytes
#
#     def __post_init__(self):
#         if self.path.is_absolute():
#             raise ValueError("\"path\" of IOSessionFileItem must be relative")
#
#
# @dataclass(frozen=True)
# class FullQualifiedIOSessionFileItem(IOSessionFileItem):
#     fullpath: Path
#
#     def __post_init__(self):
#         if not self.path.is_absolute():
#             raise ValueError("\"fullpath\" of FullQualifiedIOSessionFileItem must be absolute")
#
#
# class IOSessionFileItemList(list[IOSessionFileItem]):
#     pass
#
#
# class FullQualifiedIOSessionFileItemList(list[FullQualifiedIOSessionFileItem]):
#     pass
