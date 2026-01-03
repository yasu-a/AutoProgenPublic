from abc import ABC, abstractmethod
from enum import IntEnum, auto
from pathlib import Path

from shared.domain.value.identifier import ProjectID, StudentID


class IProjectListGateway(ABC):
    @abstractmethod
    def execute(self) -> list[ProjectID]:
        raise NotImplementedError()


class ProjectConfigState(IntEnum):
    NORMAL = auto()  # 正常
    META_BROKEN = auto()  # 読み取れない
    INCOMPATIBLE_APP_VERSION = auto()  # バージョンが正しくない
    UNOPENABLE = auto()  # 開けない


class IProjectConfigStateGateway(ABC):
    @abstractmethod
    def execute(self, project_id: ProjectID) -> ProjectConfigState:
        raise NotImplementedError()


class IProjectFileSystemGateway(ABC):
    @abstractmethod
    def get_size(self, project_id: ProjectID) -> int:
        raise NotImplementedError()

    @abstractmethod
    def show_base_folder(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def show_folder(self, project_id: ProjectID) -> None:
        raise NotImplementedError()


class StudentSubmissionListSourceRelativePathGatewayError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


class IStudentSubmissionListSourceRelativePathGateway(ABC):
    @abstractmethod
    def execute(self, *, student_id: StudentID) -> list[Path]:
        raise NotImplementedError()


class IStudentSubmissionGetFileContentGateway(ABC):
    @abstractmethod
    def execute(self, *, student_id: StudentID, file_relative_path: Path) -> bytes:
        raise NotImplementedError()
