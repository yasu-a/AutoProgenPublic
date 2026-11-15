from pathlib import Path

from autoprogen.domain.error.stage.execute import (
    ExecutableNotFoundError,
    ExecutionTimeoutError,
)
from autoprogen.domain.model.value import StorageID, FileID
from autoprogen.infra.io.executable import ExecutableIOTimeoutError, ExecutableIO
from autoprogen.infra.repository.storage import StorageRepository
from autoprogen.service.dto.storage_run_executable import StorageExecuteServiceResult


class StorageRunExecutableService:
    """一時ストレージ内の学生プログラムを実行する。"""

    def __init__(
            self,
            *,
            storage_repo: StorageRepository,
            executable_io: ExecutableIO,
    ) -> None:
        """ストレージRepositoryと実行IOを受け取る。"""
        self._storage_repo = storage_repo
        self._executable_io = executable_io

    def execute(
            self,
            *,
            storage_id: StorageID,
            executable_file_relative_path: Path,
            timeout: float,
    ) -> StorageExecuteServiceResult:
        """対象プログラムを実行し、標準出力または構造化エラーを返す。"""
        # 実行対象の検証
        storage = self._storage_repo.get(storage_id)
        if executable_file_relative_path not in storage.files:
            raise ExecutableNotFoundError()

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
            raise ExecutionTimeoutError()

        return StorageExecuteServiceResult(
            stdout_text=stdout_text,
        )
