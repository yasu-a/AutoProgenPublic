from dataclasses import dataclass

from domain.errors import CompileServiceError
from domain.models.result_base import AbstractResult


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
