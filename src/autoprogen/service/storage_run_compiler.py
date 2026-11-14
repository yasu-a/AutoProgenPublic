from pathlib import Path

from autoprogen.domain.error import StorageRunCompilerServiceError, CompileToolIOError
from autoprogen.domain.error.stage.compile import (
    CompilerNotConfiguredError,
    CompileSourceNotFoundError,
)
from autoprogen.domain.model.value import StorageID
from autoprogen.infra.io.compile_tool import CompileToolIO
from autoprogen.infra.repository.global_settings import GlobalSettingsRepository
from autoprogen.infra.repository.storage import StorageRepository
from autoprogen.service.dto.storage_run_compiler import StorageCompileServiceResult


class StorageRunCompilerService:
    """一時ストレージ内のソースコードをコンパイルする。"""

    def __init__(
            self,
            *,
            compile_tool_io: CompileToolIO,
            global_settings_repo: GlobalSettingsRepository,
            storage_repo: StorageRepository,
    ) -> None:
        """コンパイラIO、設定、ストレージRepositoryを受け取る。"""
        self._compile_tool_io = compile_tool_io
        self._global_settings_repo = global_settings_repo
        self._storage_repo = storage_repo

    def execute(
            self,
            *,
            storage_id: StorageID,
            source_file_relative_path: Path,
            compiler_tool_fullpath: Path | None = None,
    ) -> StorageCompileServiceResult:
        """対象ソースをコンパイルし、出力または構造化エラーを返す。"""
        # コンパイラのパスを取得する
        if compiler_tool_fullpath is None:
            compiler_tool_fullpath = self._global_settings_repo.get().compiler_tool_fullpath
        if compiler_tool_fullpath is None:
            raise StorageRunCompilerServiceError(
                error=CompilerNotConfiguredError(),
                output=None,
            )

        # コンパイル対象の検証
        storage = self._storage_repo.get(storage_id)
        if source_file_relative_path not in storage.files:
            raise StorageRunCompilerServiceError(
                error=CompileSourceNotFoundError(),
                output=None,
            )

        # コンパイルのための引数の生成
        source_file_fullpath = storage.base_folder_fullpath / source_file_relative_path
        kwargs = dict(
            # コンパイラのパス
            compiler_tool_fullpath=compiler_tool_fullpath,
            # コンパイルのタイムアウト
            timeout=self._global_settings_repo.get().compile_timeout,
            # コンパイル時のカレントディレクトリ
            cwd_fullpath=source_file_fullpath.parent,
            # ソースコードの相対パス
            target_relative_path=source_file_fullpath.relative_to(
                source_file_fullpath.parent),
        )

        # コンパイルの実行
        try:
            output = self._compile_tool_io.run_and_get_output(**kwargs)
        except CompileToolIOError as e:
            raise StorageRunCompilerServiceError(
                error=e.error,
                output=e.output,
            )

        return StorageCompileServiceResult(
            output=output
        )
