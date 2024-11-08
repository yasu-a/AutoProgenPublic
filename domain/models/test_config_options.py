from dataclasses import dataclass


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
