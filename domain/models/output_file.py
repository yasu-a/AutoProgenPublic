from domain.models.values import FileID
from utils.json_util import bytes_to_jsonable, jsonable_to_bytes


class OutputFile:
    def __init__(
            self,
            *,
            file_id: FileID,
            content: bytes | str,
    ):
        self._file_id = file_id
        if isinstance(content, str):
            self._content = bytes(content, encoding="utf-8")
        else:
            self._content = content

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


class OutputFileMapping(dict[FileID, OutputFile]):
    # TODO: frozendictを導入してこのクラスのインスタンスを持つクラスをすべてdataclass(frozen=True)にする

    def __validate(self):
        # キーとしてのFileIDと値の中のFileIDは一致する
        for file_id, output_file in self.items():
            assert file_id == output_file.file_id, (file_id, output_file)
            # 特殊ファイルは標準出力しかありえない
            if file_id.is_special:
                assert file_id in [FileID.STDOUT], file_id

    def to_json(self) -> dict[str, dict]:
        self.__validate()
        return {
            file_id.to_json(): output_file.to_json()
            for file_id, output_file in self.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        obj = cls({
            FileID.from_json(file_id_str): OutputFile.from_json(output_file_body)
            for file_id_str, output_file_body in body.items()
        })
        obj.__validate()
        return obj