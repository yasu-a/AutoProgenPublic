from abc import ABC, abstractmethod
from dataclasses import dataclass, fields

from domain.model.value import TestCaseID


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
    def get_name(cls) -> str:
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
            "name": self.get_name(),
            **{
                f.name: getattr(self, f.name).to_json()
                for f in fields(self)
            },
        }

    @classmethod
    def from_json(cls, body: dict) -> "AbstractStage":
        for sub_cls in cls.__subclasses__():
            if sub_cls.get_name() == body["name"]:
                # noinspection PyArgumentList
                return sub_cls(
                    **{
                        f.name: f.type.from_json(body[f.name])
                        for f in fields(sub_cls)
                    }
                )
        assert False, body["name"]


@dataclass(frozen=True)
class BuildStage(AbstractStage):
    # ソースコード抽出

    @classmethod
    def get_name(cls) -> str:
        return "build"


@dataclass(frozen=True)
class CompileStage(AbstractStage):
    # コンパイル

    @classmethod
    def get_name(cls) -> str:
        return "compile"


@dataclass(frozen=True)
class ExecuteStage(AbstractStage):
    # 実行

    testcase_id: TestCaseID

    @classmethod
    def get_name(cls) -> str:
        return "execute"


@dataclass(frozen=True)
class TestStage(AbstractStage):
    # テスト

    testcase_id: TestCaseID

    @classmethod
    def get_name(cls) -> str:
        return "test"
