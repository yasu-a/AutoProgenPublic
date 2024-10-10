from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from domain.models.student_master import StudentMaster, Student
from domain.models.values import StudentID
from files.core.current_project import CurrentProjectCoreIO
from files.path_providers.project_static import ProjectStaticPathProvider


class StudentRepository:
    # 生徒マスタから生徒のメタデータ（Studentインスタンス）を読み書きするレポジトリ

    def __init__(
            self,
            *,
            project_static_path_provider: ProjectStaticPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._project_static_path_provider = project_static_path_provider
        self._current_project_core_io = current_project_core_io

        self._lock = QMutex()
        self._student_master_cache: StudentMaster | None = None

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def __write_student_master_unlocked(self, student_master: StudentMaster) -> None:
        json_fullpath = self._project_static_path_provider.student_master_json_fullpath()
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)

        self._current_project_core_io.write_json(
            json_fullpath=json_fullpath,
            body=student_master.to_json(),
        )

        self._student_master_cache = student_master

    def __read_student_master_unlocked(self) -> StudentMaster:
        if self._student_master_cache is not None:
            return self._student_master_cache

        json_fullpath = self._project_static_path_provider.student_master_json_fullpath()
        if not json_fullpath.exists():
            student_master = StudentMaster()
            self.__write_student_master_unlocked(student_master)

        body = self._current_project_core_io.read_json(
            json_fullpath=json_fullpath,
        )
        student_master = StudentMaster.from_json(body=body)

        self._student_master_cache = student_master

        return student_master

    def put(self, student_master: StudentMaster) -> None:
        with self.__lock():
            self.__write_student_master_unlocked(student_master)

    def exists(self) -> bool:
        with self.__lock():
            student_master = self.__read_student_master_unlocked()
            return not student_master.is_empty()

    def get(self, student_id: StudentID) -> Student:
        with self.__lock():
            student_master = self.__read_student_master_unlocked()
            for student in student_master:
                if student.student_id == student_id:
                    return student
            raise ValueError(f"Student {student_id} not found")

    def list(self) -> StudentMaster:
        with self.__lock():
            return self.__read_student_master_unlocked()
