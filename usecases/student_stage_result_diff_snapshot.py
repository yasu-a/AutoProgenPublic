from domain.models.values import StudentID
from services.student_stage_result import StudentStageResultCheckTimestampQueryService
from usecases.dto.student_stage_result_diff_snapshot import StudentStageResultDiffSnapshot


class StudentStageResultTakeDiffSnapshotUseCase:
    def __init__(
            self,
            *,
            student_stage_result_check_timestamp_query_service: StudentStageResultCheckTimestampQueryService,
    ):
        self._student_stage_result_check_timestamp_query_service \
            = student_stage_result_check_timestamp_query_service

    def execute(self, student_id: StudentID) -> StudentStageResultDiffSnapshot:
        timestamp \
            = self._student_stage_result_check_timestamp_query_service.execute(student_id)
        return StudentStageResultDiffSnapshot(
            student_id=student_id,
            timestamp=timestamp,
        )
