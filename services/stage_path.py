from domain.models.stage_path import StagePath
from domain.models.stages import TestStage
from domain.models.values import TestCaseID
from services.testcase_config import TestCaseConfigListIDSubService


class StagePathListSubService:
    # ステージツリーのルートノードからそれぞれの終端ノードに至るまでのパスのリストを取得する

    def __init__(
            self,
            *,
            testcase_config_list_id_sub_service: TestCaseConfigListIDSubService,
    ):
        self._testcase_config_list_id_sub_service = testcase_config_list_id_sub_service

    def execute(self) -> list[StagePath]:
        # コンテキストが出揃っていない場合，ステージがリストに含まれない場合もある
        # 例えばテストケースがない場合はExecuteStageとTestStageが含まれない
        testcase_ids = self._testcase_config_list_id_sub_service.execute()
        return StagePath.list_paths(testcase_ids=testcase_ids)


class StagePathGetByTestCaseIDService:
    # ステージパスのうちから特定のテストケースIDに関連するステージパスを見つける
    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service

    def execute(self, testcase_id: TestCaseID) -> StagePath:
        stage_path_lst: list[StagePath] = self._stage_path_list_sub_service.execute()

        for stage_path in stage_path_lst:
            # ステージパスと関連づいているテストケースIDを取得
            test_stage = stage_path.get_stage_by_stage_type(TestStage)
            if test_stage is None:
                # ステージパスにTestStageがない（テストケースが定義されていない）
                continue
            assert isinstance(test_stage, TestStage)
            stage_path_testcase_id = test_stage.testcase_id

            if stage_path_testcase_id == testcase_id:
                return stage_path

        raise ValueError(f"stage path of {testcase_id=} not found")
