from shared.domain.interface.service import IStagePathGetByTestCaseIDService, \
    IStagePathListSubService
from shared.domain.model.stage import StageElement, Stage
from shared.domain.value.identifier import TestCaseID
from shared.infra.repository.testcase import TestCaseRepository


class StagePathListSubService(IStagePathListSubService):
    """ステージ階層のすべてのパスを列挙して返すサービス。"""

    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self) -> list[list[StageElement]]:
        # コンテキストが出揃っていない場合，ステージがリストに含まれない場合もある
        # 例えばテストケースがない場合はExecuteStageとTestStageが含まれない
        testcase_ids = [
            testcase_config.testcase_id
            for testcase_config in self._testcase_config_repo.list_all()
        ]
        
        paths: list[list[StageElement]] = []
        if testcase_ids:
            for testcase_id in testcase_ids:
                paths.append([
                    StageElement(Stage.BUILD),
                    StageElement(Stage.COMPILE),
                    StageElement(Stage.EXECUTE, testcase_id),
                    StageElement(Stage.TEST, testcase_id),
                ])
        else:
            paths.append([
                StageElement(Stage.BUILD),
                StageElement(Stage.COMPILE),
            ])
        return paths


class StagePathGetByTestCaseIDService(IStagePathGetByTestCaseIDService):
    """指定したテストケースIDに関連するステージパスを抽出するサービス。"""
    def __init__(
            self,
            *,
            stage_path_list_sub_service: IStagePathListSubService,
    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service

    def execute(self, testcase_id: TestCaseID) -> list[StageElement]:
        stage_path_lst: list[list[StageElement]] = self._stage_path_list_sub_service.execute()

        for stage_path in stage_path_lst:
            # ステージパスと関連づいているテストケースIDを取得
            test_stage = next((s for s in stage_path if s.stage == Stage.TEST), None)
            if test_stage is None:
                # ステージパスにTestStageがない（テストケースが定義されていない）
                continue
            stage_path_testcase_id = test_stage.testcase_id

            if stage_path_testcase_id == testcase_id:
                return stage_path

        raise ValueError(f"stage path of {testcase_id=} not found")
