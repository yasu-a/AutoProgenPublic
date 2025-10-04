from domain.model.stage import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from domain.model.value import TestCaseID


class StagePath(tuple[AbstractStage, ...]):  # TODO: flowに改名
    @classmethod
    def list_paths(cls, testcase_ids: list[TestCaseID]) -> "list[StagePath]":
        paths: list[StagePath] = []
        if testcase_ids:
            for testcase_id in testcase_ids:
                paths.append(
                    cls([
                        BuildStage(),
                        CompileStage(),
                        ExecuteStage(testcase_id),
                        TestStage(testcase_id),
                    ])
                )
        else:
            paths.append(
                cls([
                    BuildStage(),
                    CompileStage(),
                ])
            )
        return paths

    # TODO: 修正：より自然にはStagePathがコンテキストとしてtestcase_idを保持しているべき
    @property
    def testcase_id(self) -> TestCaseID:
        for stage in self:
            if isinstance(stage, ExecuteStage):
                return stage.testcase_id
            if isinstance(stage, TestStage):
                return stage.testcase_id
        raise ValueError("No testcase_id found in this stage path")

    def get_stage_by_stage_type(self, stage_type: type[AbstractStage]) -> AbstractStage | None:
        # ステージの型からステージを得る
        for stage in self:
            if isinstance(stage, stage_type):
                return stage
        return None

    @property
    def first_stage(self) -> AbstractStage:
        return self[0]

    def get_next_stage_of(self, stage: AbstractStage) -> AbstractStage | None:
        # None if a given stage is the last stage
        if stage not in self:
            raise ValueError(f"stage {stage} is not in this stage path")
        stage_index = self.index(stage)
        next_index = stage_index + 1
        if next_index >= len(self):
            return None
        return self[next_index]

    def get_previous_stage_of(self, stage: AbstractStage) -> AbstractStage | None:
        # None if a given stage is the last stage
        if stage not in self:
            raise ValueError(f"stage {stage} is not in this stage path")
        stage_index = self.index(stage)
        previous_index = stage_index - 1
        if previous_index < 0:
            return None
        return self[previous_index]

    def __repr__(self):
        return "StagePath(" + ", ".join(map(repr, self)) + ")"
