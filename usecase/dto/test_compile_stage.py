from dataclasses import dataclass


@dataclass(frozen=True)
class TestCompileStageResult:
    is_success: bool
    output: str
