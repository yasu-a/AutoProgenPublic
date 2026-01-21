import hashlib
import itertools
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Any, Iterable

from shared.domain.error import CoreIOError
from shared.domain.interface.path_manager import IAppPathManager
from shared.domain.interface.system import IProjectCoreIOFactory, IProjectCoreIO
from shared.domain.value.identifier import ProjectID
from util.app_logging import create_logger


class ProjectCoreIO(IProjectCoreIO):
    _logger = create_logger()

    def __init__(self, *, project_dir: Path):
        self._project_dir = project_dir

    def _print_log(self, level: Literal["info", "debug"], op_name, **kwargs):
        project_id_part: str = self._project_dir.stem
        kwargs_str = []
        for k, v in kwargs.items():
            kwargs_str.append(f"{k}={v}")

        if level == "info":
            printer = self._logger.info
        elif level == "debug":
            printer = self._logger.debug
        else:
            raise ValueError(f"Invalid level: {level}")

        printer(f"{op_name}[{project_id_part}]({', '.join(kwargs_str)})")

    def __check_file_location(
            self,
            *,
            path: Path,
            external_ok=False,
    ) -> None:
        if not path.is_absolute():
            raise CoreIOError(f"path must be absolute: {path}")
        if not path.is_file():
            raise CoreIOError(f"path must be a file: {path}")
        if not external_ok:
            assert path.is_relative_to(
                self._project_dir
            ), path

    def __check_folder_location(
            self,
            *,
            path: Path,
            external_ok=False,
    ) -> None:
        if not path.is_absolute():
            raise CoreIOError(f"path must be absolute: {path}")
        if not path.is_dir():
            raise CoreIOError(f"path must be a directory: {path}")
        if not external_ok:
            assert path.is_relative_to(
                self._project_dir
            ), path

    def __check_path_may_not_exist(
            self,
            *,
            path: Path,
            external_ok=False,
    ) -> None:
        # 存在しないかもしれないパスを調べるので種類は宣言しない
        if not path.is_absolute():
            raise CoreIOError(f"path must be absolute: {path}")
        if not external_ok:
            if not path.is_relative_to(
                    self._project_dir):
                raise CoreIOError(f"path must be within ProjectEntity: {path}")

    def rmtree_folder(
            self,
            *,
            path: Path,
    ) -> None:
        # プロジェクト内のフォルダを削除する
        self.__check_folder_location(
            path=path,
        )
        self._print_log("info", "rmtree_folder", path=path)
        shutil.rmtree(path)

    def copy_file_into_folder(
            self,
            *,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str = None,
    ) -> None:
        # プロジェクト内のファイルをプロジェクト内のフォルダにコピーする
        self.__check_file_location(
            path=src_file_fullpath,
        )
        self.__check_folder_location(
            path=dst_folder_fullpath,
        )
        self._print_log(
            "debug",
            "copy_file_into_folder",
            src_file_fullpath=src_file_fullpath,
            dst_folder_fullpath=dst_folder_fullpath,
            dst_file_name=dst_file_name,
        )
        if dst_file_name is None:
            dst_file_name = src_file_fullpath.name
        shutil.copy(src_file_fullpath, dst_folder_fullpath / dst_file_name)

    def copy_files_in_folder_into_folder(
            self,
            *,
            src_folder_fullpath: Path,
            dst_folder_fullpath: Path,
    ) -> None:
        # プロジェクト内のフォルダのすべてのファイルをプロジェクト内のフォルダにコピーする
        self.__check_folder_location(
            path=src_folder_fullpath,
        )
        self.__check_folder_location(
            path=dst_folder_fullpath,
        )
        self._print_log(
            "debug",
            "copy_files_in_folder_into_folder",
            src_folder_fullpath=src_folder_fullpath,
            dst_folder_fullpath=dst_folder_fullpath,
        )
        for src_fullpath in src_folder_fullpath.iterdir():
            if src_fullpath.is_file():
                self.copy_file_into_folder(
                    src_file_fullpath=src_fullpath,
                    dst_folder_fullpath=dst_folder_fullpath,
                )
            elif src_fullpath.is_dir():
                self.copy_files_in_folder_into_folder(
                    src_folder_fullpath=src_fullpath,
                    dst_folder_fullpath=dst_folder_fullpath / src_fullpath.name,
                )

    def copy_folder(
            self,
            *,
            src_path: Path,
            dst_path: Path,
    ) -> None:
        # プロジェクト内のフォルダをコピーする
        self.__check_folder_location(
            path=src_path,
        )
        self.__check_folder_location(
            path=dst_path,
        )
        self._print_log(
            "debug",
            "copy_folder",
            src_path=src_path,
            dst_path=dst_path,
        )
        shutil.copytree(src_path, dst_path)

    def copy_external_file_into_folder(
            self,
            *,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str = None,
    ) -> None:
        # 任意のファイルをプロジェクト内のフォルダにコピーする
        self.__check_file_location(
            path=src_file_fullpath,
            external_ok=True,
        )
        self.__check_folder_location(
            path=dst_folder_fullpath,
        )
        self._print_log(
            "debug",
            "copy_external_file_into_folder",
            src_file_fullpath=src_file_fullpath,
            dst_folder_fullpath=dst_folder_fullpath,
            dst_file_name=dst_file_name,
        )
        if dst_file_name is None:
            dst_file_name = src_file_fullpath.name
        shutil.copy(src_file_fullpath, dst_folder_fullpath / dst_file_name)

    def unlink(
            self,
            *,
            path: Path,
    ) -> None:
        # プロジェクト内のファイルを削除する
        self.__check_file_location(
            path=path,
        )
        self._print_log("info", "unlink", path=path)
        path.unlink(missing_ok=False)

    def write_json(
            self,
            *,
            json_fullpath: Path,
            body: Any,
    ):
        # プロジェクト内のパスにjsonを書き込む
        self.__check_path_may_not_exist(
            path=json_fullpath,
        )
        self._print_log("debug", "write_json", json_fullpath=json_fullpath)
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        with json_fullpath.open(mode="w", encoding="utf-8") as f:
            json.dump(
                body,
                f,
                indent=2,
                ensure_ascii=False,
            )

    def read_json(
            self,
            *,
            json_fullpath: Path,
    ) -> Optional:
        # プロジェクト内のパスからjsonを読み出す
        self.__check_file_location(
            path=json_fullpath,
        )
        self._print_log("debug", "read_json", json_fullpath=json_fullpath)
        with json_fullpath.open(mode="r", encoding="utf-8") as f:
            return json.load(f)

    def touch(
            self,
            *,
            file_fullpath: Path,
            content_bytes: bytes = b"",
    ):
        # プロジェクト内のパスにファイルを作る
        self.__check_path_may_not_exist(
            path=file_fullpath,
        )
        self._print_log("debug", "touch", file_fullpath=file_fullpath)
        file_fullpath.parent.mkdir(parents=True, exist_ok=True)
        with file_fullpath.open(mode="wb") as f:
            f.write(content_bytes)

    def read_file_content_str(
            self,
            *,
            file_fullpath: Path,
    ) -> str:
        # プロジェクト内のテキストファイルを読み出す
        self.__check_file_location(
            path=file_fullpath,
        )
        self._print_log(
            "debug", "read_file_content_str", file_fullpath=file_fullpath
        )
        with file_fullpath.open(mode="r", encoding="utf-8") as f:
            return f.read()

    def read_file_content_bytes(
            self,
            *,
            file_fullpath: Path,
    ) -> bytes:
        # プロジェクト内のバイナリファイルを読み出す
        self.__check_file_location(
            path=file_fullpath
        )
        self._print_log(
            "debug",
            "read_file_content_bytes",
            file_fullpath=file_fullpath,
        )
        with file_fullpath.open(mode="rb") as f:
            return f.read()

    def write_file_content_bytes(
            self,
            *,
            file_fullpath: Path,
            content_bytes: bytes,
    ) -> None:
        # プロジェクト内のバイナリファイルを書きこむ
        self.__check_path_may_not_exist(
            path=file_fullpath,
        )
        self._print_log(
            "debug",
            "write_file_content_bytes",
            file_fullpath=file_fullpath,
        )
        assert isinstance(content_bytes, bytes), type(content_bytes)
        with file_fullpath.open(mode="wb") as f:
            f.write(content_bytes)

    def calculate_folder_checksum(
            self,
            *,
            folder_fullpath: Path,
    ) -> int:
        self.__check_folder_location(
            path=folder_fullpath,
        )

        self._print_log(
            "debug",
            "calculate_folder_checksum",
            folder_fullpath=folder_fullpath,
        )

        entries: list[dict] = []
        for root, dirs, files in os.walk(str(folder_fullpath)):
            root = Path(root)
            for name in itertools.chain(dirs, files):
                path = root / name
                stat = path.stat()
                hash_src = dict(
                    path=str(path), mtime=stat.st_mtime, size=stat.st_size)
                entries.append(hash_src)
        entries = sorted(entries, key=lambda item: item["path"])

        sub_hash_entries: list[bytes] = []
        for entry in entries:
            h = hashlib.md5(str(entry).encode("utf-8")).digest()
            sub_hash_entries.append(h)

        hash_src = b"".join(sub_hash_entries)
        return int.from_bytes(hashlib.md5(hash_src).digest(), byteorder="big") % (2 ** 32)

    def walk_files(
            self,
            *,
            folder_fullpath: Path,
            return_absolute: bool,
    ) -> Iterable[Path]:
        self.__check_folder_location(
            path=folder_fullpath,
        )

        # self._print_log("debug", "walk_files", folder_fullpath=folder_fullpath, return_absolute=return_absolute)

        for root, dirs, files in os.walk(str(folder_fullpath)):
            for filename in files:
                file_fullpath = Path(root) / filename
                if return_absolute:
                    yield file_fullpath
                else:
                    yield file_fullpath.relative_to(folder_fullpath)

    def get_file_mtime(
            self,
            *,
            file_fullpath: Path,
    ) -> datetime:
        self.__check_file_location(
            path=file_fullpath,
        )
        # self._print_log("debug", "get_file_mtime", file_fullpath=file_fullpath)
        return datetime.fromtimestamp(file_fullpath.stat().st_mtime)

    def get_folder_size(
            self,
            *,
            folder_fullpath: Path,
    ) -> int:
        self.__check_folder_location(
            path=folder_fullpath,
        )

        self._print_log(
            "debug",
            "get_folder_size",
            folder_fullpath=folder_fullpath,
        )

        total_size = 0
        for file_fullpath in self.walk_files(
                folder_fullpath=folder_fullpath,
                return_absolute=True,
        ):
            total_size += os.path.getsize(file_fullpath)

        return total_size


class ProjectCoreIOFactory(IProjectCoreIOFactory):
    def __init__(self, app_path_manager_factory: IAppPathManager):
        self._app_path_manager_factory = app_path_manager_factory

    def create_project_core_io(self, project_id: ProjectID) -> IProjectCoreIO:
        project_dir \
            = self._app_path_manager_factory.get_project_dir(project_id)
        return ProjectCoreIO(project_dir=project_dir)
