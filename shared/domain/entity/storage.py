from pathlib import Path

from shared.domain.value.identifier import StorageID
from shared.domain.value.storage_item import StorageFileContentMapper


class StorageEntity:
    def __init__(
            self,
            *,
            storage_id: StorageID,
            base_folder_fullpath: Path,
            files: StorageFileContentMapper,
    ):
        self._storage_id = storage_id  # IDフィールド: immutable
        self.base_folder_fullpath = base_folder_fullpath
        self.files = files

        self._validate()

    def _validate(self):
        if not isinstance(self._storage_id, StorageID):
            raise TypeError(
                f"Expected 'storage_id' to be StorageID, "
                f"got {type(self._storage_id).__name__}: {self._storage_id!r}"
            )
        if not isinstance(self.base_folder_fullpath, Path):
            raise TypeError(
                f"Expected 'base_folder_fullpath' to be Path, "
                f"got {type(self.base_folder_fullpath).__name__}: {self.base_folder_fullpath!r}"
            )
        if not isinstance(self.files, StorageFileContentMapper):
            raise TypeError(
                f"Expected 'files' to be StorageFileContentMapper, "
                f"got {type(self.files).__name__}: {self.files!r}"
            )

    @property
    def storage_id(self) -> StorageID:
        """IDフィールド: Getterのみ（変更不可）"""
        return self._storage_id

    def __eq__(self, other):
        """IDベースの等価性判定"""
        if not isinstance(other, StorageEntity):
            return False
        return self._storage_id == other._storage_id

    def __hash__(self):
        """IDベースのハッシュ"""
        return hash(self._storage_id)

    def to_json(self):
        # StorageEntityのシリアライズは必要に応じて実装
        raise NotImplementedError("StorageEntity serialization not implemented")

    @classmethod
    def from_json(cls, body):
        # StorageEntityのデシリアライズは必要に応じて実装
        raise NotImplementedError("StorageEntity deserialization not implemented")
