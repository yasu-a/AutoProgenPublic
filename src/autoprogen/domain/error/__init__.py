# TODO: リファクタリング！！！

from autoprogen.domain.error.stage.base import StageError


class CoreIOError(RuntimeError):
    def __init__(self, message):
        self.message = message


class RepositoryError(RuntimeError):
    pass


class RepositoryItemNotFoundError(RepositoryError):
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


class ManabaReportArchiveError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class ReadonlyExcelWorksheetGatewayError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class ManabaReportListParserError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class ManabaReportListArchiveValidateServiceError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class StudentSubmissionServiceError(ServiceError):
    def __init__(self, reason: str):
        self.reason = reason


class BuildServiceError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class StorageRunCompilerServiceError(RuntimeError):
    """コンパイル処理の構造化エラーとコンパイラ出力を伝える。"""

    def __init__(self, *, error: StageError, output: str | None):
        """原因となったStageErrorと、取得できた生出力を保持する。"""
        self.error = error
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
    """コンパイラIOの構造化エラーと生出力をServiceへ伝える。"""

    def __init__(self, *, error: StageError, output: str | None):
        """原因となったStageErrorと、取得できた生出力を保持する。"""
        self.error = error
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
