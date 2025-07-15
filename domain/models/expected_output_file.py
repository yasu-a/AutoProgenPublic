from collections import OrderedDict
from typing import Iterable

from domain.models.pattern import PatternList
from domain.models.values import FileID


# immutable
class ExpectedOutputFile:
    def __init__(
            self,
            *,
            file_id: FileID,
            patterns: PatternList,  # 予期するパターン
    ):
        self._file_id = file_id
        self._patterns = patterns

    @classmethod
    def create_default(cls, file_id: FileID) -> "ExpectedOutputFile":
        return cls(
            file_id=file_id,
            patterns=PatternList(),
        )

    def to_json(self) -> dict:
        return dict(
            file_id=self._file_id.to_json(),
            patterns=self._patterns.to_json(),
        )

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            patterns=PatternList.from_json(body["patterns"]),
        )

    def __hash__(self) -> int:
        return hash((self._file_id, self._patterns))

    def __eq__(self, other):
        if other is None:
            return False
        assert isinstance(other, type(self))
        return self._file_id == other._file_id and self._patterns == other._patterns

    @property
    def file_id(self) -> FileID:
        return self._file_id

    @property
    def patterns(self) -> PatternList:
        return self._patterns


class ExpectedOutputFileCollection:
    def __init__(self, it: Iterable[ExpectedOutputFile] = ()):
        self._mapping: OrderedDict[FileID, ExpectedOutputFile] = OrderedDict()
        for item in it:
            self.put(item)

    def put(self, item: ExpectedOutputFile) -> None:
        self._mapping[item.file_id] = item

    def find(self, file_id: FileID) -> ExpectedOutputFile:
        return self._mapping[file_id]

    def has(self, file_id: FileID) -> bool:
        return file_id in self._mapping

    @property
    def file_ids(self) -> list[FileID]:
        return list(self._mapping.keys())

    def items(self):
        return self._mapping.items()

    def to_json(self) -> dict:
        # {file_id_str: expected_output_file_json, ...}
        return {
            file_id.to_json(): expected_output_file.to_json()
            for file_id, expected_output_file in self._mapping.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        # body: {file_id_str: expected_output_file_json, ...}
        return cls(
            ExpectedOutputFile.from_json(expected_output_file_body)
            for file_id_str, expected_output_file_body in body.items()
        )
