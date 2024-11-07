from domain.models.values import FileID
from utils.json_util import bytes_to_jsonable, jsonable_to_bytes


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

    def __hash__(self) -> int:
        return hash((self._file_id, self._content))

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


class InputFileMapping(dict[FileID, InputFile]):
    # TODO: frozendictを導入してこのクラスのインスタンスを持つクラスをすべてdataclass(frozen=True)にする

    def __validate(self):
        for file_id, input_file in self.items():
            # キーとしてのFileIDと値の中のFileIDは一致する
            assert file_id == input_file.file_id, (file_id, input_file)
            # 特殊ファイルは標準入力しかありえない
            if file_id.is_special:
                assert file_id in [FileID.STDIN], file_id

    def to_json(self) -> dict[str, dict]:
        self.__validate()
        return {
            file_id.to_json(): input_file.to_json()
            for file_id, input_file in self.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        obj = cls({
            FileID.from_json(file_id_str): InputFile.from_json(input_file_body)
            for file_id_str, input_file_body in body.items()
        })
        obj.__validate()
        return obj

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.items(), key=lambda x: x[0])))

    @property
    def has_stdin(self) -> bool:
        return FileID.STDIN in self

    @property
    def special_file_count(self) -> int:
        return sum(1 for file_id in self if file_id.is_special)

    @property
    def normal_file_count(self) -> int:
        return sum(1 for file_id in self if not file_id.is_special)
