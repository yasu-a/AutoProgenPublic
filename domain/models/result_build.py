from dataclasses import dataclass

from domain.errors import BuildServiceError
from domain.models.result_base import AbstractResult


@dataclass
class BuildResult(AbstractResult):
    submission_folder_hash: int | None

    @classmethod
    def error(cls, e: BuildServiceError) -> "BuildResult":
        return cls(reason=e.reason, submission_folder_hash=None)

    @classmethod
    def success(cls, submission_folder_hash: int) -> "BuildResult":
        return cls(reason=None, submission_folder_hash=submission_folder_hash)

    def to_json(self):
        return dict(
            reason=self.reason,
            submission_folder_hash=self.submission_folder_hash,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            reason=body["reason"],
            submission_folder_hash=body["submission_folder_hash"],
        )

    def has_same_hash(self, h: int) -> bool:
        return self.submission_folder_hash == h
