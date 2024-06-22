class ProjectIOError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class ManabaReportArchiveIOError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class BuildServiceError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class CompileServiceError(RuntimeError):
    def __init__(self, *, reason: str, output: str | None):
        self.reason = reason
        self.output = output


class ProjectCreateServiceError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class ProjectListServiceError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason
