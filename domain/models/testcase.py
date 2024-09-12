from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.models.values import FileID
from utils.json_util import jsonable_to_bytes, bytes_to_jsonable


# ExecuteConfig

# noinspection DuplicatedCode
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


# noinspection DuplicatedCode
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


@dataclass(frozen=True)
class ExecuteConfigOptions:
    timeout: float

    def to_json(self):
        return dict(
            timeout=self.timeout,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            timeout=body["timeout"],
        )


class TestCaseExecuteConfig:
    def __init__(
            self,
            *,
            input_files: InputFileMapping,
            options: ExecuteConfigOptions,
    ):
        self._input_files = input_files
        self._options = options

    def to_json(self):
        return dict(
            input_files=self._input_files.to_json(),
            options=self._options.to_json(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            input_files=InputFileMapping.from_json(body["input_files"]),
            options=ExecuteConfigOptions.from_json(body["options"]),
        )

    def __hash__(self) -> int:
        return hash((self._input_files, self._options))

    @property
    def input_files(self) -> InputFileMapping:
        return self._input_files

    @property
    def options(self) -> ExecuteConfigOptions:
        return self._options


# TestConfig


class AbstractExpectedToken(ABC):
    @abstractmethod
    def _to_json(self) -> dict:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _from_json(cls, body: dict):
        raise NotImplementedError()

    def __hash__(self) -> int:
        raise NotImplementedError()

    def to_json(self) -> dict:
        return dict(
            **self._to_json(),
            type=type(self).__name__,
        )

    @classmethod
    def from_json(cls, body: dict):
        sub_classes = cls.__subclasses__()
        for sub_cls in sub_classes:
            if sub_cls.__name__ == body["type"]:
                return sub_cls._from_json(body)
        assert False, body

    @classmethod
    def create_default(cls) -> "AbstractExpectedToken":
        raise NotImplementedError()


class TextExpectedToken(AbstractExpectedToken):
    def __init__(self, value: str):
        assert isinstance(value, str), value
        self._value = value

    def _to_json(self) -> dict:
        return dict(
            value=self._value,
        )

    @classmethod
    def _from_json(cls, body: dict):
        return cls(
            value=body["value"],
        )

    def __hash__(self) -> int:
        return hash(self._value)

    @property
    def value(self) -> str:
        return self._value

    @classmethod
    def create_default(cls) -> "TextExpectedToken":
        return TextExpectedToken(value="")


class FloatExpectedToken(AbstractExpectedToken):
    def __init__(self, value: float):
        assert isinstance(value, float), value
        self._value = value

    def _to_json(self) -> dict:
        return dict(
            value=self._value,
        )

    @classmethod
    def _from_json(cls, body: dict):
        return cls(
            value=body["value"],
        )

    def __hash__(self) -> int:
        return hash(self._value)

    @property
    def value(self) -> float:
        return self._value

    @classmethod
    def create_default(cls) -> "FloatExpectedToken":
        return FloatExpectedToken(value=0.0)

    def is_matched(self, token: str):
        raise NotImplementedError()


class ExpectedTokenList(list[AbstractExpectedToken]):
    def to_json(self) -> list:
        return [
            token.to_json()
            for token in self
        ]

    @classmethod
    def from_json(cls, body: list):
        return cls([
            AbstractExpectedToken.from_json(token_body)
            for token_body in body
        ])

    def __hash__(self) -> int:
        return hash(tuple(self))

    def is_empty(self) -> bool:
        return len(self) == 0


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


@dataclass(frozen=True)
class TestConfigOptions:
    ordered_matching: bool
    float_tolerance: float
    allowable_edit_distance: int

    # ignore_whitespace: bool

    def to_json(self):
        return dict(
            ordered_matching=self.ordered_matching,
            float_tolerance=self.float_tolerance,
            allowable_edit_distance=self.allowable_edit_distance,
            # ignore_whitespace=self.ignore_whitespace,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            ordered_matching=body["ordered_matching"],
            float_tolerance=body["float_tolerance"],
            allowable_edit_distance=body["allowable_edit_distance"],
            # ignore_whitespace=body["ignore_whitespace"],
        )


class TestCaseTestConfig:
    def __init__(
            self,
            *,
            expected_output_files: ExpectedOutputFileMapping,
            options: TestConfigOptions,
    ):
        self._expected_output_files = expected_output_files
        self._options = options

    @property
    def expected_output_files(self):
        return self._expected_output_files

    @property
    def options(self):
        return self._options

    def to_json(self):
        return dict(
            expected_output_files=self._expected_output_files.to_json(),
            options=self._options.to_json(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            expected_output_files=ExpectedOutputFileMapping.from_json(
                body['expected_output_files']
            ),
            options=TestConfigOptions.from_json(body['options']),
        )

    def __hash__(self) -> int:
        return hash((self._expected_output_files, self._options))


# TestCaseConfig

class TestCaseConfig:
    def __init__(
            self,
            *,
            execute_config: TestCaseExecuteConfig,
            test_config: TestCaseTestConfig,
    ):
        self._execute_config = execute_config
        self._test_config = test_config

    @classmethod
    def from_json(cls, body):
        return cls(
            execute_config=TestCaseExecuteConfig.from_json(body["execute_config"]),
            test_config=TestCaseTestConfig.from_json(body["test_config"]),
        )

    def to_json(self):
        return dict(
            execute_config=self._execute_config.to_json(),
            test_config=self._test_config.to_json(),
        )

    @property
    def execute_config(self):
        return self._execute_config

    @property
    def test_config(self):
        return self._test_config

    @classmethod
    def create_default(cls):
        return cls(
            execute_config=TestCaseExecuteConfig(
                input_files=InputFileMapping(),
                options=ExecuteConfigOptions(
                    timeout=5.0,
                ),
            ),
            test_config=TestCaseTestConfig(
                expected_output_files=ExpectedOutputFileMapping(),
                options=TestConfigOptions(
                    ordered_matching=True,
                    float_tolerance=1.0e-6,
                    allowable_edit_distance=0,
                    # ignore_whitespace=False,
                ),
            ),
        )
