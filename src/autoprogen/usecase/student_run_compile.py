from pathlib import Path

from autoprogen.domain.error.stage.compile import (
    CompileStageError,
    SourceSafetyViolationError,
)
from autoprogen.domain.model.project_settings import SourceCodeCheckSkip
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student_stage_result import CompileStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.domain.service.source_code_check import SourceCodeCheckService
from autoprogen.domain.service.source_code_check_factory import SourceCodeCheckCatalogFactory
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository
from autoprogen.service.storage import (
    StorageCreateService,
    StorageDeleteService,
    StorageLoadStudentSourceService,
    StorageStoreStudentExecutableService,
)
from autoprogen.service.storage_run_compiler import StorageRunCompilerService
from autoprogen.service.student_stage_path_result import StudentPutStageResultService


class StudentRunCompileStageUseCase:
    """学生のソース検査、コンパイル、成果物保存を順番に実行する。"""

    def __init__(
            self,
            *,
            storage_create_service: StorageCreateService,
            storage_load_student_source_service: StorageLoadStudentSourceService,
            storage_store_student_executable_service: StorageStoreStudentExecutableService,
            source_code_check_catalog_factory: SourceCodeCheckCatalogFactory,
            source_code_check_service: SourceCodeCheckService,
            project_settings_repository: ProjectSettingsRepository,
            storage_run_compiler_service: StorageRunCompilerService,
            storage_delete_service: StorageDeleteService,
            student_put_stage_result_service: StudentPutStageResultService,
    ) -> None:
        """COMPILEステージで使用するサービスとRepositoryを受け取る。"""
        self._storage_create_service = storage_create_service
        self._storage_load_student_source_service = storage_load_student_source_service
        self._storage_store_student_executable_service = storage_store_student_executable_service
        self._source_code_check_catalog_factory = source_code_check_catalog_factory
        self._source_code_check_service = source_code_check_service
        self._project_settings_repository = project_settings_repository
        self._storage_run_compiler_service = storage_run_compiler_service
        self._storage_delete_service = storage_delete_service
        self._student_put_stage_result_service = student_put_stage_result_service

    __SOURCE_FILE_RELATIVE_PATH = Path("main.c")
    __EXECUTABLE_FILE_RELATIVE_PATH = Path("main.exe")

    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
        """学生一人分のCOMPILEステージを実行して結果を保存する。"""
        # 成功・失敗の両方へ記録する安全性設定を一度だけ取得する。
        project_settings = self._project_settings_repository.get()

        # コンパイル処理に使用する一時ストレージを作成する。
        storage_id = self._storage_create_service.execute()
        source_code_check_skipped = False

        try:
            # 実際にコンパイルするソースコードを一時ストレージへ読み込む。
            source_code = self._storage_load_student_source_service.execute(
                student_id=student_id,
                storage_id=storage_id,
                file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
            )

            source_sha256 = source_code.calculate_sha256()
            source_code_check_skip = SourceCodeCheckSkip(
                student_id=student_id,
                source_sha256=source_sha256,
            )
            source_code_check_skipped = (
                source_code_check_skip in project_settings.source_code_check_skips
            )

            # 許可されていないソースコードだけを、有効な規則で検査する。
            if not source_code_check_skipped:
                catalog = self._source_code_check_catalog_factory.create().filter(
                    exclude=(
                        (identifier.group_id, identifier.check_id)
                        for identifier in project_settings.suppressed_source_code_checks
                    ),
                )
                check_result = self._source_code_check_service.execute(
                    source_code=source_code,
                    catalog=catalog,
                )
                if not check_result.is_safe:
                    raise SourceSafetyViolationError(
                        source_sha256=check_result.source_sha256,
                        findings=check_result.findings,
                    )

            # 安全性を確認できたソースコードをコンパイルする。
            compile_result = self._storage_run_compiler_service.execute(
                storage_id=storage_id,
                source_file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
            )
        except CompileStageError as error:
            # 想定されたCOMPILEエラーだけを失敗結果として保存する。
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=CompileStudentStageResult.create_instance(
                    student_id=student_id,
                    error=error,
                    output=error.output or "",
                    suppressed_source_code_checks=(
                        project_settings.suppressed_source_code_checks
                    ),
                    source_code_check_skipped=source_code_check_skipped,
                ),
            )
        else:
            # 正常に生成された実行ファイルを学生の動的データへ保存する。
            self._storage_store_student_executable_service.execute(
                student_id=student_id,
                storage_id=storage_id,
                file_relative_path=self.__EXECUTABLE_FILE_RELATIVE_PATH,
            )

            # コンパイラ出力と実行時の安全性設定を成功結果へ保存する。
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=CompileStudentStageResult.create_instance(
                    student_id=student_id,
                    output=compile_result.output,
                    suppressed_source_code_checks=(
                        project_settings.suppressed_source_code_checks
                    ),
                    source_code_check_skipped=source_code_check_skipped,
                    error=None,
                ),
            )
        finally:
            # 成否にかかわらずコンパイル用の一時ストレージを削除する。
            self._storage_delete_service.execute(storage_id)
