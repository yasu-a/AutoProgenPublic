from domain.model.value import StudentID
from service.student_mark import StudentMarkCheckTimestampQueryService
from service.student_stage_path_result import StudentStageResultCheckTimestampQueryService
from usecase.dto.student_stage_result_diff_snapshot import StudentStageResultDiffSnapshot


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
        timestamp_stage_result \
            = self._student_stage_result_check_timestamp_query_service.execute(student_id)

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
