from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AbstractResult(ABC):  # ステージ化された結果の基底クラス TODO: rename to AbstractStageResult???
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
