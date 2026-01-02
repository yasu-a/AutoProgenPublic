from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from shared.domain.value.identifier import StudentID


class ICurrentDatetimeGateway(ABC):
    @abstractmethod
    def execute(self) -> datetime:
        raise NotImplementedError()


class IStudentSubmissionGetSourceContentGateway(ABC):
    @abstractmethod
    def execute(self, student_id: StudentID) -> str:
        raise NotImplementedError()


class IStudentSubmissionGetChecksumGateway(ABC):
    @abstractmethod
    def execute(self, student_id: StudentID) -> int:
        raise NotImplementedError()


class IStudentSubmissionFolderShowGateway(ABC):
    @abstractmethod
    def execute(self, student_id: StudentID) -> None:
        raise NotImplementedError()
