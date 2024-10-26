from domain.models.student_stage_result import BuildSuccessStudentStageResult, \
    BuildFailureStudentStageResult
from domain.models.values import StudentID
from files.repositories.student_stage_result import StudentStageResultRepository
from services.student_dynamic import StudentDynamicSetSourceContentService, \
    StudentDynamicClearService
from services.student_submission import StudentSubmissionGetSourceContentService, \
    StudentSubmissionGetSourceFileServiceError, StudentSubmissionGetChecksumService
from transaction import transactional_with


class StudentRunBuildStageUseCase:
    # BUILDステージ
    # 提出データフォルダからソースコードを探してきて動的データにエクスポートする

    def __init__(
            self,
            *,
            student_submission_get_source_content_service: StudentSubmissionGetSourceContentService,
            student_stage_result_repo: StudentStageResultRepository,
            student_dynamic_clear_service: StudentDynamicClearService,
            student_dynamic_set_source_content_service: StudentDynamicSetSourceContentService,
            student_submission_get_checksum_service: StudentSubmissionGetChecksumService,
    ):
        self._student_submission_get_source_content_service = student_submission_get_source_content_service
        self._student_stage_result_repo = student_stage_result_repo
        self._student_dynamic_clear_service = student_dynamic_clear_service
        self._student_dynamic_set_source_content_service = student_dynamic_set_source_content_service
        self._student_submission_get_checksum_service = student_submission_get_checksum_service

    @transactional_with("student_id")
    def execute(self, student_id: StudentID) -> None:
        # 動的データをクリアする
        self._student_dynamic_clear_service.execute(
            student_id=student_id,
        )

        # ソースコードを探してくる
        try:
            source_content_text = self._student_submission_get_source_content_service.execute(
                student_id=student_id,
            )
        except StudentSubmissionGetSourceFileServiceError as e:
            # 失敗したら異常終了の結果を書きこんで終了
            self._student_stage_result_repo.put(
                result=BuildFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason=e.reason,
                )
            )
            return

        # ソースコードを動的データに配置
        self._student_dynamic_set_source_content_service.execute(
            student_id=student_id,
            source_content_text=source_content_text,
        )

        # 正常終了の結果を書きこんで終了
        submission_folder_checksum = self._student_submission_get_checksum_service.execute(
            student_id=student_id,
        )
        self._student_stage_result_repo.put(
            result=BuildSuccessStudentStageResult.create_instance(
                student_id=student_id,
                submission_folder_checksum=submission_folder_checksum,
            )
        )
