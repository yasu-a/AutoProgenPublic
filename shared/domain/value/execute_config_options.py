from dataclasses import dataclass


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
