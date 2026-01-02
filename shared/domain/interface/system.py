from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Iterable, Callable

from shared.domain.value.identifier import ProjectID
from shared.infra.system.task import AbstractTask


class IProjectCoreIO(ABC):
    """プロジェクト内のファイル操作を行うCoreIOのインターフェース"""

    @abstractmethod
    def rmtree_folder(self, *, project_id: ProjectID, path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy_file_into_folder(
            self,
            *,
            project_id: ProjectID,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str | None = None,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy_files_in_folder_into_folder(
            self,
            *,
            project_id: ProjectID,
            src_folder_fullpath: Path,
            dst_folder_fullpath: Path,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy_folder(
            self,
            *,
            project_id: ProjectID,
            src_path: Path,
            dst_path: Path,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def copy_external_file_into_folder(
            self,
            *,
            project_id: ProjectID,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str | None = None,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def unlink(self, *, project_id: ProjectID, path: Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def write_json(self, *, project_id: ProjectID, json_fullpath: Path, body: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_json(self, *, project_id: ProjectID, json_fullpath: Path) -> Optional[Any]:
        raise NotImplementedError()

    @abstractmethod
    def touch(self, *, project_id: ProjectID, file_fullpath: Path,
              content_bytes: bytes = b"") -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_file_content_str(self, *, project_id: ProjectID, file_fullpath: Path) -> str:
        raise NotImplementedError()

    @abstractmethod
    def read_file_content_bytes(self, *, project_id: ProjectID, file_fullpath: Path) -> bytes:
        raise NotImplementedError()

    @abstractmethod
    def write_file_content_bytes(self, *, project_id: ProjectID, file_fullpath: Path,
                                 content_bytes: bytes) -> None:
        raise NotImplementedError()

    @abstractmethod
    def calculate_folder_checksum(self, *, project_id: ProjectID, folder_fullpath: Path) -> int:
        raise NotImplementedError()

    @abstractmethod
    def walk_files(self, *, project_id: ProjectID, folder_fullpath: Path, return_absolute: bool) -> \
    Iterable[Path]:
        raise NotImplementedError()

    @abstractmethod
    def get_file_mtime(self, *, project_id: ProjectID, file_fullpath: Path) -> datetime:
        raise NotImplementedError()

    @abstractmethod
    def get_folder_size(self, *, project_id: ProjectID, folder_fullpath: Path) -> int:
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


class ICurrentProjectCoreIO(ABC):
    """現在のプロジェクトのファイル操作を行うCoreIOのインターフェース"""

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
    def copy_folder(self, *, src_path: Path, dst_path: Path) -> None:
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
    def touch(self, *, file_fullpath: Path, content_bytes: bytes = b"") -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_file_content_str(self, *, file_fullpath: Path) -> str:
        raise NotImplementedError()

    @abstractmethod
    def read_file_content_bytes(self, *, file_fullpath: Path) -> bytes:
        raise NotImplementedError()

    @abstractmethod
    def write_file_content_bytes(self, *, file_fullpath: Path, content_bytes: bytes) -> None:
        raise NotImplementedError()

    @abstractmethod
    def calculate_folder_checksum(self, *, folder_fullpath: Path) -> int:
        raise NotImplementedError()

    @abstractmethod
    def walk_files(self, *, folder_fullpath: Path, return_absolute: bool) -> Iterable[Path]:
        raise NotImplementedError()

    @abstractmethod
    def get_file_mtime(self, *, file_fullpath: Path) -> datetime:
        raise NotImplementedError()

    @abstractmethod
    def get_folder_size(self, *, folder_fullpath: Path) -> int:
        raise NotImplementedError()


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
    def terminate(self, callback: Callable[[str], None]) -> None:
        raise NotImplementedError()
