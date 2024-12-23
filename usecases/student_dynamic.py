from domain.errors import StudentServiceError, StudentUseCaseError
from domain.models.values import StudentID
from services.student_mark import StudentMarkCheckTimestampQueryService
from services.student_stage_result import StudentStageResultCheckTimestampQueryService
from usecases.dto.student_stage_result_diff_snapshot import StudentStageResultDiffSnapshot


class StudentDynamicTakeDiffSnapshotUseCase:
    def __init__(
            self,
            *,
            student_stage_result_check_timestamp_query_service: StudentStageResultCheckTimestampQueryService,
            student_mark_check_timestamp_query_service: StudentMarkCheckTimestampQueryService,
    ):
        self._student_stage_result_check_timestamp_query_service \
            = student_stage_result_check_timestamp_query_service
        self._student_mark_check_timestamp_query_service \
            = student_mark_check_timestamp_query_service

    def execute(self, student_id: StudentID) -> StudentStageResultDiffSnapshot:
        # TODO: StudentStageResultCheckTimestampQueryServiceのFIXMEを暫定的に解消するためのtry-exceptロジック
        try:
            timestamp_stage_result \
                = self._student_stage_result_check_timestamp_query_service.execute(student_id)
        except StudentServiceError:
            raise StudentUseCaseError(f"failed to get timestamp of stage result {student_id}")

        timestamp_mark \
            = self._student_mark_check_timestamp_query_service.execute(student_id)

        timestamps = []
        if timestamp_stage_result is not None:
            timestamps.append(timestamp_stage_result)
        if timestamp_mark is not None:
            timestamps.append(timestamp_mark)

        if timestamps:
            latest_timestamp = max(timestamps)
        else:
            latest_timestamp = None

        return StudentStageResultDiffSnapshot(
            student_id=student_id,
            timestamp=latest_timestamp,
        )
