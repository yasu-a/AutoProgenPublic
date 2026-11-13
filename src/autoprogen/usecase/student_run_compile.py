import hashlib
from pathlib import Path

from autoprogen.domain.error import StorageRunCompilerServiceError
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student_stage_result import CompileFailureStudentStageResult, \
    CompileSuccessStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository
from autoprogen.service.storage import StorageCreateService, \
    StorageDeleteService, StorageLoadStudentSourceService, \
    StorageStoreStudentExecutableService
from autoprogen.service.storage_run_compiler import StorageRunCompilerService
from autoprogen.service.source_code_check import SourceCodeCheckDecodeError, SourceCodeCheckService
from autoprogen.service.source_code_check_factory import SourceCodeCheckCatalogFactory
from autoprogen.service.student_stage_path_result import StudentPutStageResultService


class StudentRunCompileStageUseCase:
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
    ):
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
        # ストレージ領域の生成
        storage_id = self._storage_create_service.execute()

        # ストレージ領域に生徒のソースコードをロード
        source_code_bytes = self._storage_load_student_source_service.execute(
            student_id=student_id,
            storage_id=storage_id,
            file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
        )

        try:
            # 同じ学生・同じソースコードを採点者が許可していた場合のみ検査を省略する。
            project_settings = self._project_settings_repository.get()
            source_sha256 = hashlib.sha256(source_code_bytes).hexdigest()
            is_approved = any(
                skip.student_id == student_id and skip.source_sha256 == source_sha256
                for skip in project_settings.source_code_check_skips
            )
            if not is_approved:
                # プロジェクトで抑制されている規則は検査対象から外す。
                catalog = self._source_code_check_catalog_factory.create().filter(
                    exclude=(
                        (identifier.group_id, identifier.check_id)
                        for identifier in project_settings.suppressed_source_code_checks
                    ),
                )

                # 実際にコンパイルされるソースと同じバイト列を検査する。
                check_result = self._source_code_check_service.execute(
                    source_code_bytes=source_code_bytes,
                    catalog=catalog,
                )
                if check_result.findings:
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
                    self._student_put_stage_result_service.execute(
                        stage_path=stage_path,
                        result=CompileFailureStudentStageResult.create_instance(
                            student_id=student_id,
                            reason=(
                                "ソースコードの安全性チェックで問題が検出されたため、"
                                "コンパイルを停止しました。\n"
                                + "\n".join(detail_lines)
                            ),
                            output="",
                        ),
                    )
                    return

            # コンパイルの実行と結果の生成
            service_result = self._storage_run_compiler_service.execute(
                storage_id=storage_id,
                source_file_relative_path=self.__SOURCE_FILE_RELATIVE_PATH,
            )
        except SourceCodeCheckDecodeError:
            # UTF-8として解析できないソースはコンパイルせず、ステージ失敗にする。
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=CompileFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason=(
                        "ソースコードの安全性チェックに失敗しました。\n"
                        "ソースコードをUTF-8として読み込めませんでした。"
                    ),
                    output="",
                ),
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
