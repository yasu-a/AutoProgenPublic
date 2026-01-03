from feature.workspace.usecase.interface import IStudentDynamicTakeDiffSnapshotUseCase, StudentStageResultDiffSnapshotDto
from shared.domain.service.student_stage_path_result import \
    StudentStagePathResultEntityCheckTimestampQueryService
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student_mark import StudentMarkEntityRepository


class StudentDynamicTakeDiffSnapshotUseCase(IStudentDynamicTakeDiffSnapshotUseCase):
    def __init__(
            self,
            *,
            student_stage_result_check_timestamp_query_service: StudentStagePathResultEntityCheckTimestampQueryService,
            student_mark_repo: StudentMarkEntityRepository,
    ):
        self._student_stage_result_check_timestamp_query_service \
            = student_stage_result_check_timestamp_query_service
        self._student_mark_repo \
            = student_mark_repo

    def execute(self, student_id: StudentID) -> StudentStageResultDiffSnapshotDto:
        timestamp_stage_result \
            = self._student_stage_result_check_timestamp_query_service.execute(student_id)

        timestamp_mark \
            = self._student_mark_repo.get_timestamp(student_id)

        timestamps = []
        if timestamp_stage_result is not None:
            timestamps.append(timestamp_stage_result)
        if timestamp_mark is not None:
            timestamps.append(timestamp_mark)

        if timestamps:
            latest_timestamp = max(timestamps)
        else:
            latest_timestamp = None

        return StudentStageResultDiffSnapshotDto(
            student_id=student_id,
            timestamp=latest_timestamp,
        )
