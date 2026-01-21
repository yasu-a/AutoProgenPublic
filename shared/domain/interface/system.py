from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Optional, Iterable, Callable, Generator, IO

from shared.domain.value.identifier import ProjectID, StudentID
from shared.infra.system.task import AbstractTask


class IProjectCoreIO(ABC):
    """プロジェクト内のファイル操作を行うCoreIOのインターフェース"""

    @abstractmethod
    def rmtree_folder(self, *, path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy_file_into_folder(
            self,
            *,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str | None = None,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy_files_in_folder_into_folder(
            self,
            *,
            src_folder_fullpath: Path,
            dst_folder_fullpath: Path,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy_folder(
            self,
            *,
            src_path: Path,
            dst_path: Path,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy_external_file_into_folder(
            self,
            *,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str | None = None,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def unlink(self, *, path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def write_json(self, *, json_fullpath: Path, body: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_json(self, *, json_fullpath: Path) -> Optional[Any]:
        raise NotImplementedError()

    @abstractmethod
    def touch(self, *, file_fullpath: Path,
              content_bytes: bytes = b"") -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_file_content_str(self, *, file_fullpath: Path) -> str:
        raise NotImplementedError()

    @abstractmethod
    def read_file_content_bytes(self, *, file_fullpath: Path) -> bytes:
        raise NotImplementedError()

    @abstractmethod
    def write_file_content_bytes(self, *, file_fullpath: Path,
                                 content_bytes: bytes) -> None:
        raise NotImplementedError()

    @abstractmethod
    def calculate_folder_checksum(self, *, folder_fullpath: Path) -> int:
        raise NotImplementedError()

    @abstractmethod
    def walk_files(self, *, folder_fullpath: Path, return_absolute: bool) \
            -> Iterable[Path]:
        raise NotImplementedError()

    @abstractmethod
    def get_file_mtime(self, *, file_fullpath: Path) -> datetime:
        raise NotImplementedError()

    @abstractmethod
    def get_folder_size(self, *, folder_fullpath: Path) -> int:
        raise NotImplementedError()


class IProjectCoreIOFactory(ABC):
    @abstractmethod
    def create_project_core_io(self, project_id: ProjectID) -> IProjectCoreIO:
        raise NotImplementedError()


class IGlobalCoreIO(ABC):
    """グローバル設定ファイル操作を行うCoreIOのインターフェース"""

    @abstractmethod
    def read_json(self, *, json_fullpath: Path) -> Optional[Any]:
        raise NotImplementedError()

    @abstractmethod
    def write_json(self, *, json_fullpath: Path, body: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_file_content_str(self, *, file_fullpath: Path) -> str:
        raise NotImplementedError()

    @abstractmethod
    def read_file_content_bytes(self, *, file_fullpath: Path) -> bytes:
        raise NotImplementedError()


# class ICurrentProjectCoreIO(ABC):
#     """現在のプロジェクトのファイル操作を行うCoreIOのインターフェース"""

#     @abstractmethod
#     def rmtree_folder(self, *, path: Path) -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def copy_file_into_folder(
#             self,
#             *,
#             src_file_fullpath: Path,
#             dst_folder_fullpath: Path,
#             dst_file_name: str | None = None,
#     ) -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def copy_files_in_folder_into_folder(
#             self,
#             *,
#             src_folder_fullpath: Path,
#             dst_folder_fullpath: Path,
#     ) -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def copy_folder(self, *, src_path: Path, dst_path: Path) -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def copy_external_file_into_folder(
#             self,
#             *,
#             src_file_fullpath: Path,
#             dst_folder_fullpath: Path,
#             dst_file_name: str | None = None,
#     ) -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def unlink(self, *, path: Path) -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def write_json(self, *, json_fullpath: Path, body: Any) -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def read_json(self, *, json_fullpath: Path) -> Optional[Any]:
#         raise NotImplementedError()

#     @abstractmethod
#     def touch(self, *, file_fullpath: Path, content_bytes: bytes = b"") -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def read_file_content_str(self, *, file_fullpath: Path) -> str:
#         raise NotImplementedError()

#     @abstractmethod
#     def read_file_content_bytes(self, *, file_fullpath: Path) -> bytes:
#         raise NotImplementedError()

#     @abstractmethod
#     def write_file_content_bytes(self, *, file_fullpath: Path, content_bytes: bytes) -> None:
#         raise NotImplementedError()

#     @abstractmethod
#     def calculate_folder_checksum(self, *, folder_fullpath: Path) -> int:
#         raise NotImplementedError()

#     @abstractmethod
#     def walk_files(self, *, folder_fullpath: Path, return_absolute: bool) -> Iterable[Path]:
#         raise NotImplementedError()

#     @abstractmethod
#     def get_file_mtime(self, *, file_fullpath: Path) -> datetime:
#         raise NotImplementedError()

#     @abstractmethod
#     def get_folder_size(self, *, folder_fullpath: Path) -> int:
#         raise NotImplementedError()


class ITaskManager(ABC):
    """タスク管理を行うインターフェース"""

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def count_active(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def is_empty(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def enqueue(self, task: AbstractTask) -> None:
        raise NotImplementedError()

    @abstractmethod
    def terminate(self, progress_callback: Callable[[str], None]) -> None:
        raise NotImplementedError()


class IManabaReportArchiveIO(ABC):
    @contextmanager
    @abstractmethod
    def open_master_excel(
            self,
            archive_fullpath: Path,
    ) -> Generator[IO[bytes], None, None]:
        raise NotImplementedError()

    @abstractmethod
    def validate_master_excel_exists(
            self,
            *,
            archive_fullpath: Path,
    ) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def validate_archive_contents(
            self,
            *,
            student_submission_folder_names: set[str],
            archive_fullpath: Path,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def iter_student_submission_archive_contents(
            self,
            *,
            student_id: StudentID,
            student_submission_folder_name: str,
            archive_fullpath: Path,
    ) -> Iterable[tuple[PurePosixPath, IO[bytes]]]:  # [^]
        raise NotImplementedError()
