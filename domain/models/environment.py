import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class EnvEntryLabel(Enum):
    EXTERNAL = 1
    SOURCE_MAIN = 2


@dataclass(slots=True)
class StudentEnvEntry:
    path: str  # relative path from environment
    label: EnvEntryLabel
    updated_at: datetime

    def to_json(self):
        return dict(
            path=self.path,
            label=self.label.value,
            updated_at=self.updated_at.timestamp(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            path=body["path"],
            label=EnvEntryLabel(body["label"]),
            updated_at=datetime.fromtimestamp(body["updated_at"]),
        )

    @property
    def filename_except_ext(self):
        _, filename = os.path.split(self.path)
        filename_except_ext, _ = os.path.splitext(filename)
        return filename_except_ext

    def extract_number_from_filename(self) -> int | None:
        numbers = re.findall(r"\d+", self.filename_except_ext)
        if len(numbers) == 0:
            return None
        return int(numbers[0])


@dataclass(slots=True)
class StudentEnvImportResult:
    source_item_path: str | None  # item relative path in archive
    env_item_path: str | None  # item relative path in environment
    success: bool
    reason: str | None

    def to_json(self):
        return asdict(self)

    @classmethod
    def from_json(cls, body):
        return cls(
            source_item_path=body["source_item_path"],
            env_item_path=body["env_item_path"],
            success=body["success"],
            reason=body["reason"],
        )


@dataclass(slots=True)
class StudentEnvMeta:
    path: str
    entries: dict[str, StudentEnvEntry]  # path -> StudentEnvEntryInfo
    import_results: dict[str, StudentEnvImportResult]  # source_item_name -> StudentEnvImportResult

    def to_json(self):
        return dict(
            path=self.path,
            entries={k: v.to_json() for k, v in self.entries.items()},
            import_results={k: v.to_json() for k, v in self.import_results.items()},
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            path=body["path"],
            entries={k: StudentEnvEntry.from_json(v)
                     for k, v in body["entries"].items()},
            import_results={k: StudentEnvImportResult.from_json(v)
                            for k, v in body["import_results"].items()},
        )

    @property
    def success(self):
        return all(import_result.success for import_result in self.import_results.values())

    def get_env_entry_by_label_and_number(self, label: EnvEntryLabel, number: int) \
            -> StudentEnvEntry | None:
        for entry in self.entries.values():
            if entry.label != label:
                continue
            if entry.extract_number_from_filename() != number:
                continue
            return entry
        return None
