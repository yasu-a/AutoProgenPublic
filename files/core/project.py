import hashlib
import itertools
import json
import os
import shutil
from pathlib import Path
from typing import Optional, Any, Iterable

from app_logging import create_logger
from domain.models.values import ProjectID
from files.path_providers.project import ProjectPathProvider


class ProjectCoreIO:
    _logger = create_logger()

    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def __check_file_location(
            self,
            *,
            project_id: ProjectID,
            path: Path,
            external_ok=False,
    ) -> None:
        assert path.is_absolute(), path
        assert path.is_file(), path
        if not external_ok:
            assert path.is_relative_to(
                self._project_path_provider.base_folder_fullpath(project_id)
            ), path

    def __check_folder_location(
            self,
            *,
            project_id: ProjectID,
            path: Path,
            external_ok=False,
    ) -> None:
        assert path.is_absolute(), path
        assert path.is_dir(), path
        if not external_ok:
            assert path.is_relative_to(
                self._project_path_provider.base_folder_fullpath(project_id)
            ), path

    def __check_path_may_not_exist(
            self,
            *,
            project_id: ProjectID,
            path: Path,
            external_ok=False,
    ) -> None:
        # 存在しないかもしれないパスを調べるので種類は宣言しない
        assert path.is_absolute(), path
        if not external_ok:
            assert path.is_relative_to(
                self._project_path_provider.base_folder_fullpath(project_id)
            ), path

    def rmtree_folder(
            self,
            *,
            project_id: ProjectID,
            path: Path,
    ) -> None:
        # プロジェクト内のフォルダを削除する
        self.__check_folder_location(
            project_id=project_id,
            path=path,
        )
        self._logger.info(f"rmtree_folder {path!s}")
        shutil.rmtree(path)

    def copy_file_into_folder(
            self,
            *,
            project_id: ProjectID,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str = None,
    ) -> None:
        # プロジェクト内のファイルをプロジェクト内のフォルダにコピーする
        self.__check_file_location(
            project_id=project_id,
            path=src_file_fullpath,
        )
        self.__check_folder_location(
            project_id=project_id,
            path=dst_folder_fullpath,
        )
        if dst_file_name is None:
            dst_file_name = src_file_fullpath.name
        shutil.copy(src_file_fullpath, dst_folder_fullpath / dst_file_name)

    def copy_files_in_folder_into_folder(
            self,
            *,
            project_id: ProjectID,
            src_folder_fullpath: Path,
            dst_folder_fullpath: Path,
    ) -> None:
        # プロジェクト内のフォルダのすべてのファイルをプロジェクト内のフォルダにコピーする
        self.__check_folder_location(
            project_id=project_id,
            path=src_folder_fullpath,
        )
        self.__check_folder_location(
            project_id=project_id,
            path=dst_folder_fullpath,
        )
        for src_fullpath in dst_folder_fullpath.iterdir():
            if src_fullpath.is_file():
                self.copy_file_into_folder(
                    project_id=project_id,
                    src_file_fullpath=src_fullpath,
                    dst_folder_fullpath=dst_folder_fullpath,
                )
            elif src_fullpath.is_dir():
                self.copy_files_in_folder_into_folder(
                    project_id=project_id,
                    src_folder_fullpath=src_fullpath,
                    dst_folder_fullpath=dst_folder_fullpath / src_fullpath.name,
                )

    def copy_folder(
            self,
            *,
            project_id: ProjectID,
            src_path: Path,
            dst_path: Path,
    ) -> None:
        # プロジェクト内のフォルダをコピーする
        self.__check_folder_location(
            project_id=project_id,
            path=src_path,
        )
        self.__check_folder_location(
            project_id=project_id,
            path=dst_path,
        )
        shutil.copytree(src_path, dst_path)

    def copy_external_file_into_folder(
            self,
            *,
            project_id: ProjectID,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str = None,
    ) -> None:
        # 任意のファイルをプロジェクト内のフォルダにコピーする
        self.__check_file_location(
            project_id=project_id,
            path=src_file_fullpath,
            external_ok=True,
        )
        self.__check_folder_location(
            project_id=project_id,
            path=dst_folder_fullpath,
        )
        if dst_file_name is None:
            dst_file_name = src_file_fullpath.name
        shutil.copy(src_file_fullpath, dst_folder_fullpath / dst_file_name)

    def unlink(
            self,
            *,
            project_id: ProjectID,
            path: Path,
    ) -> None:
        # プロジェクト内のファイルを削除する
        self.__check_file_location(
            project_id=project_id,
            path=path,
        )
        self._logger.info(f"unlink {path!s}")
        path.unlink(missing_ok=False)

    def write_json(
            self,
            *,
            project_id: ProjectID,
            json_fullpath: Path,
            body: Any,
    ):
        # プロジェクト内のパスにjsonを書き込む
        self.__check_path_may_not_exist(
            project_id=project_id,
            path=json_fullpath,
        )
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
            project_id: ProjectID,
            json_fullpath: Path,
    ) -> Optional:
        # プロジェクト内のパスからjsonを読み出す
        self.__check_file_location(
            project_id=project_id,
            path=json_fullpath,
        )
        with json_fullpath.open(mode="r", encoding="utf-8") as f:
            return json.load(f)

    def touch(
            self,
            *,
            project_id: ProjectID,
            file_fullpath: Path,
            content_bytes: bytes = b"",
    ):
        # プロジェクト内のパスにファイルを作る
        self.__check_path_may_not_exist(
            project_id=project_id,
            path=file_fullpath,
        )
        file_fullpath.parent.mkdir(parents=True, exist_ok=True)
        with file_fullpath.open(mode="wb") as f:
            f.write(content_bytes)

    def read_file_content_str(
            self,
            *,
            project_id: ProjectID,
            file_fullpath: Path,
    ) -> str:
        # プロジェクト内のテキストファイルを読み出す
        self.__check_file_location(
            project_id=project_id,
            path=file_fullpath,
        )
        with file_fullpath.open(mode="r", encoding="utf-8") as f:
            return f.read()

    def read_file_content_bytes(
            self,
            *,
            project_id: ProjectID,
            file_fullpath: Path,
    ) -> bytes:
        # プロジェクト内のバイナリファイルを読み出す
        self.__check_file_location(
            project_id=project_id,
            path=file_fullpath
        )
        with file_fullpath.open(mode="rb") as f:
            return f.read()

    def write_file_content_bytes(
            self,
            *,
            project_id: ProjectID,
            file_fullpath: Path,
            content_bytes: bytes,
    ) -> None:
        # プロジェクト内のバイナリファイルを書きこむ
        self.__check_path_may_not_exist(
            project_id=project_id,
            path=file_fullpath,
        )
        assert isinstance(content_bytes, bytes), type(content_bytes)
        with file_fullpath.open(mode="wb") as f:
            f.write(content_bytes)

    def calculate_folder_hash(
            self,
            *,
            project_id: ProjectID,
            folder_fullpath: Path,
    ) -> int:
        self.__check_folder_location(
            project_id=project_id,
            path=folder_fullpath,
        )

        entries: list[dict] = []
        for root, dirs, files in os.walk(str(folder_fullpath)):
            root = Path(root)
            for name in itertools.chain(dirs, files):
                path = root / name
                stat = path.stat()
                hash_src = dict(path=str(path), mtime=stat.st_mtime, size=stat.st_size)
                entries.append(hash_src)
        entries = sorted(entries, key=lambda item: item["path"])

        sub_hash_entries: list[bytes] = []
        for entry in entries:
            h = hashlib.md5(str(entry).encode("utf-8")).digest()
            sub_hash_entries.append(h)

        hash_src = b"".join(sub_hash_entries)
        return int.from_bytes(hashlib.md5(hash_src).digest(), byteorder="big")

    def walk_files(
            self,
            *,
            project_id: ProjectID,
            folder_fullpath: Path,
            return_absolute: bool,
    ) -> Iterable[Path]:
        self.__check_folder_location(
            project_id=project_id,
            path=folder_fullpath,
        )

        for root, dirs, files in os.walk(str(folder_fullpath)):
            for filename in files:
                file_fullpath = Path(root) / filename
                if return_absolute:
                    yield file_fullpath
                else:
                    yield file_fullpath.relative_to(folder_fullpath)
