from domain.models.stages import AbstractStage


class StagePath(tuple[AbstractStage, ...]):
    def get_stage_by_stage_type(self, stage_type: type[AbstractStage]) -> AbstractStage | None:
        # ステージの型からステージを得る
        for stage in self:
            if isinstance(stage, stage_type):
                return stage
        return None
