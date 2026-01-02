from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

from feature.projman.usecase.dto import NormalProjectSummary, ProjectInitializeResult, \
    ProjectConfigState
from shared.domain.value.identifier import ProjectID, StudentID


# ProjectEntity UseCase Interfaces
class IProjectCheckExistByNameUseCase(ABC):
    @abstractmethod
    def execute(self, target_project_name: str) -> bool:
        raise NotImplementedError()


class IProjectCreateUseCase(ABC):
    @abstractmethod
    def execute(self, project_name: str, target_number: int, zip_name: str) -> ProjectID:
        raise NotImplementedError()


class IProjectDeleteUseCase(ABC):
    @abstractmethod
    def execute(self, project_id: ProjectID) -> None:
        raise NotImplementedError()


class IProjectGetSizeQueryUseCase(ABC):
    @abstractmethod
    def execute(self, project_id: ProjectID) -> int:
        raise NotImplementedError()


class IProjectUpdateLastOpenedUseCase(ABC):
    """プロジェクトの最終開いた時刻を更新するUseCaseのインターフェース"""

    @abstractmethod
    def execute(self, project_id: ProjectID) -> None:
        raise NotImplementedError()


class IProjectListRecentSummaryUseCase(ABC):
    @abstractmethod
    def execute(self) -> list[NormalProjectSummary]:
        raise NotImplementedError()


class IProjectBaseFolderShowUseCase(ABC):
    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError()


class IProjectFolderShowUseCase(ABC):
    @abstractmethod
    def execute(self, project_id: ProjectID) -> None:
        raise NotImplementedError()


# Current ProjectEntity UseCase Interfaces
class ICurrentProjectSummaryGetUseCase(ABC):
    @abstractmethod
    def execute(self) -> NormalProjectSummary:
        raise NotImplementedError()


class ICurrentProjectInitializeStaticUseCase(ABC):
    @abstractmethod
    def execute(self, callback: Callable[[str], None]) -> ProjectInitializeResult:
        raise NotImplementedError()


class IStudentMasterCreateUseCase(ABC):
    """学生マスタ作成UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError()


class IStudentSubmissionExtractUseCase(ABC):
    """学生提出物展開UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError()


# Gateway Interfaces
class IProjectListGateway(ABC):
    @abstractmethod
    def execute(self) -> list[ProjectID]:
        raise NotImplementedError()


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


class IStudentSubmissionListSourceRelativePathGateway(ABC):
    @abstractmethod
    def execute(self, *, student_id: StudentID) -> list[Path]:
        raise NotImplementedError()


class IStudentSubmissionGetFileContentGateway(ABC):
    @abstractmethod
    def execute(self, *, student_id: StudentID, file_relative_path: Path) -> bytes:
        raise NotImplementedError()


class StudentSubmissionListSourceRelativePathGatewayError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
