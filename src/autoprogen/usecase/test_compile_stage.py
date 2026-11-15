from pathlib import Path

from autoprogen.domain.error.stage.compile import CompileStageError
from autoprogen.service.stage_error_text import StageErrorTextFormatter
from autoprogen.service.storage import StorageCreateService, StorageLoadTestSourceService, \
    StorageDeleteService
from autoprogen.service.storage_run_compiler import StorageRunCompilerService
from autoprogen.usecase.dto.test_compile_stage import TestCompileStageResult


class TestCompileStageUseCase:
    """設定されたコンパイラをテスト用ソースコードで動作確認する。"""

    def __init__(
            self,
            *,
            storage_create_service: StorageCreateService,
            storage_load_test_source_service: StorageLoadTestSourceService,
            storage_run_compiler_service: StorageRunCompilerService,
            storage_delete_service: StorageDeleteService,
            stage_error_text_formatter: StageErrorTextFormatter,
    ) -> None:
        """コンパイラ動作確認に必要なServiceを受け取る。"""
        self._storage_create_service = storage_create_service
        self._storage_load_test_source_service = storage_load_test_source_service
        self._storage_run_compiler_service = storage_run_compiler_service
        self._storage_delete_service = storage_delete_service
        self._stage_error_text_formatter = stage_error_text_formatter

    __SOURCE_FILE_RELATIVE_PATH = Path("main.c")

    def execute(self, compiler_tool_fullpath: Path | None = None) -> TestCompileStageResult:
        """コンパイラを実行し、画面表示用の確認結果を返す。"""
        # コンパイラ動作確認に使用する一時ストレージを作成する。
        storage_id = self._storage_create_service.execute()

        try:
            # 一時ストレージへテスト用ソースコードを読み込む。
            self._storage_load_test_source_service.execute(
                storage_id=storage_id,
                file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
            )

            # 指定されたコンパイラでテスト用ソースコードをコンパイルする。
            service_result = self._storage_run_compiler_service.execute(
                storage_id=storage_id,
                source_file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
                compiler_tool_fullpath=compiler_tool_fullpath,
            )
        except CompileStageError as error:
            # 既存の表示変換と生出力を組み合わせて失敗内容を返す。
            result = TestCompileStageResult(
                is_success=False,
                output=(
                    f"コンパイルテストに失敗しました\n"
                    f"\n"
                    f"{self._stage_error_text_formatter.format_summary(error)}\n"
                    f"\n"
                    f"＜出力＞\n"
                    f"{error.output or ''}"
                ),
            )
        else:
            # 成功時はコンパイラの生出力をそのまま画面へ返す。
            result = TestCompileStageResult(
                is_success=True,
                output=(
                    f"コンパイルテストに成功しました。\n"
                    f"\n"
                    f"＜出力＞\n"
                    f"{service_result.output}"
                ),
            )
        finally:
            # 成否にかかわらず動作確認用の一時ストレージを削除する。
            self._storage_delete_service.execute(storage_id)

        return result
