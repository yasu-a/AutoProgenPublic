from dataclasses import dataclass


@dataclass(frozen=True)
class CompileTestResult:
    is_success: bool
    output: str
