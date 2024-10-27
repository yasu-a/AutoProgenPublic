from collections import OrderedDict

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage
from domain.models.student_stage_path_result import StudentStagePathResult
from domain.models.student_stage_result import AbstractStudentStageResult
from domain.models.values import StudentID
from infra.repositories.student_stage_result import StudentStageResultRepository


class StudentStagePathResultGetService:
    # 生徒の指定されたステージパスの各ステージの結果を取得する

    def __init__(
            self,
            *,
            student_stage_result_repo: StudentStageResultRepository,
    ):
        self._student_stage_result_repo = student_stage_result_repo

    def execute(self, student_id: StudentID, stage_path: StagePath) \
            -> StudentStagePathResult | None:
        stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None] = OrderedDict()
        for stage in stage_path:
            is_finished = self._student_stage_result_repo.exists(
                student_id=student_id,
                stage=stage,
            )
            if not is_finished:
                stage_result = None
            else:
                stage_result = self._student_stage_result_repo.get(
                    student_id=student_id,
                    stage=stage,
                )
            stage_results[stage] = stage_result
        return StudentStagePathResult(
            stage_results=stage_results,
        )
