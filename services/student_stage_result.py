from datetime import datetime

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage
from domain.models.values import StudentID
from infra.repositories.student_stage_result import StudentStageResultRepository
from services.stage_path import StagePathListSubService


class StudentStageResultCheckTimestampQueryService:
    # 生徒の進捗データの最終更新日時を取得する

    def __init__(
            self,
            *,
            student_stage_result_repo: StudentStageResultRepository,
    ):
        self._student_stage_result_repo = student_stage_result_repo

    def execute(self, student_id: StudentID) -> datetime | None:  # None if no file exists
        return self._student_stage_result_repo.get_timestamp(student_id)


class StudentStageResultRollbackService:
    # 与えられたステージ以降（与えられたステージ自身を含む）の結果生成をなかったことにする

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
    ) -> None:
        for stage in reversed(stage_path):
            if self._student_stage_result_repo.exists(student_id, stage):
                self._student_stage_result_repo.delete(student_id, stage)
            if isinstance(stage, stage_type):
                break


class StudentStageResultClearService:
    # 生徒の結果データを全削除する

    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_result_repo: StudentStageResultRepository,
    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_result_repo = student_stage_result_repo

    def execute(
            self,
            *,
            student_id: StudentID,
    ) -> None:
        stage_paths = self._stage_path_list_sub_service.execute()
        for stage_path in stage_paths:
            for stage in reversed(stage_path):
                if self._student_stage_result_repo.exists(student_id, stage):
                    self._student_stage_result_repo.delete(student_id, stage)
