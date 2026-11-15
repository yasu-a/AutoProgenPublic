# TODO: リファクタリング！！！

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


class StopTask(RuntimeError):
    pass


class StudentMasterServiceError(ServiceError):
    def __init__(self, reason: str):
        self.reason = reason


class MatchServiceError(ServiceError):
    def __init__(self, reason: str):
        self.reason = reason
