from dataclasses import dataclass, asdict


@dataclass(slots=True)
class EnvironmentCompileResult:
    success: bool
    reason: str | None
    output_lines: list[str] | None

    @classmethod
    def from_cli_and_reason(cls, success: bool, output: str | None, reason: str | None = None):
        return cls(
            success=success,
            reason=reason,
            output_lines=(
                None
                if output is None else
                [line.rstrip() for line in output.split("\n")]
            ),
        )

    def to_json(self):
        return asdict(self)

    @classmethod
    def from_json(cls, body):
        return cls(
            success=body["success"],
            reason=body["reason"],
            output_lines=body["output_lines"],
        )
