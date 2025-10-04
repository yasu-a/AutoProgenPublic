from pathlib import Path

from domain.error import StorageRunCompilerServiceError
from domain.model.stage_path import StagePath
from domain.model.student_stage_result import CompileFailureStudentStageResult, \
    CompileSuccessStudentStageResult
from domain.model.value import StudentID
from service.storage import StorageCreateService, \
    StorageDeleteService, StorageLoadStudentSourceService, StorageStoreStudentExecutableService
from service.storage_run_compiler import StorageRunCompilerService
from service.student_stage_path_result import StudentPutStageResultService


class StudentRunCompileStageUseCase:
    def __init__(
            self,
            *,
            storage_create_service: StorageCreateService,
            storage_load_student_source_service: StorageLoadStudentSourceService,
            storage_store_student_executable_service: StorageStoreStudentExecutableService,
            storage_run_compiler_service: StorageRunCompilerService,
            storage_delete_service: StorageDeleteService,
            student_put_stage_result_service: StudentPutStageResultService,
    ):
        self._storage_create_service = storage_create_service
        self._storage_load_student_source_service = storage_load_student_source_service
        self._storage_store_student_executable_service = storage_store_student_executable_service
        self._storage_run_compiler_service = storage_run_compiler_service
        self._storage_delete_service = storage_delete_service
        self._student_put_stage_result_service = student_put_stage_result_service

    __SOURCE_FILE_RELATIVE_PATH = Path("main.c")
    __EXECUTABLE_FILE_RELATIVE_PATH = Path("main.exe")

    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
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
            # 失敗したら異常終了の結果を書きこむ
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=CompileFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason=f"コンパイルに失敗しました。\n{e.reason}",
                    output=e.output or "",
                )
            )
        else:
            # 実行ファイルを動的データに記録
            self._storage_store_student_executable_service.execute(
                student_id=student_id,
                storage_id=storage_id,
                file_relative_path=self.__EXECUTABLE_FILE_RELATIVE_PATH,
            )

            # 正常終了の結果を書きこむ
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=CompileSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    output=service_result.output,
                )
            )
        finally:
            # ストレージ領域の解放
            self._storage_delete_service.execute(storage_id)
