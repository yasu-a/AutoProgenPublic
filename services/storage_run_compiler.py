from pathlib import Path

from domain.errors import StorageRunCompilerServiceError, CompileToolIOError
from domain.models.values import StorageID
from files.external.compile_tool import CompileToolIO
from files.repositories.global_config import GlobalConfigRepository
from files.repositories.storage import StorageRepository
from files.repositories.student_dynamic import StudentDynamicRepository
from services.dto.storage_run_compiler import StorageCompileServiceResult


class StorageRunCompilerService:
    # ストレージ領域内でコンパイルを行う
    def __init__(
            self,
            *,
            compile_tool_io: CompileToolIO,
            global_config_repo: GlobalConfigRepository,
            student_dynamic_repo: StudentDynamicRepository,
            storage_repo: StorageRepository,
    ):
        self._compile_tool_io = compile_tool_io
        self._global_config_repo = global_config_repo
        self._student_dynamic_repo = student_dynamic_repo
        self._storage_repo = storage_repo

    def execute(
            self,
            *,
            storage_id: StorageID,
            source_file_relative_path: Path,
            compiler_tool_fullpath: Path = None,
    ) -> StorageCompileServiceResult:
        # コンパイラのパスを取得する
        if compiler_tool_fullpath is None:
            compiler_tool_fullpath = self._global_config_repo.get().compiler_tool_fullpath
        if compiler_tool_fullpath is None:
            raise StorageRunCompilerServiceError(
                reason="コンパイラが設定されていません",
                output=None,
            )

        # コンパイル対象の検証
        storage = self._storage_repo.get(storage_id)
        if source_file_relative_path not in storage.files:
            raise StorageRunCompilerServiceError(
                reason="コンパイル対象が存在しません",
                output=None,
            )

        # コンパイルのための引数の生成
        source_file_fullpath = storage.base_folder_fullpath / source_file_relative_path
        kwargs = dict(
            # コンパイラのパス
            compiler_tool_fullpath=compiler_tool_fullpath,
            # コンパイルのタイムアウト
            timeout=self._global_config_repo.get().compile_timeout,
            # コンパイル時のカレントディレクトリ
            cwd_fullpath=source_file_fullpath.parent,
            # ソースコードの相対パス
            target_relative_path=source_file_fullpath.relative_to(source_file_fullpath.parent),
        )

        # コンパイルの実行
        try:
            output = self._compile_tool_io.run_and_get_output(**kwargs)
        except CompileToolIOError as e:
            raise StorageRunCompilerServiceError(
                reason=f"コンパイルに失敗しました。\n{e.reason}",
                output=e.output,
            )

        return StorageCompileServiceResult(
            output=output
        )
