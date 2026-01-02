from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class StorageDiffSnapshotFileEntry:
    relative_path: Path
    mtime: datetime

    def __hash__(self):
        return hash(self.relative_path)

    def __eq__(self, other):
        if not isinstance(other, StorageDiffSnapshotFileEntry):
            return False
        return self.relative_path == other.relative_path


@dataclass(frozen=True)
class StorageFileSnapshot:
    file_entries: frozenset[StorageDiffSnapshotFileEntry]

    def file_entries_not_in(self, other: "StorageFileSnapshot") \
            -> frozenset[StorageDiffSnapshotFileEntry]:
        return self.file_entries - other.file_entries

    def file_entries_in(self, other: "StorageFileSnapshot") \
            -> frozenset[StorageDiffSnapshotFileEntry]:
        return self.file_entries & other.file_entries

    @classmethod
    def get_created_file_entries(
            cls,
            *,
            old_snapshot: "StorageFileSnapshot",
            new_snapshot: "StorageFileSnapshot",
    ) -> frozenset[StorageDiffSnapshotFileEntry]:
        return new_snapshot.file_entries_not_in(old_snapshot)

    @classmethod
    def get_deleted_file_entries(
            cls,
            *,
            old_snapshot: "StorageFileSnapshot",
            new_snapshot: "StorageFileSnapshot",
    ) -> frozenset[StorageDiffSnapshotFileEntry]:
        return old_snapshot.file_entries_not_in(new_snapshot)

    @classmethod
    def get_updated_file_entries(
            cls,
            *,
            old_snapshot: "StorageFileSnapshot",
            new_snapshot: "StorageFileSnapshot",
    ) -> frozenset[tuple[StorageDiffSnapshotFileEntry, StorageDiffSnapshotFileEntry]]:
        updated_file_entries = []
        for old_file_entry in old_snapshot.file_entries:
            for new_file_entry in new_snapshot.file_entries:
                if old_file_entry != new_file_entry:
                    continue
                if old_file_entry.mtime != new_file_entry.mtime:
                    continue
                updated_file_entries.append((old_file_entry, new_file_entry))
        return frozenset(updated_file_entries)


@dataclass
class StorageDiff:
    created: frozenset[Path]  # Path: file relative path
    updated: frozenset[Path]
    deleted: frozenset[Path]

    @classmethod
    def from_snapshots(
            cls,
            *,
            old_snapshot: StorageFileSnapshot,
            new_snapshot: StorageFileSnapshot,
    ) -> "StorageDiff":
        created = frozenset(
            entry.relative_path
            for entry in StorageFileSnapshot.get_created_file_entries(
                old_snapshot=old_snapshot,
                new_snapshot=new_snapshot
            )
        )
        updated = frozenset(
            entry[0].relative_path
            for entry in StorageFileSnapshot.get_updated_file_entries(
                old_snapshot=old_snapshot,
                new_snapshot=new_snapshot
            )
        )
        deleted = frozenset(
            entry.relative_path
            for entry in StorageFileSnapshot.get_deleted_file_entries(
                old_snapshot=old_snapshot,
                new_snapshot=new_snapshot
            )
        )
        return cls(created=created, updated=updated, deleted=deleted)
