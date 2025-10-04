from domain.model.stage_path import StagePath
from domain.model.student_stage_result import BuildSuccessStudentStageResult, \
    BuildFailureStudentStageResult
from domain.model.value import StudentID
from service.student_dynamic import StudentDynamicSetSourceContentService, \
    StudentDynamicClearService
from service.student_stage_path_result import StudentPutStageResultService
from service.student_submission import StudentSubmissionGetSourceContentService, \
    StudentSubmissionGetSourceFileServiceError, StudentSubmissionGetChecksumService


class StudentRunBuildStageUseCase:
    # BUILDステージ
    # 提出データフォルダからソースコードを探してきて動的データにエクスポートする

    def __init__(
            self,
            *,
            student_submission_get_source_content_service: StudentSubmissionGetSourceContentService,
            student_dynamic_clear_service: StudentDynamicClearService,
            student_dynamic_set_source_content_service: StudentDynamicSetSourceContentService,
            student_submission_get_checksum_service: StudentSubmissionGetChecksumService,
            student_put_stage_result_service: StudentPutStageResultService,
    ):
        self._student_submission_get_source_content_service = student_submission_get_source_content_service
        self._student_dynamic_clear_service = student_dynamic_clear_service
        self._student_dynamic_set_source_content_service = student_dynamic_set_source_content_service
        self._student_submission_get_checksum_service = student_submission_get_checksum_service
        self._student_put_stage_result_service = student_put_stage_result_service

    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
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
            # 失敗したら異常終了の結果を書きこむ
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=BuildFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason=e.reason,
                )
            )
        else:
            # ソースコードを動的データに配置
            self._student_dynamic_set_source_content_service.execute(
                student_id=student_id,
                source_content_text=source_content_text,
            )

            # 正常終了の結果を書きこんで終了
            submission_folder_checksum = self._student_submission_get_checksum_service.execute(
                student_id=student_id,
            )
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=BuildSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    submission_folder_checksum=submission_folder_checksum,
                )
            )
