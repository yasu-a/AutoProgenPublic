from pathlib import Path

from domain.errors import StorageRunExecutableServiceError
from domain.models.values import StorageID, FileID
from infra.io.executable import ExecutableIOTimeoutError, ExecutableIO
from infra.repositories.storage import StorageRepository
from services.dto.storage_run_executable import StorageExecuteServiceResult


class StorageRunExecutableService:
    def __init__(
            self,
            *,
            storage_repo: StorageRepository,
            executable_io: ExecutableIO,
    ):
        self._storage_repo = storage_repo
        self._executable_io = executable_io

    def execute(
            self,
            *,
            storage_id: StorageID,
            executable_file_relative_path: Path,
            timeout: float,
    ) -> StorageExecuteServiceResult:
        # 実行対象の検証
        storage = self._storage_repo.get(storage_id)
        if executable_file_relative_path not in storage.files:
            raise StorageRunExecutableServiceError(
                reason="実行対象が存在しません",
            )

        # 実行のための引数の生成
        kwargs = dict(
            # 実行ファイルのパス
            executable_fullpath=storage.base_folder_fullpath / executable_file_relative_path,
            # タイムアウト
            timeout=timeout,
        )
        # 標準入力にリダイレクトするファイルのパス
        input_file_fullpath = storage.base_folder_fullpath / FileID.STDIN.deployment_relative_path
        if not input_file_fullpath.exists():
            input_file_fullpath = None

        # 実行ファイルの実行
        try:
            stdout_text = self._executable_io.run(
                **kwargs,
                input_file_fullpath=input_file_fullpath,
            )
        except ExecutableIOTimeoutError:
            raise StorageRunExecutableServiceError(
                reason="実行がタイムアウトしました\n"
                       "この環境のスペックに対して並列タスク数が多すぎる・プログラムが入力を待っている・無限ループしているなどの可能性があります",
            )

        return StorageExecuteServiceResult(
            stdout_text=stdout_text,
        )
