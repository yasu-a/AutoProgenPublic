from pathlib import Path

from domain.error import StorageRunCompilerServiceError
from service.storage import StorageCreateService, StorageLoadTestSourceService, \
    StorageDeleteService
from service.storage_run_compiler import StorageRunCompilerService
from usecase.dto.test_compile_stage import TestCompileStageResult


class TestCompileStageUseCase:
    def __init__(
            self,
            *,
            storage_create_service: StorageCreateService,
            storage_load_test_source_service: StorageLoadTestSourceService,
            storage_run_compiler_service: StorageRunCompilerService,
            storage_delete_service: StorageDeleteService,
    ):
        self._storage_create_service = storage_create_service
        self._storage_load_test_source_service = storage_load_test_source_service
        self._storage_run_compiler_service = storage_run_compiler_service
        self._storage_delete_service = storage_delete_service

    __SOURCE_FILE_RELATIVE_PATH = Path("main.c")

    def execute(self, compiler_tool_fullpath: Path = None) -> TestCompileStageResult:
        # ストレージ領域の生成
        storage_id = self._storage_create_service.execute()

        # ストレージ領域にテスト用のソースコードをロード
        self._storage_load_test_source_service.execute(
            storage_id=storage_id,
            file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
        )

        # コンパイルの実行と結果の生成
        try:
            service_result = self._storage_run_compiler_service.execute(
                storage_id=storage_id,
                source_file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
                compiler_tool_fullpath=compiler_tool_fullpath,
            )
        except StorageRunCompilerServiceError as e:
            result = TestCompileStageResult(
                is_success=False,
                output=(
                    f"コンパイルテストに失敗しました\n"
                    f"\n"
                    f"{e.reason}\n"
                    f"\n"
                    f"＜出力＞\n"
                    f"{e.output}"
                ),
            )
        else:
            result = TestCompileStageResult(
                is_success=True,
                output=(
                    f"コンパイルテストに成功しました。\n"
                    f"\n"
                    f"＜出力＞\n"
                    f"{service_result.output}"
                ),
            )

        # ストレージ領域の解放
        self._storage_delete_service.execute(storage_id)

        return result
