from domain.models.stages import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.values import TestCaseID


class StagePath(tuple[AbstractStage, ...]):
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

    def get_stage_by_stage_type(self, stage_type: type[AbstractStage]) -> AbstractStage | None:
        # ステージの型からステージを得る
        for stage in self:
            if isinstance(stage, stage_type):
                return stage
        return None

    def __repr__(self):
        return "StagePath(" + ", ".join(map(repr, self)) + ")"
