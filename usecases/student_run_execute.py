from pathlib import Path

from domain.errors import StorageRunExecutableServiceError
from domain.models.student_stage_result import ExecuteFailureStudentStageResult, \
    ExecuteSuccessStudentStageResult
from domain.models.values import StudentID, TestCaseID
from infra.repositories.student_stage_result import StudentStageResultRepository
from services.dto.storage_diff_snapshot import StorageDiff
from services.storage import StorageCreateService, StorageDeleteService, \
    StorageLoadStudentExecutableService, StorageLoadExecuteConfigInputFilesService, \
    StorageWriteStdoutFileService, StorageCreateOutputFileMappingFromDiffService, \
    StorageTakeSnapshotService
from services.storage_run_executable import StorageRunExecutableService
from services.testcase_config import TestCaseConfigGetExecuteConfigMtimeService, \
    TestCaseConfigGetExecuteOptionsService


class StudentRunExecuteStageUseCase:
    def __init__(
            self,
            *,
            storage_create_service: StorageCreateService,
            storage_load_student_executable_service: StorageLoadStudentExecutableService,
            storage_load_execute_config_input_files_service: StorageLoadExecuteConfigInputFilesService,
            storage_take_snapshot_service: StorageTakeSnapshotService,
            storage_delete_service: StorageDeleteService,
            student_stage_result_repo: StudentStageResultRepository,
            testcase_config_get_execute_config_mtime_service: TestCaseConfigGetExecuteConfigMtimeService,
            storage_run_executable_service: StorageRunExecutableService,
            testcase_config_get_execute_options_service: TestCaseConfigGetExecuteOptionsService,
            storage_create_output_file_mapping_from_diff_service: StorageCreateOutputFileMappingFromDiffService,
            storage_write_stdout_file_service: StorageWriteStdoutFileService,
    ):
        self._storage_create_service \
            = storage_create_service
        self._storage_load_student_executable_service \
            = storage_load_student_executable_service
        self._storage_load_execute_config_input_files_service \
            = storage_load_execute_config_input_files_service
        self._storage_take_snapshot_service \
            = storage_take_snapshot_service
        self._storage_delete_service \
            = storage_delete_service
        self._student_stage_result_repo \
            = student_stage_result_repo
        self._testcase_config_get_execute_config_mtime_service \
            = testcase_config_get_execute_config_mtime_service
        self._storage_run_executable_service \
            = storage_run_executable_service
        self._testcase_config_get_execute_options_service \
            = testcase_config_get_execute_options_service
        self._storage_create_output_file_mapping_from_diff_service \
            = storage_create_output_file_mapping_from_diff_service
        self._storage_write_stdout_file_service \
            = storage_write_stdout_file_service

    __EXECUTABLE_FILE_RELATIVE_PATH = Path("main.exe")

    def execute(self, student_id: StudentID, testcase_id: TestCaseID) -> None:
        # ストレージ領域の生成
        storage_id = self._storage_create_service.execute()

        # ストレージ領域に生徒の実行ファイルをロード
        self._storage_load_student_executable_service.execute(
            storage_id=storage_id,
            student_id=student_id,
            file_relative_path=self.__EXECUTABLE_FILE_RELATIVE_PATH,
        )

        # ストレージ領域の構成のスナップショットをとる
        storage_snapshot_before_run = self._storage_take_snapshot_service.execute(
            storage_id=storage_id,
        )

        # ストレージ領域に実行構成をロード
        self._storage_load_execute_config_input_files_service.execute(
            storage_id=storage_id,
            testcase_id=testcase_id,
        )

        # 実行オプションを取得
        execute_options = self._testcase_config_get_execute_options_service.execute(
            testcase_id=testcase_id,
        )

        # 実行
        try:
            service_result = self._storage_run_executable_service.execute(
                storage_id=storage_id,
                executable_file_relative_path=self.__EXECUTABLE_FILE_RELATIVE_PATH,
                timeout=execute_options.timeout,
            )
        except StorageRunExecutableServiceError as e:
            # 失敗したら異常終了の結果を書きこむ
            self._student_stage_result_repo.put(
                result=ExecuteFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    reason=e.reason,
                )
            )
            return
        else:
            # 標準出力を書きこむ
            self._storage_write_stdout_file_service.execute(
                storage_id=storage_id,
                stdout_text=service_result.stdout_text,
            )

            # ストレージ領域の構成のスナップショットをとる
            storage_snapshot_after_run = self._storage_take_snapshot_service.execute(
                storage_id=storage_id,
            )

            # スナップショットから差分を生成して出力ファイルを特定
            storage_diff = StorageDiff.from_snapshots(
                old_snapshot=storage_snapshot_before_run,
                new_snapshot=storage_snapshot_after_run,
            )
            output_files = self._storage_create_output_file_mapping_from_diff_service.execute(
                storage_id=storage_id,
                storage_diff=storage_diff,
            )

            # 正常終了の結果を書きこむ
            execute_config_mtime = self._testcase_config_get_execute_config_mtime_service.execute(
                testcase_id=testcase_id,
            )
            self._student_stage_result_repo.put(
                result=ExecuteSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    execute_config_mtime=execute_config_mtime,
                    output_files=output_files,
                )
            )
        finally:
            # ストレージ領域を解放
            # FIXME: プロセスの実行に失敗するとmain.exeの削除にPermissionErrorが出る
            # 　　　　StorageRepositoryのdelete中にリトライの仕組みを追加して対応中
            self._storage_delete_service.execute(
                storage_id=storage_id,
            )
