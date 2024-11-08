from abc import ABC, abstractmethod


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

    def __eq__(self, other) -> bool:
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

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        return self._value == other._value

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

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        return self._value == other._value

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
