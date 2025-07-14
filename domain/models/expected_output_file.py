from domain.models.pattern import PatternList
from domain.models.values import FileID


class ExpectedOutputFile:
    def __init__(
            self,
            *,
            file_id: FileID,
            patterns: PatternList,  # 予期するパターン
    ):
        self._file_id = file_id
        self._patterns = patterns

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

    @classmethod
    def create_default(cls, file_id: FileID) -> "ExpectedOutputFile":
        return cls(
            file_id=file_id,
            patterns=PatternList(),
        )


class ExpectedOutputFileMapping(dict[FileID, ExpectedOutputFile]):
    def __validate_mapping_key_and_item_id(self):
        for file_id, expected_output_file in self.items():
            assert file_id == expected_output_file.file_id, (file_id, expected_output_file)

    def to_json(self) -> dict[str, dict]:
        self.__validate_mapping_key_and_item_id()
        return {
            file_id.to_json(): expected_output_file.to_json()
            for file_id, expected_output_file in self.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        obj = cls({
            FileID.from_json(file_id_str): ExpectedOutputFile.from_json(expected_output_file_body)
            for file_id_str, expected_output_file_body in body.items()
        })
        obj.__validate_mapping_key_and_item_id()
        return obj

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.items(), key=lambda x: x[0])))
