from abc import ABC, abstractmethod
from dataclasses import dataclass, fields

from domain.models.values import TestCaseID


@dataclass(frozen=True)
class AbstractStage(ABC):  # 生徒のプロセスのステージを表す基底クラス
    def list_context_elements_str(self) -> list[str]:
        # list str(testcase_id) etc.
        return [
            str(getattr(self, f.name))
            for f in fields(self)
        ]

    @classmethod
    @abstractmethod
    def get_name_str(cls) -> str:
        raise NotImplementedError()

    def __repr__(self):
        name = type(self).__name__
        args = ", ".join(
            f"{f.name}={getattr(self, f.name)}"
            for f in fields(self)
        )
        return f"{name}({args})"

    def to_json(self) -> dict:
        return {
            "name": self.get_name_str(),
            **{
                f.name: getattr(self, f.name).to_json()
                for f in fields(self)
            },
        }

    @classmethod
    def from_json(cls, body: dict) -> "AbstractStage":
        for sub_cls in cls.__subclasses__():
            if sub_cls.get_name_str() == body["name"]:
                return sub_cls(
                    **{
                        f.name: f.type.from_json(body[f.name])
                        for f in fields(sub_cls)
                    }
                )
        assert False, body["name"]


@dataclass(frozen=True)
class BuildStage(AbstractStage):
    @classmethod
    def get_name_str(cls) -> str:
        return "build"


@dataclass(frozen=True)
class CompileStage(AbstractStage):
    @classmethod
    def get_name_str(cls) -> str:
        return "compile"


@dataclass(frozen=True)
class ExecuteStage(AbstractStage):
    testcase_id: TestCaseID

    @classmethod
    def get_name_str(cls) -> str:
        return "execute"


@dataclass(frozen=True)
class TestStage(AbstractStage):
    testcase_id: TestCaseID

    @classmethod
    def get_name_str(cls) -> str:
        return "test"
