import hashlib
from pathlib import Path

from autoprogen.domain.error import StorageRunCompilerServiceError
from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.source_code_check import SourceCodeCheckCatalog, SourceCodeCheckResult
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student_stage_result import CompileFailureStudentStageResult, CompileStageResultType, \
    CompileSuccessStudentStageResult
from autoprogen.domain.model.value import StorageID, StudentID
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository
from autoprogen.service.dto.storage_run_compiler import StorageCompileServiceResult
from autoprogen.service.storage import StorageCreateService, \
    StorageDeleteService, StorageLoadStudentSourceService, \
    StorageStoreStudentExecutableService
from autoprogen.service.storage_run_compiler import StorageRunCompilerService
from autoprogen.domain.service.source_code_check import SourceCodeCheckDecodeError, SourceCodeCheckService
from autoprogen.domain.service.source_code_check_factory import SourceCodeCheckCatalogFactory
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

    def _create_storage(self) -> StorageID:
        """コンパイル処理に使用する一時ストレージを作成する。"""
        return self._storage_create_service.execute()

    def _load_student_source(self, student_id: StudentID, storage_id: StorageID) -> bytes:
        """学生のソースコードを一時ストレージへ配置して内容を返す。"""
        return self._storage_load_student_source_service.execute(
            student_id=student_id,
            storage_id=storage_id,
            file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
        )

    def _is_skip_security_check_approved(
        self, student_id: StudentID,
        source_code_bytes: bytes,
        project_settings: ProjectSettings,
    ) -> bool:
        """一度取得した設定を用いて学生とソースの検査省略許可を調べる。"""
        source_sha256 = hashlib.sha256(source_code_bytes).hexdigest()
        is_approved = any(
            skip.student_id == student_id and skip.source_sha256 == source_sha256
            for skip in project_settings.source_code_check_skips
        )
        return is_approved

    def _get_check_catalog_suppress_preference_applied(
        self, project_settings: ProjectSettings,
    ) -> SourceCodeCheckCatalog:
        """一度取得した設定から、抑制規則を取り除いたカタログを返す。"""
        catalog = self._source_code_check_catalog_factory.create().filter(
            exclude=(
                (identifier.group_id, identifier.check_id)
                for identifier in project_settings.suppressed_source_code_checks
            ),
        )
        return catalog

    def _run_security_check(
        self,
        source_code_bytes: bytes,
        catalog: SourceCodeCheckCatalog,
    ) -> SourceCodeCheckResult:
        """実際にコンパイルするソースコードを検査する。"""
        return self._source_code_check_service.execute(
            source_code_bytes=source_code_bytes,
            catalog=catalog,
        )

    def _create_security_check_failure_stage_result(
        self,
        student_id: StudentID,
        catalog: SourceCodeCheckCatalog,
        check_result: SourceCodeCheckResult,
    ) -> CompileFailureStudentStageResult:
        """検出された規則を列挙したCOMPILE失敗結果を作成する。"""
        rule_names = {
            (group.group_id, entry.check_id): entry.name
            for group in catalog.groups
            for entry in group.entries
        }
        detail_lines = [
            f"{finding.line_number}行目: "
            f"[{finding.group_id}.{finding.check_id}] "
            f"{rule_names.get((finding.group_id, finding.check_id), '検出した規則')}"
            for finding in check_result.findings[:50]
        ]
        if len(check_result.findings) > 50:
            detail_lines.append(
                f"ほか{len(check_result.findings) - 50}件の検出があります。"
            )
        return CompileFailureStudentStageResult.create_instance(
            student_id=student_id,
            reason=(
                "ソースコードの安全性チェックで問題が検出されたため、"
                "コンパイルを停止しました。\n"
                f"検査対象SHA-256: {check_result.source_sha256}\n"
                + "\n".join(detail_lines)
            ),
            output="",
        )

    def _run_security_check_if_required(
        self,
        student_id: StudentID,
        source_code_bytes: bytes,
    ) -> CompileFailureStudentStageResult | None:
        """許可済みソースを除外して検査し、問題があれば失敗結果を返す。"""
        # 一度取得した設定を許可判定と規則抑制の両方に使用する。
        project_settings = self._project_settings_repository.get()
        if self._is_skip_security_check_approved(student_id, source_code_bytes, project_settings):
            return None

        catalog = self._get_check_catalog_suppress_preference_applied(
            project_settings)
        check_result = self._run_security_check(source_code_bytes, catalog)
        if check_result.is_safe:
            return None

        return self._create_security_check_failure_stage_result(
            student_id,
            catalog,
            check_result,
        )

    def _create_security_check_decode_failure_result(
        self,
        student_id: StudentID,
    ) -> CompileFailureStudentStageResult:
        """UTF-8として検査できない場合のCOMPILE失敗結果を作成する。"""
        return CompileFailureStudentStageResult.create_instance(
            student_id=student_id,
            reason=(
                "ソースコードの安全性チェックに失敗しました。\n"
                "ソースコードをUTF-8として読み込めませんでした。"
            ),
            output="",
        )

    def _run_compile(self, storage_id: StorageID) -> StorageCompileServiceResult:
        """一時ストレージ上のソースコードをコンパイルする。"""
        return self._storage_run_compiler_service.execute(
            storage_id=storage_id,
            source_file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
        )

    def _create_compile_failure_result(
        self,
        student_id: StudentID,
        error: StorageRunCompilerServiceError,
    ) -> CompileFailureStudentStageResult:
        """コンパイラのエラーをCOMPILE失敗結果へ変換する。"""
        return CompileFailureStudentStageResult.create_instance(
            student_id=student_id,
            reason=f"コンパイルに失敗しました。\n{error.reason}",
            output=error.output or "",
        )

    def _store_student_executable(self, student_id: StudentID, storage_id: StorageID) -> None:
        """コンパイル済みの実行ファイルを学生の動的データへ保存する。"""
        self._storage_store_student_executable_service.execute(
            student_id=student_id,
            storage_id=storage_id,
            file_relative_path=self.__EXECUTABLE_FILE_RELATIVE_PATH,
        )

    def _create_compile_success_result(
        self,
        student_id: StudentID,
        service_result: StorageCompileServiceResult,
    ) -> CompileSuccessStudentStageResult:
        """コンパイラの出力を保持したCOMPILE成功結果を作成する。"""
        return CompileSuccessStudentStageResult.create_instance(
            student_id=student_id,
            output=service_result.output,
        )

    def _save_result(self, stage_path: StagePath, result: CompileStageResultType) -> None:
        """COMPILEステージの実行結果を学生データへ保存する。"""
        self._student_put_stage_result_service.execute(
            stage_path=stage_path,
            result=result,
        )

    def _delete_storage(self, storage_id: StorageID) -> None:
        """コンパイル処理に使用した一時ストレージを削除する。"""
        self._storage_delete_service.execute(storage_id)

    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
        """学生一人分のCOMPILEステージを実行して結果を保存する。"""
        # コンパイル専用の一時ストレージを作成する。
        storage_id = self._create_storage()

        try:
            # 学生のソースコードを一時ストレージへ配置する。
            source_code_bytes = self._load_student_source(
                student_id,
                storage_id,
            )

            # 許可状態とプロジェクト設定に従ってソースコードを検査する。
            failure_result = self._run_security_check_if_required(
                student_id,
                source_code_bytes,
            )
            if failure_result is not None:
                # 安全性チェックの失敗結果を保存して処理を終了する。
                self._save_result(stage_path, failure_result)
                return

            # 安全性を確認できたソースコードをコンパイルする。
            service_result = self._run_compile(storage_id)
        except SourceCodeCheckDecodeError:
            # 検査できない文字コードをCOMPILE失敗として記録する。
            result = self._create_security_check_decode_failure_result(
                student_id)
            self._save_result(stage_path, result)
        except StorageRunCompilerServiceError as e:
            # コンパイラのエラーをCOMPILE失敗として記録する。
            result = self._create_compile_failure_result(student_id, e)
            self._save_result(stage_path, result)
        else:
            # 生成された実行ファイルを学生の動的データへ保存する。
            self._store_student_executable(student_id, storage_id)

            # コンパイル成功結果を学生データへ記録する。
            result = self._create_compile_success_result(
                student_id, service_result)
            self._save_result(stage_path, result)
        finally:
            # 成否にかかわらず一時ストレージを削除する。
            self._delete_storage(storage_id)
