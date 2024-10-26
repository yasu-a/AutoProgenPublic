from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage
from domain.models.values import StudentID
from files.repositories.student_stage_result import StudentStageResultRepository


class StudentStageRollbackService:
    def __init__(
            self,
            *,
            student_stage_result_repo: StudentStageResultRepository,
    ):
        self._student_stage_result_repo = student_stage_result_repo

    def execute(
            self,
            *,
            student_id: StudentID,
            stage_path: StagePath,
            stage_type: type[AbstractStage],
    ):
        # stageを含むstage以降の結果生成をなかったことにする
        for stage in reversed(stage_path):
            if self._student_stage_result_repo.exists(student_id, stage):
                self._student_stage_result_repo.delete(student_id, stage)
            if isinstance(stage, stage_type):
                break
