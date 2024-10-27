from domain.models.values import StorageID
from infra.repositories.storage import StorageRepository
from services.dto.storage_diff_snapshot import StorageDiffSnapshotFileEntry, StorageFileSnapshot


class StorageTakeSnapshotService:
    def __init__(
            self,
            *,
            storage_repo: StorageRepository,
    ):
        self._storage_repo = storage_repo

    def execute(self, storage_id: StorageID) -> StorageFileSnapshot:
        storage = self._storage_repo.get(storage_id)

        snapshot_file_entries: list[StorageDiffSnapshotFileEntry] = []
        for file_relative_path in storage.files:
            snapshot_file_entries.append(
                StorageDiffSnapshotFileEntry(
                    relative_path=file_relative_path,
                    mtime=storage.files.stat(file_relative_path).mtime
                )
            )

        return StorageFileSnapshot(
            file_entries=frozenset(snapshot_file_entries),
        )
