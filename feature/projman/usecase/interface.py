from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from shared.domain.value.identifier import ProjectID


# DTOはinterfaceの直上に定義
@dataclass(frozen=True)
class ProjectInitializeResultDto:
    """プロジェクト初期化UseCaseの結果を表すDTO"""
    message: str | None

    @classmethod
    def create_success(cls):
        return cls(message=None)

    @classmethod
    def create_error(cls, message: str):
        return cls(message=message)


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


class IProjectUpdateLastOpenUseCase(ABC):
    """プロジェクトの最終開いた時刻を更新するUseCaseのインターフェース"""

    @abstractmethod
    def execute(self, project_id: ProjectID) -> None:
        raise NotImplementedError()


class AbstractProjectSummary(ABC):  # TODO: rename to *Dto
    def __init__(self, *, project_id: ProjectID):
        self._project_id = project_id

    @property
    def project_id(self) -> ProjectID:
        return self._project_id

    @property
    def project_name(self) -> str:
        return str(self._project_id)

    @property
    @abstractmethod
    def has_error(self) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def error_message(self) -> str:
        # self.has_error is True ならエラーメッセージを返し，それ以外は例外を投げる
        raise NotImplementedError()

    def __lt__(self, other):
        if isinstance(other, AbstractProjectSummary):
            return self._project_id < other._project_id

        return NotImplemented


class NormalProjectSummary(AbstractProjectSummary):
    # 正常なプロジェクトのサマリーデータ
    def __init__(
            self,
            *,
            project_id: ProjectID,
            target_number: int,
            zip_name: str,
            open_at: datetime,
    ):
        super().__init__(project_id=project_id)
        self._target_number = target_number
        self._zip_name = zip_name
        self._open_at = open_at

    @property
    def target_number(self) -> int:
        return self._target_number

    @property
    def zip_name(self) -> str:
        return self._zip_name

    @property
    def open_at(self) -> datetime:
        return self._open_at

    @property
    def has_error(self) -> bool:
        return False

    @property
    def error_message(self) -> str:
        raise ValueError("ProjectEntity has no error")

    def __lt__(self, other):
        if isinstance(other, NormalProjectSummary):
            if self._open_at != other._open_at:
                return self._open_at > other._open_at
        elif isinstance(other, AbstractProjectSummary):
            return True

        return super().__lt__(other)


class ErrorProjectSummary(AbstractProjectSummary):
    # エラーを含むプロジェクトのサマリーデータ
    def __init__(self, *, project_id: ProjectID, error_message: str):
        super().__init__(project_id=project_id)
        self._error_message = error_message

    @property
    def has_error(self) -> bool:
        return True

    @property
    def error_message(self) -> str:
        return self._error_message

    def __lt__(self, other):
        if isinstance(other, NormalProjectSummary):
            return False

        return super().__lt__(other)


@dataclass(frozen=True)
class ProjectInitializeResult:
    message: str | None

    @classmethod
    def create_success(cls):
        return cls(message=None)

    @classmethod
    def create_error(cls, message: str):
        return cls(message=message)

    @property
    def has_error(self) -> bool:
        return self.message is not None


class IProjectListRecentSummaryUseCase(ABC):
    @abstractmethod
    def execute(self) -> list[AbstractProjectSummary]:
        raise NotImplementedError()


class IProjectBaseFolderShowUseCase(ABC):
    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError()


class IProjectFolderShowUseCase(ABC):
    @abstractmethod
    def execute(self, project_id: ProjectID) -> None:
        raise NotImplementedError()


@dataclass
class NewProjectConfigDto:
    project_name: str
    target_number: int
    manaba_report_archive_fullpath: Path


# Current ProjectEntity UseCase Interfaces
class ICurrentProjectSummaryGetUseCase(ABC):
    @abstractmethod
    def execute(self) -> NormalProjectSummary:
        raise NotImplementedError()


class ICurrentProjectInitializeStaticUseCase(ABC):
    @abstractmethod
    def execute(self, progress_callback: Callable[[str], None]) -> ProjectInitializeResultDto:
        raise NotImplementedError()


class IStudentMasterCreateUseCase(ABC):
    """学生マスタ作成UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, progress_callback: Callable[[str], None]):
        raise NotImplementedError()


class IStudentSubmissionExtractUseCase(ABC):
    """学生提出物展開UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, progress_callback: Callable[[str], None]):
        raise NotImplementedError()
