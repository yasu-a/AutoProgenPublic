from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Literal

from domain.models.values import StorageID


@dataclass(frozen=True)
class StorageFileItem:
    relative_path: Path
    content_bytes: bytes


@dataclass(slots=True)
class _StorageFileItemCacheEntry:
    file_item: StorageFileItem
    is_modified: bool
    is_deleted: bool


@dataclass(frozen=True)
class StorageStat:
    size: int
    mtime: datetime


FileRelativePathListProducerType = Callable[[], list[Path]]  # ^, Path: relative file path
FileContentMapperType = Callable[[Path], bytes | None]  # ^
FileRelativePathExistsMapperType = Callable[[Path], bool]
FileRelativePathStatMapperType = Callable[[Path], StorageStat | None]  # ^


# ^ returns None if file not found


class StorageFileContentMapper:
    # ストレージ内のファイルの読み出しの遅延評価とファイルに対する変更の保持機能を
    # ストレージ内相対パスからStorageFileItemへのマッピングのインターフェースとして提供する

    def __init__(
            self,
            file_relative_path_list_producer: FileRelativePathListProducerType,
            file_content_mapper: FileContentMapperType,
            file_relative_path_exists_mapper: FileRelativePathExistsMapperType,
            file_relative_path_stat_mapper: FileRelativePathStatMapperType,
    ):
        self._file_relative_path_list_producer = file_relative_path_list_producer
        self._file_content_mapper = file_content_mapper
        self._file_relative_path_exists_mapper = file_relative_path_exists_mapper
        self._file_relative_path_stat_mapper = file_relative_path_stat_mapper

        self._cache: dict[Path, _StorageFileItemCacheEntry] = {}
        # ^ None if file is deleted
        # ^ Path: relative file path

    def __contains__(self, relative_file_path: Path) -> bool:
        if relative_file_path in self._cache:
            # キャッシュに存在する
            cache_entry = self._cache[relative_file_path]
            if cache_entry.is_deleted:
                # 削除されている
                return False
            else:
                # キャッシュに存在する
                return True
        else:
            # キャッシュに存在しない
            if not self._file_relative_path_exists_mapper(relative_file_path):
                # ディスク上に存在しない
                return False
            else:
                # ディスク上に存在する
                return True

    def __getitem__(self, relative_file_path: Path) -> bytes | None:
        # ファイルが存在しない場合はNoneを返す
        if relative_file_path in self._cache:
            # キャッシュに存在する
            cache_entry = self._cache[relative_file_path]
            if cache_entry.is_deleted:
                # 削除されている
                return None
            else:
                # キャッシュに存在する
                return cache_entry.file_item.content_bytes
        else:
            # キャッシュに存在しない
            if not self._file_relative_path_exists_mapper(relative_file_path):
                # ディスク上に存在しない
                return None
            else:
                # ディスク上に存在する
                content_bytes = self._file_content_mapper(relative_file_path)
                self._cache[relative_file_path] = _StorageFileItemCacheEntry(
                    file_item=StorageFileItem(
                        relative_path=relative_file_path,
                        content_bytes=content_bytes,
                    ),
                    is_modified=False,
                    is_deleted=False,
                )
                return self._cache[relative_file_path].file_item.content_bytes

    def stat(self, relative_file_path: Path) -> StorageStat | None:
        # 実際にファイルが存在するディスク上（キャッシュをスキップ）のファイルのstatを取得する
        return self._file_relative_path_stat_mapper(relative_file_path)

    def __setitem__(self, file_relative_path: Path, content_bytes: bytes) -> None:
        self._cache[file_relative_path] = _StorageFileItemCacheEntry(
            file_item=StorageFileItem(
                relative_path=file_relative_path,
                content_bytes=content_bytes,
            ),
            is_modified=True,
            is_deleted=False,
        )

    def __delitem__(self, file_item: StorageFileItem) -> None:
        self._cache[file_item.relative_path] = _StorageFileItemCacheEntry(
            file_item=file_item,
            is_modified=True,
            is_deleted=True,
        )

    def iter_modifications(self) \
            -> Iterable[tuple[Path, tuple[Literal["updated", "deleted"], bytes | None]]]:
        # ストレージに対する変更をイテレートする
        for relative_file_path, cache_entry in self._cache.items():
            if not cache_entry.is_modified:
                # 変更がない
                continue
            if cache_entry.is_deleted:
                # 削除された
                yield relative_file_path, ("deleted", None)
            else:
                # 内容が上書きされた
                yield relative_file_path, ("updated", cache_entry.file_item.content_bytes)

    def __iter__(self) -> Iterable[Path]:
        # ストレージ内に存在するファイルの相対パスをイテレートする
        # 削除されたファイルアイテムは返さない

        # キャッシュに存在するファイルのパスを取得
        cache_path_set = set(self._cache)
        for relative_file_path in self._cache:
            if self._cache[relative_file_path].is_deleted:
                # 削除されている
                continue
            yield relative_file_path

        # ディスク上に存在するファイルパスをイテレートする
        for relative_file_path in self._file_relative_path_list_producer():
            if relative_file_path in cache_path_set:
                # すでにイテレートした
                continue
            yield relative_file_path


@dataclass
class Storage:
    storage_id: StorageID
    base_folder_fullpath: Path
    files: StorageFileContentMapper
