from dataclasses import dataclass
from enum import Enum

from shared.domain.value.identifier import TestCaseID


class Stage(Enum):
    """処理のステージを列挙し、テストケースIDの要求有無を提供する列挙型。"""
    BUILD = "build"
    COMPILE = "compile"
    EXECUTE = "execute"
    TEST = "test"

    def is_testcase_required(self):
        return self in (Stage.EXECUTE, Stage.TEST)

    def to_json(self) -> str:
        """Serialize Stage enum to its value (string) for JSON."""
        return self.value

    @classmethod
    def from_json(cls, value: str) -> "Stage":
        """Deserialize from JSON string to Stage enum."""
        return Stage(value)


@dataclass(frozen=True)
class StageElement:
    """ステージと任意のテストケースIDをひとまとめにする値オブジェクト。"""
    stage: Stage
    testcase_id: TestCaseID | None = None

    def __post_init__(self):
        if self.stage.is_testcase_required():
            if self.testcase_id is None:
                raise ValueError(
                    f"testcase_id is required for stage {self.stage}")
        else:
            if self.testcase_id is not None:
                raise ValueError(
                    f"testcase_id must be None for stage {self.stage}")

    def __repr__(self):
        if self.testcase_id is None:
            return f"{self.stage.name}"
        return f"{self.stage.name}({self.testcase_id})"

    def to_json(self) -> dict:
        return {
            "stage": self.stage.to_json(),
            "testcase_id": self.testcase_id.to_json() if self.testcase_id else None,
        }

    @classmethod
    def from_json(cls, body: dict) -> "StageElement":
        stage = Stage.from_json(body["stage"])
        testcase_id = TestCaseID.from_json(body["testcase_id"]) if body["testcase_id"] is not None else None
        return cls(stage=stage, testcase_id=testcase_id)
