import uuid
from pathlib import Path

from domain.model.file_item import ExecutableFileItem
from domain.model.input_file import InputFileCollection
from domain.model.output_file import OutputFileCollection, OutputFile
from domain.model.value import StorageID, StudentID, TestCaseID, FileID
from infra.repository.storage import StorageRepository
from infra.repository.student_dynamic import StudentSourceRepository, \
    StudentExecutableRepository
from infra.repository.test_source import TestSourceRepository
from infra.repository.testcase_config import TestCaseConfigRepository
from service.dto.storage_diff_snapshot import StorageDiff, StorageFileSnapshot, \
    StorageDiffSnapshotFileEntry


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
            file_relative_path: Path,
    ) -> None:
        # テスト用のソースコードを読み込む
        content_bytes = self._test_source_repo.get()

        # ストレージ領域に配置する
        storage = self._storage_repo.get(storage_id)
        storage.files[file_relative_path] = content_bytes
        self._storage_repo.put(storage)


class StorageLoadStudentSourceService:
    # ストレージ領域内に生徒のソースコードを生成する

    def __init__(
            self,
            *,
            student_source_repo: StudentSourceRepository,
            storage_repo: StorageRepository,
    ):
        self._student_source_repo = student_source_repo
        self._storage_repo = storage_repo

    def execute(
            self,
            *,
            student_id: StudentID,
            storage_id: StorageID,
            file_relative_path: Path,
    ) -> None:
        # 生徒のソースコードを読み込む
        content_bytes = self._student_source_repo.get(student_id).content_bytes

        # ストレージ領域に配置する
        storage = self._storage_repo.get(storage_id)
        storage.files[file_relative_path] = content_bytes
        self._storage_repo.put(storage)


class StorageLoadStudentExecutableService:
    # ストレージ領域内に生徒の実行ファイルを生成する

    def __init__(
            self,
            *,
            student_executable_repo: StudentExecutableRepository,
            storage_repo: StorageRepository,
    ):
        self._student_executable_repo = student_executable_repo
        self._storage_repo = storage_repo

    def execute(
            self,
            *,
            student_id: StudentID,
            storage_id: StorageID,
            file_relative_path: Path,
    ) -> None:
        # 生徒の実行ファイルを読み込む
        content_bytes = self._student_executable_repo.get(student_id).content_bytes

        # ストレージ領域に配置する
        storage = self._storage_repo.get(storage_id)
        storage.files[file_relative_path] = content_bytes
        self._storage_repo.put(storage)


class StorageStoreStudentExecutableService:
    # ストレージ領域の生徒の実行ファイルを動的フォルダにコピーする

    def __init__(
            self,
            *,
            student_executable_repo: StudentExecutableRepository,
            storage_repo: StorageRepository,
    ):
        self._student_executable_repo = student_executable_repo
        self._storage_repo = storage_repo

    def execute(
            self,
            *,
            student_id: StudentID,
            storage_id: StorageID,
            file_relative_path: Path,
    ) -> None:
        storage = self._storage_repo.get(storage_id)
        if file_relative_path not in storage.files:
            raise FileNotFoundError(
                f"指定された実行ファイルが見つかりません。: {file_relative_path}")
        content_bytes = storage.files[file_relative_path]
        self._student_executable_repo.put(
            student_id=student_id,
            file_item=ExecutableFileItem(
                content_bytes=content_bytes,
            )
        )


class StorageLoadExecuteConfigInputFilesService:
    # ストレージ領域にテストケース実行構成の入力ファイルを生成する

    def __init__(
            self,
            *,
            storage_repo: StorageRepository,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._storage_repo = storage_repo
        self._testcase_config_repo = testcase_config_repo

    def execute(self, *, storage_id: StorageID, testcase_id: TestCaseID) -> None:
        # ストレージ領域を取得
        storage = self._storage_repo.get(storage_id)

        # テストケースの実行構成から入力ファイルを取得
        input_file_collection: InputFileCollection \
            = self._testcase_config_repo.get(testcase_id).execute_config.input_file_collection

        # ストレージ領域に各入力ファイルを配置
        for file_id, input_file in input_file_collection.items():
            storage.files[file_id.deployment_relative_path] = input_file.content_bytes

        # ストレージ領域をコミット
        self._storage_repo.put(storage)


class StorageWriteStdoutFileService:
    # ストレージ領域に標準出力ファイルを書き込む

    def __init__(
            self,
            *,
            storage_repo: StorageRepository,
    ):
        self._storage_repo = storage_repo

    def execute(self, *, storage_id: StorageID, stdout_text: str) -> None:
        # ストレージ領域を取得
        storage = self._storage_repo.get(storage_id)

        # 生徒の標準出力ファイルを生成
        file_relative_path = FileID.STDOUT.deployment_relative_path
        storage.files[file_relative_path] = stdout_text.encode("utf-8")

        # ストレージ領域をコミット
        self._storage_repo.put(storage)


class StorageCreateOutputFileCollectionFromDiffService:
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
    ) -> OutputFileCollection:
        storage = self._storage_repo.get(storage_id)

        output_file_collection = OutputFileCollection()
        for file_relative_path in storage_diff.created:
            if file_relative_path == FileID.STDOUT.deployment_relative_path:
                file_id = FileID.STDOUT
            elif file_relative_path == FileID.STDIN.deployment_relative_path:
                file_id = FileID.STDIN
            else:
                file_id = FileID(file_relative_path)
            output_file_collection.put(
                OutputFile(
                    file_id=file_id,
                    content=storage.files[file_relative_path]
                )
            )

        return output_file_collection


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
