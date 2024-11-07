from datetime import datetime

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage
from domain.models.values import StudentID
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.path_providers.current_project import StudentStageResultPathProvider
from infra.repositories.student_stage_result import StudentStageResultRepository
from infra.repositories.testcase_config import TestCaseConfigRepository
from services.stage_path import StagePathListSubService


class StudentStageResultCheckTimestampQueryService:
    # 生徒の進捗データの最終更新日時を取得する

    def __init__(
            self,
            *,
            student_stage_result_path_provider: StudentStageResultPathProvider,
            testcase_config_repo: TestCaseConfigRepository,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_stage_result_path_provider = student_stage_result_path_provider
        self._testcase_config_repo = testcase_config_repo
        self._current_project_core_io = current_project_core_io

    def execute(self, student_id: StudentID) -> datetime | None:  # None if no file exists
        base_folder_fullpath \
            = self._student_stage_result_path_provider.base_folder_fullpath(student_id)
        if not base_folder_fullpath.exists():
            return None

        latest_timestamp: datetime | None = None
        for file_fullpath in self._current_project_core_io.walk_files(
                folder_fullpath=base_folder_fullpath,
                return_absolute=True,
        ):
            # FIXME: transaction導入 ループ中にファイルが消されるとエラー
            timestamp = self._current_project_core_io.get_file_mtime(
                file_fullpath=file_fullpath,
            )
            if latest_timestamp is None or latest_timestamp < timestamp:
                latest_timestamp = timestamp

        return latest_timestamp


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
