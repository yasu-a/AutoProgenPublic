import re

__all__ = (
    "StudentID",
    "TargetID",
    "TestCaseID",
    "ProjectName",
)


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

    def to_json(self):
        return str(self)

    @classmethod
    def from_json(cls, value):
        return cls(value)
