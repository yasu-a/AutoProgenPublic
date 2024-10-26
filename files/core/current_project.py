from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Iterable

from app_logging import create_logger
from domain.models.values import ProjectID
from files.core.project import ProjectCoreIO


class CurrentProjectCoreIO:
    _logger = create_logger()

    def __init__(
            self,
            *,
            current_project_id: ProjectID,
            project_core_io: ProjectCoreIO,
    ):
        self._current_project_id = current_project_id
        self._project_core_io = project_core_io

    def rmtree_folder(
            self,
            *,
            path: Path,
    ) -> None:
        self._project_core_io.rmtree_folder(
            project_id=self._current_project_id,
            path=path,
        )

    def copy_file_into_folder(
            self,
            *,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str = None,
    ) -> None:
        self._project_core_io.copy_file_into_folder(
            project_id=self._current_project_id,
            src_file_fullpath=src_file_fullpath,
            dst_folder_fullpath=dst_folder_fullpath,
            dst_file_name=dst_file_name,
        )

    def copy_files_in_folder_into_folder(
            self,
            *,
            src_folder_fullpath: Path,
            dst_folder_fullpath: Path,
    ) -> None:
        self._project_core_io.copy_files_in_folder_into_folder(
            project_id=self._current_project_id,
            src_folder_fullpath=src_folder_fullpath,
            dst_folder_fullpath=dst_folder_fullpath,
        )

    def copy_folder(
            self,
            *,
            src_path: Path,
            dst_path: Path,
    ) -> None:
        self._project_core_io.copy_folder(
            project_id=self._current_project_id,
            src_path=src_path,
            dst_path=dst_path,
        )

    def copy_external_file_into_folder(
            self,
            *,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str = None,
    ) -> None:
        self._project_core_io.copy_external_file_into_folder(
            project_id=self._current_project_id,
            src_file_fullpath=src_file_fullpath,
            dst_folder_fullpath=dst_folder_fullpath,
            dst_file_name=dst_file_name,
        )

    def unlink(
            self,
            *,
            path: Path,
    ) -> None:
        self._project_core_io.unlink(
            project_id=self._current_project_id,
            path=path,
        )

    def write_json(
            self,
            *,
            json_fullpath: Path,
            body: Any,
    ):
        self._project_core_io.write_json(
            project_id=self._current_project_id,
            json_fullpath=json_fullpath,
            body=body,
        )

    def read_json(
            self, *,
            json_fullpath: Path,
    ) -> Optional:
        return self._project_core_io.read_json(
            project_id=self._current_project_id,
            json_fullpath=json_fullpath)

    def touch(
            self, *,
            file_fullpath: Path,
            content_bytes: bytes = b"",
    ) -> None:
        self._project_core_io.touch(
            project_id=self._current_project_id,
            file_fullpath=file_fullpath,
            content_bytes=content_bytes)

    def read_file_content_str(
            self,
            *,
            file_fullpath: Path,
    ) -> str:
        return self._project_core_io.read_file_content_str(
            project_id=self._current_project_id,
            file_fullpath=file_fullpath,
        )

    def read_file_content_bytes(
            self, *,
            file_fullpath: Path,
    ) -> bytes:
        return self._project_core_io.read_file_content_bytes(
            project_id=self._current_project_id,
            file_fullpath=file_fullpath,
        )

    def write_file_content_bytes(
            self, *,
            file_fullpath: Path,
            content_bytes: bytes,
    ) -> None:
        self._project_core_io.write_file_content_bytes(
            project_id=self._current_project_id,
            file_fullpath=file_fullpath,
            content_bytes=content_bytes,
        )

    def calculate_folder_checksum(
            self,
            *,
            folder_fullpath: Path,
    ) -> int:
        return self._project_core_io.calculate_folder_checksum(
            project_id=self._current_project_id,
            folder_fullpath=folder_fullpath,
        )

    def walk_files(
            self,
            *,
            folder_fullpath: Path,
            return_absolute: bool,
    ) -> Iterable[Path]:
        yield from self._project_core_io.walk_files(
            project_id=self._current_project_id,
            folder_fullpath=folder_fullpath,
            return_absolute=return_absolute,
        )

    def get_file_mtime(
            self,
            *,
            file_fullpath: Path,
    ) -> datetime:
        return self._project_core_io.get_file_mtime(
            project_id=self._current_project_id,
            file_fullpath=file_fullpath,
        )
