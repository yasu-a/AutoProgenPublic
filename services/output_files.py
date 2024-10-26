from domain.models.output_file import OutputFileMapping, OutputFile
from domain.models.values import StorageID, FileID
from files.repositories.storage import StorageRepository
from services.dto.storage_diff_snapshot import StorageDiff


class OutputFilesCreateFromStorageDiffService:
    def __init__(
            self,
            *,
            storage_repo: StorageRepository,
    ):
        self._storage_repo = storage_repo

    def execute(
            self,
            *,
            storage_id: StorageID,
            storage_diff: StorageDiff,
    ) -> OutputFileMapping:
        storage = self._storage_repo.get(storage_id)

        output_file_mapping: dict[FileID, OutputFile] = {}
        for created_file_relative_path in storage_diff.created:
            file_id = FileID(created_file_relative_path)
            output_file_mapping[file_id] = OutputFile(
                file_id=file_id,
                content=storage.files[created_file_relative_path]
            )

        return OutputFileMapping(output_file_mapping)
