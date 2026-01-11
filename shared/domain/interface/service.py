from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.model.stage import StageElement, Stage
from shared.domain.model.student_result import AbstractStageResultEntity
from shared.domain.service.dto.storage_diff_snapshot import StorageDiff, StorageFileSnapshot
from shared.domain.service.dto.storage_run_compiler import StorageCompileServiceResult
from shared.domain.service.dto.storage_run_executable import StorageExecuteServiceResult
from shared.domain.value.identifier import TestCaseID, StorageID, StudentID
from shared.domain.value.output_file import OutputFileCollection
from shared.domain.value.output_file_test_result import MatchResult
from shared.domain.value.pattern import PatternList
from shared.domain.value.test_config_options import TestConfigOptions


# TestCase Service Interfaces
class ITestCaseConfigCopyService(ABC):
    @abstractmethod
    def execute(self, testcase_id: TestCaseID, new_testcase_id: TestCaseID) -> None:
        raise NotImplementedError()


# Match Service Interfaces
class IMatchGetBestService(ABC):
    @classmethod
    @abstractmethod
    def execute(
            cls,
            *,
            content_string: str,
            patterns: PatternList,
            test_config_options: TestConfigOptions,
    ) -> MatchResult:
        raise NotImplementedError()


# Storage Service Interfaces
class IStorageCreateService(ABC):
    @abstractmethod
    def execute(self) -> StorageID:
        raise NotImplementedError()


class IStorageDeleteService(ABC):
    @abstractmethod
    def execute(self, storage_id: StorageID) -> None:
        raise NotImplementedError()


class IStorageLoadTestSourceService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            storage_id: StorageID,
            file_relative_path: Path,
    ) -> None:
        raise NotImplementedError()


class IStorageLoadStudentSourceService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            student_id: StudentID,
            storage_id: StorageID,
            file_relative_path: Path,
    ) -> None:
        raise NotImplementedError()


class IStorageLoadStudentExecutableService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            student_id: StudentID,
            storage_id: StorageID,
            file_relative_path: Path,
    ) -> None:
        raise NotImplementedError()


class IStorageStoreStudentExecutableService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            student_id: StudentID,
            storage_id: StorageID,
            file_relative_path: Path,
    ) -> None:
        raise NotImplementedError()


class IStorageLoadExecuteConfigInputFilesService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            storage_id: StorageID,
            testcase_id: TestCaseID,
    ) -> None:
        raise NotImplementedError()


class IStorageWriteStdoutFileService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            storage_id: StorageID,
            stdout_text: str,
    ) -> None:
        raise NotImplementedError()


class IStorageCreateOutputFileCollectionFromDiffService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            storage_id: StorageID,
            storage_diff: StorageDiff,
    ) -> OutputFileCollection:
        raise NotImplementedError()


class IStorageTakeSnapshotService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            storage_id: StorageID,
    ) -> StorageFileSnapshot:
        raise NotImplementedError()


# Storage Run Service Interfaces
class IStorageRunCompilerService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            storage_id: StorageID,
            source_file_relative_path: Path,
            compiler_tool_fullpath: Path = None,
    ) -> StorageCompileServiceResult:
        raise NotImplementedError()


class IStorageRunExecutableService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            storage_id: StorageID,
            executable_file_relative_path: Path,
            timeout: float,
    ) -> StorageExecuteServiceResult:
        raise NotImplementedError()


# Stage Path Service Interfaces
class IStagePathListSubService(ABC):
    @abstractmethod
    def execute(self) -> list[list[StageElement]]:
        raise NotImplementedError()


class IStagePathGetByTestCaseIDService(ABC):
    @abstractmethod
    def execute(self, testcase_id: TestCaseID) -> list[StageElement]:
        raise NotImplementedError()


# Student Dynamic Service Interfaces
class IStudentDynamicClearService(ABC):
    @abstractmethod
    def execute(self, *, student_id: StudentID) -> None:
        raise NotImplementedError()


class IStudentDynamicSetSourceContentService(ABC):
    @abstractmethod
    def execute(self, *, student_id: StudentID, source_content_text: str) -> None:
        raise NotImplementedError()


# Student Mark Service Interfaces
class IStudentMarkEntityGetSubService(ABC):
    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentMarkEntity:
        raise NotImplementedError()


class IStudentMarkEntityListService(ABC):
    @abstractmethod
    def execute(self) -> list[StudentMarkEntity]:
        raise NotImplementedError()


# Student Stage Path Result Service Interfaces
class IStudentStagePathResultEntityCheckRollbackService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            student_id: StudentID,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None],
    ) -> Stage | None:
        raise NotImplementedError()


class IStudentStagePathResultEntityRollbackService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            student_id: StudentID,
            stage_path: list[StageElement],
            stage_type: Stage,
    ) -> None:
        raise NotImplementedError()


class IStudentStagePathResultEntityClearService(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            student_id: StudentID,
    ) -> None:
        raise NotImplementedError()


class IStudentPutStagePathResultEntityService(ABC):
    @abstractmethod
    def execute(
            self,
            result: "AbstractStageResultEntity",
    ) -> None:
        raise NotImplementedError()


class IStudentGetStagePathResultMapService(ABC):
    @abstractmethod
    def execute(
            self,
            student_id: StudentID,
            stage_path: list[StageElement],
    ) -> OrderedDict[StageElement, AbstractStageResultEntity | None]:
        raise NotImplementedError()


class IStudentStagePathResultEntityCheckTimestampQueryService(ABC):
    @abstractmethod
    def execute(self, student_id: StudentID) -> datetime | None:
        raise NotImplementedError()


class IStudentStagePathResultAnalyzerService(ABC):
    @abstractmethod
    def get_next_stage(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> StageElement | None:
        raise NotImplementedError()

    @abstractmethod
    def is_all_finished(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_last_failure_detailed_reason(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> str | None:
        raise NotImplementedError()

    @abstractmethod
    def get_last_failure_main_reason(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> str | None:
        raise NotImplementedError()

    @abstractmethod
    def get_stage_statuses(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> OrderedDict[StageElement, str]:  # returns "unfinished", "success", "failure"
        raise NotImplementedError()

    @abstractmethod
    def is_last_stage_success(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> bool | None:
        raise NotImplementedError()
