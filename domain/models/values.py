import re

__all__ = (
    "StudentID",
    "TargetID",
    "TestCaseID",
    "ProjectName",
    "SpecialFileType",
    "FileID",
)

from enum import Enum

from pathlib import Path


class ProjectName:
    def __init__(self, value: str):
        assert isinstance(value, str)
        self.__value = value

    def __str__(self) -> str:
        return self.__value

    def __hash__(self):
        return hash(self.__value)

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.__value == other.__value

    def __repr__(self):
        return f"{type(self).__name__}(\"{self.__value}\")"

    def __lt__(self, other):
        assert isinstance(other, type(self))
        return self.__value > other.__value

    def to_json(self):
        return str(self)

    @classmethod
    def from_json(cls, value):
        return cls(value)


class StudentID:
    @classmethod
    def _validate_value(cls, value: str):
        return re.fullmatch(r"\d{2}[A-Z]\d{7}[A-Z]", value) is not None

    def __init__(self, value: str):
        assert isinstance(value, str)
        if not self._validate_value(value):
            raise ValueError(f"Malformed student id: {value}")

        self.__value = value

    def __str__(self) -> str:
        return self.__value

    def __hash__(self):
        return hash(self.__value)

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.__value == other.__value

    def __repr__(self):
        return f"{type(self).__name__}(\"{self.__value}\")"

    def __lt__(self, other):
        assert isinstance(other, type(self))
        return self.__value < other.__value

    def to_json(self):
        return str(self)

    @classmethod
    def from_json(cls, value):
        return cls(value)


class TargetID:
    def __init__(self, value: int | str):
        try:
            value = int(value)
        except ValueError:
            value = None
        if not isinstance(value, int):
            raise ValueError("Value must be an integer or an integer-compatible value")
        if value < 0:
            raise ValueError("Value must be non-negative")
        self.__value = value

    def __int__(self) -> int:
        return self.__value

    def __str__(self) -> str:
        return str(int(self))

    def __hash__(self):
        return hash(self.__value)

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.__value == other.__value

    def __repr__(self):
        return f"{type(self).__name__}({self.__value})"

    def __lt__(self, other):
        assert isinstance(other, type(self))
        return self.__value < other.__value

    def to_json(self):
        return str(self)

    @classmethod
    def from_json(cls, value):
        return cls(int(value))


class TestCaseID:
    def __init__(self, value: str):
        assert isinstance(value, str)
        self.__value = value

    def __str__(self) -> str:
        return self.__value

    def __hash__(self):
        return hash(self.__value)

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.__value == other.__value

    def __repr__(self):
        return f"{type(self).__name__}(\"{self.__value}\")"

    def __lt__(self, other):
        assert isinstance(other, type(self))
        return self.__value < other.__value

    def to_json(self) -> str:
        return str(self)

    @classmethod
    def from_json(cls, value):
        return cls(value)


class SpecialFileType(Enum):  # values are virtual filename
    STDIN = "__stdin__"
    STDOUT = "__stdout__"


class FileID:
    _is_special: bool
    _value: Path | SpecialFileType

    def __init__(self, value: Path | SpecialFileType | str):
        # value: deployment_relative_path or special_file_type or string notation of instance
        if isinstance(value, Path):
            if str(value).startswith(":"):
                raise ValueError("Malformed file ID")
            assert not value.is_absolute(), value
            self._is_special = False
            self._value = value
        elif isinstance(value, SpecialFileType):
            self._is_special = True
            self._value = value
        elif isinstance(value, str):
            obj = self.__from_string(value)
            self._is_special = obj._is_special
            self._value = obj._value
        else:
            raise ValueError("Invalid type of value for file ID")
        assert isinstance(self._value, (Path, SpecialFileType)), (value, self._value)

    def __to_string(self) -> str:
        if self._is_special:
            return f":{self._value.value}"
        else:
            return str(self._value)

    @classmethod
    def __from_string(cls, s: str):
        if s.startswith(":"):
            return cls(SpecialFileType(s[1:]))
        else:
            return cls(Path(s))

    def to_json(self) -> str:
        return self.__to_string()

    @classmethod
    def from_json(cls, body: str):
        return cls.__from_string(body)

    @property
    def is_special(self) -> bool:
        return self._is_special

    @property
    def special_file_type(self) -> SpecialFileType:
        return self._value

    @property
    def deployment_relative_path(self) -> Path:  # ファイルがフォルダに配備されているときの相対パス
        if self._is_special:
            # noinspection PyTypeChecker
            value: str = self._value.value
            return Path(value)
        else:
            return self._value

    def __str__(self) -> str:
        return self.__to_string()

    def __eq__(self, other):
        assert isinstance(other, FileID), other
        return (
                self._is_special == other._is_special
                and self._value == other._value
        )

    def __hash__(self):
        return hash((self._is_special, self._value))

    def __repr__(self):
        return f"FileID({self._value!r})"

    def __order_index(self) -> tuple:  # インスタンスの順序付けのためのオブジェクトを返す
        return (
            self._is_special,  # is_special
            self._value if self._is_special else None,  # value as a SpecialFileType
            None if self._is_special else self._value,  # value as a Path
        )

    def __lt__(self, other):
        assert isinstance(other, FileID), other
        return self.__order_index() < other.__order_index()

    STDIN: "FileID"
    STDOUT: "FileID"


FileID.STDIN = FileID(SpecialFileType.STDIN)
FileID.STDOUT = FileID(SpecialFileType.STDOUT)
