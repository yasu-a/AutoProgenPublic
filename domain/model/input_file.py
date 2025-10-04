from collections import OrderedDict
from typing import Iterable

from domain.model.value import FileID
from util.json_util import bytes_to_jsonable, jsonable_to_bytes


# immutable
class InputFile:
    def __init__(
            self,
            *,
            file_id: FileID,
            content: bytes | str,
    ):
        self._file_id = file_id
        if isinstance(content, str):
            self._content: bytes = bytes(content, encoding="utf-8")
        else:
            self._content: bytes = content

    def to_json(self) -> dict:
        return dict(
            file_id=self._file_id.to_json(),
            content_bytes=bytes_to_jsonable(self._content),
        )

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            content=jsonable_to_bytes(body["content_bytes"]),
        )

    def __hash__(self):
        return hash((InputFile, self._file_id, self._content))

    def __eq__(self, other):
        if other is None:
            return False
        assert isinstance(other, type(self))
        return self._file_id == other._file_id and self._content == other._content

    @property
    def file_id(self) -> FileID:
        return self._file_id

    @property
    def content_bytes(self) -> bytes:
        return self._content

    @property
    def content_string(self) -> str | None:  # None if encoding unsupported
        try:
            return self._content.decode("utf-8")
        except UnicodeDecodeError:
            return None


class InputFileCollection:
    def __init__(self, it: Iterable[InputFile] = ()):  # デフォルト空
        self._mapping: OrderedDict[FileID, InputFile] = OrderedDict()
        for item in it:
            self.put(item)

    def put(self, item: InputFile) -> None:
        self._mapping[item.file_id] = item

    def find(self, file_id: FileID) -> InputFile:
        return self._mapping[file_id]

    def has(self, file_id: FileID) -> bool:
        return file_id in self._mapping

    @property
    def file_ids(self) -> list[FileID]:
        return list(self._mapping.keys())

    def items(self):
        return self._mapping.items()

    def to_json(self) -> dict:
        return {
            file_id.to_json(): input_file.to_json()
            for file_id, input_file in self._mapping.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            InputFile.from_json(input_file_body)
            for file_id_str, input_file_body in body.items()
        )

    @property
    def has_stdin(self) -> bool:
        return FileID.STDIN in self._mapping

    @property
    def special_file_count(self) -> int:
        return sum(1 for file_id in self._mapping if file_id.is_special)

    @property
    def normal_file_count(self) -> int:
        return sum(1 for file_id in self._mapping if not file_id.is_special)
