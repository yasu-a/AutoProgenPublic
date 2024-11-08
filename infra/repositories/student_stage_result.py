from contextlib import contextmanager
from typing import Generic

from PyQt5.QtCore import QMutex

from domain.models.student_stage_result import *
from domain.models.values import StudentID
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.path_providers.current_project import StudentStageResultPathProvider

K = TypeVar("K")  # key type
V = TypeVar("V")  # value type


@dataclass(slots=True)
class LRUCacheEntry(Generic[V]):
    v: V
    age: int


class LRUCache(Generic[K, V]):
    def __init__(self, max_size: int, reduced_size: int):
        assert 0 < reduced_size < max_size

        self.__max_size = max_size
        self.__reduced_size = reduced_size

        self.__cache: dict[K, LRUCacheEntry[V]] = {}
        self.__next_age = 0

    def __get_next_age(self) -> int:
        self.__next_age += 1
        return self.__next_age

    def __reduce_if_needed(self):
        if len(self.__cache) < self.__max_size:
            return

        entries = list(self.__cache.items())
        entries.sort(key=lambda item: item[1].age, reverse=True)

        self.__cache.clear()
        for i in range(self.__reduced_size):
            k, entry = entries[i]
            self.__cache[k] = entry

    def __contains__(self, k: K) -> bool:
        return k in self.__cache

    def __getitem__(self, k: K) -> V:
        return self.__cache[k].v

    def __setitem__(self, k: K, v: V) -> None:
        self.__cache[k] = LRUCacheEntry[V](v=v, age=self.__next_age)
        self.__reduce_if_needed()

    def __delitem__(self, k: K) -> None:
        del self.__cache[k]


class StudentLockServer:
    def __init__(self):
        self._lock = QMutex()
        self._student_locks: dict[StudentID, QMutex] = {}

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def __getitem__(self, student_id: StudentID) -> QMutex:
        with self.__lock():
            if student_id not in self._student_locks:
                self._student_locks[student_id] = QMutex()
            return self._student_locks[student_id]


class StudentStageResultRepository:
    def __init__(
            self,
            *,
            student_stage_result_path_provider: StudentStageResultPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_stage_result_path_provider = student_stage_result_path_provider
        self._current_project_core_io = current_project_core_io

        self._student_lock_server = StudentLockServer()

        self.__lru_cache: LRUCache[tuple[StudentID, AbstractStage], AbstractStudentStageResult] \
            = LRUCache(max_size=1 << 10, reduced_size=1 << 9)

    @contextmanager
    def __lock(self, student_id: StudentID):
        self._student_lock_server[student_id].lock()
        try:
            yield
        finally:
            self._student_lock_server[student_id].unlock()

    @classmethod
    def __get_type_name_of_result_type(
            cls,
            result_type: type[AbstractStudentStageResult],
    ) -> str:
        return result_type.__name__

    RESULT_TYPES = (
        BuildSuccessStudentStageResult,
        BuildFailureStudentStageResult,
        CompileSuccessStudentStageResult,
        CompileFailureStudentStageResult,
        ExecuteSuccessStudentStageResult,
        ExecuteFailureStudentStageResult,
        TestSuccessStudentStageResult,
        TestFailureStudentStageResult,
    )

    @classmethod
    def __get_result_type_from_type_name(
            cls,
            result_type_name: str,
    ) -> type[AbstractStudentStageResult]:
        for sub_cls in cls.RESULT_TYPES:
            if result_type_name == cls.__get_type_name_of_result_type(sub_cls):
                return sub_cls
        assert False, result_type_name

    def put(
            self,
            result: AbstractStudentStageResult,
    ) -> None:
        with self.__lock(result.student_id):
            json_fullpath = (
                self._student_stage_result_path_provider.result_json_fullpath(
                    student_id=result.student_id,
                    stage=result.stage,
                )
            )
            json_fullpath.parent.mkdir(parents=True, exist_ok=True)

            self._current_project_core_io.write_json(
                json_fullpath=json_fullpath,
                body={
                    "__type__": self.__get_type_name_of_result_type(type(result)),
                    **result.to_json(),
                },
            )
            self.__lru_cache[(result.student_id, result.stage)] = result

    def exists(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> bool:
        with self.__lock(student_id):
            if (student_id, stage) in self.__lru_cache:
                return True

            json_fullpath = (
                self._student_stage_result_path_provider.result_json_fullpath(
                    student_id=student_id,
                    stage=stage,
                )
            )
            return json_fullpath.exists()

    def get(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> AbstractStudentStageResult:
        with self.__lock(student_id):
            if (student_id, stage) in self.__lru_cache:
                return self.__lru_cache[(student_id, stage)]

            json_fullpath = (
                self._student_stage_result_path_provider.result_json_fullpath(
                    student_id=student_id,
                    stage=stage,
                )
            )
            if not json_fullpath.exists():
                raise ValueError(f"Build result for student {student_id} not found")

            body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
            type_name = body.pop("__type__")
            result_type = self.__get_result_type_from_type_name(type_name)
            result = result_type.from_json(body)

            self.__lru_cache[(student_id, stage)] = result

            return result

    def delete(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> None:
        with self.__lock(student_id):
            if (student_id, stage) in self.__lru_cache:
                del self.__lru_cache[(student_id, stage)]

            json_fullpath = (
                self._student_stage_result_path_provider.result_json_fullpath(
                    student_id=student_id,
                    stage=stage,
                )
            )
            if not json_fullpath.exists():
                raise ValueError(f"Build result for student {student_id} not found")

            self._current_project_core_io.unlink(
                path=json_fullpath,
            )
