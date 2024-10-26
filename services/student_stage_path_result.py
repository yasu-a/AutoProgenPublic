from collections import OrderedDict

from domain.models.stage_path import StagePath
from domain.models.student_stage_path_result import StudentStagePathResult
from files.repositories.student_stage_result import *
from files.repositories.testcase_config import TestCaseConfigRepository


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


# class StudentProgressListService:
#     # 各プロセスパスの生徒の現時点で終了したところまでのProgressを返す
#
#     def __init__(
#             self,
#             *,
#             student_stage_result_repo: StudentStageResultRepository,
#             stage_list_path_sub_service: StageListPathSubService,
#     ):
#         self._student_stage_result_repo = student_stage_result_repo
#         self._stage_list_path_sub_service = stage_list_path_sub_service
#
#     @transactional_with("student_id")
#     def execute(self, student_id: StudentID) -> dict[StagePath, AbstractStudentStagePathResult]:
#         stage_paths: list[StagePath] = self._stage_list_path_sub_service.execute()
#         progresses: dict[StagePath, AbstractStudentStagePathResult] = {}
#         for i, stage_path in enumerate(stage_paths):
#             consecutive_finish_count = 0
#             last_stage_finished: AbstractStage | None = None
#             for stage in stage_path:
#                 is_stage_finished = self._student_stage_result_repo.exists(
#                     student_id=student_id,
#                     stage=stage,
#                 )
#                 if is_stage_finished:
#                     consecutive_finish_count += 1
#                     last_stage_finished = stage
#                 else:
#                     break
#
#             if last_stage_finished is None:
#                 progresses[stage_path] = StudentStagePathResultUnstarted()
#             else:
#                 progresses[stage_path] = StudentStagePathProgressWithFinishedStage(
#                     stage=last_stage_finished,
#                     result=self._student_stage_result_repo.get(
#                         student_id=student_id,
#                         stage=last_stage_finished,
#                     )
#                 )
#
#         return progresses


class StudentProgressCheckTimestampQueryService:
    # 生徒の進捗データの最終更新日時を取得する

    def __init__(
            self,
            *,
            student_stage_result_path_provider: StudentStageResultPathProvider,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._student_stage_result_path_provider = student_stage_result_path_provider
        self._testcase_config_repo = testcase_config_repo

    def execute(self, student_id: StudentID) -> datetime | None:  # No file exists
        base_folder_fullpath \
            = self._student_stage_result_path_provider.base_folder_fullpath(student_id)
        if not base_folder_fullpath.exists():
            timestamp = None
        else:
            timestamp = base_folder_fullpath.stat().st_mtime
            timestamp = datetime.fromtimestamp(timestamp)
        return timestamp
