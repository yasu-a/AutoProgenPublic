from abc import ABC, abstractmethod
from dataclasses import dataclass

from models.errors import BuildServiceError, CompileServiceError


@dataclass
class AbstractResult(ABC):
    reason: str | None

    def is_success(self) -> bool:
        return self.reason is None

    @property
    def detailed_reason(self) -> str | None:
        return self.reason

    @abstractmethod
    def to_json(self):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_json(cls, body):
        raise NotImplementedError()


@dataclass
class BuildResult(AbstractResult):
    @classmethod
    def error(cls, e: BuildServiceError) -> "BuildResult":
        return cls(reason=e.reason)

    @classmethod
    def success(cls) -> "BuildResult":
        return cls(reason=None)

    def to_json(self):
        return dict(
            reason=self.reason,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            reason=body["reason"],
        )


@dataclass
class CompileResult(AbstractResult):
    output: str | None

    @property
    def detailed_reason(self) -> str | None:
        if self.reason is None:
            return None
        return f"{self.reason}\n{self.output}"

    @classmethod
    def error(cls, e: CompileServiceError) -> "CompileResult":
        return cls(reason=e.reason, output=e.output)

    @classmethod
    def success(cls, output: str) -> "CompileResult":
        return cls(reason=None, output=output)

    def to_json(self):
        return dict(
            reason=self.reason,
            output=self.output,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            reason=body["reason"],
            output=body["output"],
        )
