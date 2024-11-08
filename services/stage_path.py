from typing import Iterable

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage, TestStage
from domain.models.values import TestCaseID
from services.stage import StageListRootSubService, StageListChildSubService


class StagePathListSubService:
    # ステージツリーのルートノードからそれぞれの終端ノードに至るまでのパスのリストを取得する

    def __init__(
            self,
            *,
            stage_list_root_sub_service: StageListRootSubService,
            stage_list_child_sub_service: StageListChildSubService,
    ):
        self._stage_list_root_sub_service = stage_list_root_sub_service
        self._stage_list_child_sub_service = stage_list_child_sub_service

    def f(self, stage: AbstractStage, path: tuple[AbstractStage, ...] = None) \
            -> Iterable[list[AbstractStage]]:
        if path is None:
            path = ()
        path = *path, stage
        child_stages = self._stage_list_child_sub_service.execute(stage)
        if child_stages:
            for child_stage in child_stages:
                yield from self.f(child_stage, path)
        else:
            yield list(path)

    def execute(self) -> list[StagePath]:
        # コンテキストが出揃っていない場合，ステージがリストに含まれない場合もある
        # 例えばテストケースがない場合はExecuteStageとTestStageが含まれない
        results = []
        for root_stage in self._stage_list_root_sub_service.execute():
            for path_from_root in self.f(root_stage):
                results.append(StagePath(path_from_root))
        return results


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
