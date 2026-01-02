from dataclasses import dataclass


@dataclass(frozen=True)
class TestConfigOptions:
    ignore_case: bool

    def to_json(self):
        return dict(
            ignore_case=self.ignore_case,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            ignore_case=body["ignore_case"],
        )
