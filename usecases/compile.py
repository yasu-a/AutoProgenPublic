from pathlib import Path

from domain.errors import StorageRunCompilerServiceError
from domain.models.student_stage_result import CompileFailureStudentStageResult, \
    CompileSuccessStudentStageResult
from domain.models.values import StudentID
from files.repositories.student_stage_result import StudentStageResultRepository
from services.storage import StorageLoadTestSourceService, StorageCreateService, \
    StorageDeleteService, StorageLoadStudentSourceService, StorageStoreStudentExecutableService
from services.storage_run_compiler import StorageRunCompilerService
from usecases.dto.compile_test import CompileTestResult


class CompileTestUseCase:
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

    def execute(self, compiler_tool_fullpath: Path = None) -> CompileTestResult:
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
            result = CompileTestResult(
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
            result = CompileTestResult(
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


class StudentRunCompileStageUseCase:
    def __init__(
            self,
            *,
            storage_create_service: StorageCreateService,
            storage_load_student_source_service: StorageLoadStudentSourceService,
            storage_store_student_executable_service: StorageStoreStudentExecutableService,
            storage_run_compiler_service: StorageRunCompilerService,
            storage_delete_service: StorageDeleteService,
            student_stage_result_repo: StudentStageResultRepository,
    ):
        self._storage_create_service = storage_create_service
        self._storage_load_student_source_service = storage_load_student_source_service
        self._storage_store_student_executable_service = storage_store_student_executable_service
        self._storage_run_compiler_service = storage_run_compiler_service
        self._storage_delete_service = storage_delete_service
        self._student_stage_result_repo = student_stage_result_repo

    __SOURCE_FILE_RELATIVE_PATH = Path("main.c")
    __EXECUTABLE_FILE_RELATIVE_PATH = Path("main.exe")

    def execute(self, student_id: StudentID) -> None:
        # ストレージ領域の生成
        storage_id = self._storage_create_service.execute()

        # ストレージ領域に生徒のソースコードをロード
        self._storage_load_student_source_service.execute(
            student_id=student_id,
            storage_id=storage_id,
            file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
        )

        # コンパイルの実行と結果の生成
        try:
            service_result = self._storage_run_compiler_service.execute(
                storage_id=storage_id,
                source_file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
            )
        except StorageRunCompilerServiceError as e:
            # 失敗したら異常終了の結果を書きこんで終了
            self._student_stage_result_repo.put(
                result=CompileFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason=f"コンパイルに失敗しました。\n{e.reason}",
                    output=e.output,
                )
            )
            return

        # 実行ファイルを動的データに記録
        self._storage_store_student_executable_service.execute(
            student_id=student_id,
            storage_id=storage_id,
            file_relative_path=self.__EXECUTABLE_FILE_RELATIVE_PATH,
        )

        # ストレージ領域の解放
        self._storage_delete_service.execute(storage_id)

        # 正常終了の結果を書きこんで終了
        self._student_stage_result_repo.put(
            result=CompileSuccessStudentStageResult.create_instance(
                student_id=student_id,
                output=service_result.output,
            )
        )
