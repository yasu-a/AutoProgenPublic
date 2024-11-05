from PyQt5.QtCore import QObject, QThread

from domain.models.values import StudentID
from utils.app_logging import create_logger


class AbstractTask(QThread):
    def __init__(self, parent: QObject):
        super().__init__(parent)


class AbstractStudentTask(AbstractTask):
    def __init__(self, parent: QObject, student_id: StudentID):
        super().__init__(parent)
        self._student_id = student_id
        self._logger = create_logger(name=f"{type(self).__name__}({str(student_id)})")

    @property
    def student_id(self):
        return self._student_id
