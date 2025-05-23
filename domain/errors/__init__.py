# TODO: リファクタリング！！！

class CoreIOError(RuntimeError):
    def __init__(self, message):
        self.message = message


class RepositoryError(RuntimeError):
    pass


class ServiceError(RuntimeError):
    pass


class UseCaseError(RuntimeError):
    pass


class ProjectIOError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class ProjectServiceError(ServiceError):
    def __init__(self, reason: str):
        self.reason = reason


class TestCaseIOError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class ManabaReportArchiveIOError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class StudentSubmissionServiceError(ServiceError):
    def __init__(self, reason: str):
        self.reason = reason


class BuildServiceError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class StorageRunCompilerServiceError(RuntimeError):
    def __init__(self, *, reason: str, output: str | None):
        self.reason = reason
        self.output = output


class StorageRunExecutableServiceError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class ExecuteServiceError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class TestServiceError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class ProjectListServiceError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class CompileToolIOError(RuntimeError):
    def __init__(self, reason: str, output: str | None):
        self.reason = reason
        self.output = output


class StudentServiceError(ServiceError):
    def __init__(self, message: str):
        self.message = message


class StudentUseCaseError(UseCaseError):
    def __init__(self, message: str):
        self.message = message


class TaskOperationError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class StopTask(RuntimeError):
    pass


class StudentMasterServiceError(ServiceError):
    def __init__(self, reason: str):
        self.reason = reason


class MatchServiceError(ServiceError):
    def __init__(self, reason: str):
        self.reason = reason
