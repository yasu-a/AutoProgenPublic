from domain.models.stages import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from services.testcase_config import TestCaseConfigListIDSubService


class StageListRootSubService:
    # ステージツリーのルートをリストアップする

    def __init__(
            self,
    ):
        pass

    @classmethod
    def execute(cls) -> list[AbstractStage]:
        return [BuildStage()]


class StageListChildSubService:
    # ステージツリーからあるステージの子ステージ（次のステージ）をリストアップする

    def __init__(
            self,
            *,
            testcase_config_list_id_sub_service: TestCaseConfigListIDSubService,
    ):
        self._testcase_config_list_id_sub_service = testcase_config_list_id_sub_service

    def execute(self, stage: AbstractStage) -> list[AbstractStage]:
        # returns None if the stage is the last stage
        if isinstance(stage, BuildStage):
            return [CompileStage()]
        elif isinstance(stage, CompileStage):
            testcase_ids = self._testcase_config_list_id_sub_service.execute()
            return [ExecuteStage(testcase_id) for testcase_id in testcase_ids]
        elif isinstance(stage, ExecuteStage):
            return [TestStage(stage.testcase_id)]
        elif isinstance(stage, TestStage):
            return []
        else:
            raise ValueError(f"Invalid stage: {stage}")


class StageGetParentSubService:
    # ステージツリーからあるステージの親ステージ（前のステージ）を取得する

    def __init__(
            self,
    ):
        pass

    @classmethod
    def execute(cls, stage: AbstractStage) -> AbstractStage | None:
        # returns None if the stage is the first stage
        if isinstance(stage, BuildStage):
            return None
        elif isinstance(stage, CompileStage):
            return BuildStage()
        elif isinstance(stage, ExecuteStage):
            return CompileStage()
        elif isinstance(stage, TestStage):
            return ExecuteStage(stage.testcase_id)
        else:
            raise ValueError(f"Invalid stage: {stage}")
