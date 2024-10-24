from typing import Iterable

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage
from services.stage import StageListRootSubService, StageListChildSubService


class StagePathListService:
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
