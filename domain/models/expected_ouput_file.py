from domain.models.expected_token import ExpectedTokenList
from domain.models.values import FileID


class ExpectedOutputFile:
    def __init__(
            self,
            *,
            file_id: FileID,
            expected_tokens: ExpectedTokenList,
    ):
        self._file_id = file_id
        self._expected_tokens = expected_tokens

    def to_json(self) -> dict:
        return dict(
            file_id=self._file_id.to_json(),
            expected_tokens=self._expected_tokens.to_json(),
        )

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            expected_tokens=ExpectedTokenList.from_json(body["expected_tokens"]),
        )

    def __hash__(self) -> int:
        return hash((self._file_id, self._expected_tokens))

    @property
    def file_id(self) -> FileID:
        return self._file_id

    @property
    def expected_tokens(self) -> ExpectedTokenList:
        return self._expected_tokens

    @classmethod
    def create_default(cls, file_id: FileID) -> "ExpectedOutputFile":
        return cls(
            file_id=file_id,
            expected_tokens=ExpectedTokenList(),
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
