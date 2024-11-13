from dataclasses import dataclass


@dataclass(frozen=True)
class TestConfigOptions:
    float_tolerance: float

    def to_json(self):
        return dict(
            float_tolerance=self.float_tolerance,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            float_tolerance=body["float_tolerance"],
        )
