import uuid
from pathlib import Path

from domain.models.values import StorageID
from files.repositories.storage import StorageRepository
from files.repositories.test_source import TestSourceRepository


class StorageCreateService:
    def __init__(
            self,
            *,
            storage_repo: StorageRepository,
    ):
        self._storage_repo = storage_repo

    def execute(self) -> StorageID:
        storage_id: StorageID = StorageID(uuid.uuid4())
        self._storage_repo.create(storage_id)
        return storage_id


class StorageDeleteService:
    def __init__(
            self,
            *,
            storage_repo: StorageRepository,
    ):
        self._storage_repo = storage_repo

    def execute(self, storage_id: StorageID):
        self._storage_repo.delete(storage_id)


class StorageLoadTestSourceService:
    # ストレージ領域内にテスト用のソースコードを生成する

    def __init__(
            self,
            *,
            test_source_repo: TestSourceRepository,
            storage_repo: StorageRepository,
    ):
        self._test_source_repo = test_source_repo
        self._storage_repo = storage_repo

    def execute(
            self,
            *,
            storage_id: StorageID,
            source_file_relative_path: Path,
    ) -> None:
        # テスト用のソースコードを読み込む
        test_source_content_bytes = self._test_source_repo.get()

        # ストレージ領域に配置する
        storage = self._storage_repo.get(storage_id)
        storage.files[source_file_relative_path] = test_source_content_bytes
        self._storage_repo.put(storage)
