from PyQt5.QtCore import QThread, QObject

from domain.models.values import StudentID
from utils.app_logging import create_logger


class AbstractTask(QThread):
    def __init__(self, parent: QObject):
        super().__init__(parent)

        self.__stop = False

    def send_stop(self) -> None:
        self.__stop = True

    def is_stop_received(self) -> bool:
        return self.__stop


class AbstractStudentTask(AbstractTask):
    def __init__(self, parent: QObject, student_id: StudentID):
        super().__init__(parent)
        self._student_id = student_id
        self._logger = create_logger(name=f"{type(self).__name__}({str(student_id)})")

    @property
    def student_id(self):
        return self._student_id
