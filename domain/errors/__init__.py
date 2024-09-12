from domain.models.testcase import TestCaseExecuteConfig, TestCaseTestConfig


class ProjectIOError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class TestCaseIOError(RuntimeError):
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


class ExecuteServiceError(RuntimeError):
    def __init__(self, *, reason: str, execute_config: TestCaseExecuteConfig):
        self.reason = reason
        self.execute_config = execute_config


class TestServiceError(RuntimeError):
    def __init__(self, *, reason: str, test_config: TestCaseTestConfig):
        self.reason = reason
        self.test_config = test_config


class ProjectCreateServiceError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class ProjectListServiceError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


# class ExecuteConfigEditDomainServiceError(RuntimeError):
#     def __init__(self, *, reason: str):
#         self.reason = reason

class CompileToolIOError(RuntimeError):
    def __init__(self, reason: str, output: str | None):
        self.reason = reason
        self.output = output


class CompileTestServiceError(RuntimeError):
    def __init__(self, *, reason: str, output: str | None):
        self.reason = reason
        self.output = output
