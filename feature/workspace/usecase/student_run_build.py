from feature.workspace.usecase.interface import IStudentRunBuildStageUseCase
from shared.domain.interface.gateway import (
    IStudentSubmissionGetSourceContentGateway,
    IStudentSubmissionGetChecksumGateway,
    ICurrentDatetimeGateway,
)
from shared.domain.model.stage import StageElement
from shared.domain.model.student_result import BuildStageResultEntity
from shared.domain.service.student_dynamic import StudentDynamicSetSourceContentService, \
    StudentDynamicClearService
from shared.domain.service.student_stage_path_result import StudentPutStagePathResultEntityService
from shared.domain.value.identifier import StudentID
from shared.infra.gateway.student_submission import StudentSubmissionGetSourceFileGatewayError


class StudentRunBuildStageUseCase(IStudentRunBuildStageUseCase):
    # BUILDステージ
    # 提出データフォルダからソースコードを探してきて動的データにエクスポートする

    def __init__(
            self,
            *,
            student_submission_get_source_content_gateway: IStudentSubmissionGetSourceContentGateway,
            student_dynamic_clear_service: StudentDynamicClearService,
            student_dynamic_set_source_content_service: StudentDynamicSetSourceContentService,
            student_submission_get_checksum_gateway: IStudentSubmissionGetChecksumGateway,
            student_put_stage_result_service: StudentPutStagePathResultEntityService,
            current_datetime_gateway: ICurrentDatetimeGateway,
    ):
        self._student_submission_get_source_content_gateway = student_submission_get_source_content_gateway
        self._student_dynamic_clear_service = student_dynamic_clear_service
        self._student_dynamic_set_source_content_service = student_dynamic_set_source_content_service
        self._student_submission_get_checksum_gateway = student_submission_get_checksum_gateway
        self._student_put_stage_result_service = student_put_stage_result_service
        self._current_datetime_gateway = current_datetime_gateway

    def execute(self, student_id: StudentID, stage_path: tuple[StageElement, ...]) -> None:
        # 動的データをクリアする
        self._student_dynamic_clear_service.execute(
            student_id=student_id,
        )

        # ソースコードを探してくる
        try:
            source_content_text = self._student_submission_get_source_content_gateway.execute(
                student_id=student_id,
            )
        except StudentSubmissionGetSourceFileGatewayError as e:
            # 失敗したら異常終了の結果を書きこむ
            self._student_put_stage_result_service.execute(
                result=BuildStageResultEntity(
                    student_id=student_id,
                    submission_folder_checksum=None,
                    timestamp=self._current_datetime_gateway.execute(),
                    is_success=False,
                    error_summary=e.reason,
                )
            )
        else:
            # ソースコードを動的データに配置
            self._student_dynamic_set_source_content_service.execute(
                student_id=student_id,
                source_content_text=source_content_text,
            )

            # 正常終了の結果を書きこんで終了
            submission_folder_checksum = self._student_submission_get_checksum_gateway.execute(
                student_id=student_id,
            )
            self._student_put_stage_result_service.execute(
                result=BuildStageResultEntity(
                    student_id=student_id,
                    submission_folder_checksum=submission_folder_checksum,
                    timestamp=self._current_datetime_gateway.execute(),
                    is_success=True,
                    error_summary=None,
                )
            )
