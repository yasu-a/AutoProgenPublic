from domain.models.stages import AbstractStage


class StagePath(tuple[AbstractStage, ...]):
    pass
