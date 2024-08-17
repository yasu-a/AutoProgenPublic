from datetime import datetime
from typing import Callable

from PyQt5.QtCore import QMutex

from app_logging import create_logger
from domain.models.reuslts import BuildResult, CompileResult, ExecuteResult
from domain.models.values import StudentID
from files.project_core import ProjectCoreIO
from files.project_path_provider import ProjectPathProvider


class ProgressIOWithContext:
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
            student_id: StudentID,
            locker: Callable[[], None],
            unlocker: Callable[[], None],
    ):
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io
        self._student_id = student_id
        self._locker = locker
        self._unlocker = unlocker

    def __enter__(self):
        self._locker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._unlocker()
        return False

    def clear_student(self) -> None:
        # 生徒のステージの進捗で生成されるプロジェクトデータを削除する
        for student_dynamic_folder_fullpath in \
                self._project_path_provider.iter_student_dynamic_folder_fullpath(self._student_id):
            if not student_dynamic_folder_fullpath.exists():
                continue
            self._project_core_io.rmtree_folder(student_dynamic_folder_fullpath)

    def get_student_mtime(self) -> datetime | None:
        # 生徒のプロジェクトデータの最終更新日時を取得する
        mtime_max = None
        path_it = self._project_path_provider.iter_student_dynamic_folder_fullpath(self._student_id)
        for folder_fullpath in path_it:
            if not folder_fullpath.exists():
                continue
            mtime = folder_fullpath.stat().st_mtime
            if mtime_max is None or mtime > mtime_max:
                mtime_max = mtime
        return mtime_max and datetime.fromtimestamp(mtime_max)

    def write_student_build_result(self, result: BuildResult) -> None:
        # 生徒のビルド結果を永続化する
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=self._student_id,
        )
        self._project_core_io.write_json(
            json_fullpath=result_json_fullpath,
            body=result.to_json(),
        )

    def is_student_build_finished(self) -> bool:
        # 生徒のビルドが終了したかどうかを確認する
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=self._student_id,
        )
        return result_json_fullpath.exists()

    def read_student_build_result(self) -> BuildResult:
        # 生徒のビルド結果を読み込む
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=self._student_id,
        )
        result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        body = self._project_core_io.read_json(
            json_fullpath=result_json_fullpath,
        )
        assert body is not None, result_json_fullpath
        return BuildResult.from_json(body)

    def write_student_compile_result(self, result: CompileResult) -> None:
        # 生徒のコンパイル結果を永続化する
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=self._student_id,
        )
        self._project_core_io.write_json(
            json_fullpath=result_json_fullpath,
            body=result.to_json(),
        )

    def is_student_compile_finished(self) -> bool:
        # 生徒のコンパイルが終了したかどうかを確認する
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=self._student_id,
        )
        return result_json_fullpath.exists()

    def read_student_compile_result(self) -> CompileResult:
        # 生徒のコンパイル結果を読み込む
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=self._student_id,
        )
        result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        body = self._project_core_io.read_json(
            json_fullpath=result_json_fullpath,
        )
        assert body is not None, result_json_fullpath
        return CompileResult.from_json(body)

    def write_student_execute_result(self, result: ExecuteResult) -> None:
        # 生徒の実行結果を永続化する
        result_json_fullpath = self._project_path_provider.student_execute_result_json_fullpath(
            student_id=self._student_id,
        )
        self._project_core_io.write_json(
            json_fullpath=result_json_fullpath,
            body=result.to_json(),
        )

    def is_student_execute_finished(self) -> bool:
        # 生徒の実行が終了したかどうかを確認する
        result_json_fullpath = self._project_path_provider.student_execute_result_json_fullpath(
            student_id=self._student_id,
        )
        return result_json_fullpath.exists()

    def read_student_execute_result(self) -> ExecuteResult:
        # 生徒の実行結果を読み込む
        result_json_fullpath = self._project_path_provider.student_execute_result_json_fullpath(
            student_id=self._student_id,
        )
        result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        body = self._project_core_io.read_json(
            json_fullpath=result_json_fullpath,
        )
        assert body is not None, result_json_fullpath
        return ExecuteResult.from_json(body)


class ProgressIO:
    # 生徒のステージ進捗に関するデータの読み書き

    _logger = create_logger()

    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io
        self._lock_global: QMutex = QMutex()
        self._lock_student: dict[StudentID, QMutex] = {}

    def __get_lock_for_student(self, student_id: StudentID) -> QMutex:
        self._lock_global.lock()
        if student_id not in self._lock_student:
            self._lock_student[student_id] = QMutex()
        lock = self._lock_student[student_id]
        self._lock_global.unlock()
        return lock

    def __begin_session_for_student(self, student_id: StudentID) -> None:
        lock = self.__get_lock_for_student(student_id)
        lock.lock()

    def __end_session_for_student(self, student_id: StudentID) -> None:
        lock = self.__get_lock_for_student(student_id)
        lock.unlock()

    def with_student(self, student_id: StudentID) -> ProgressIOWithContext:
        return ProgressIOWithContext(
            project_path_provider=self._project_path_provider,
            project_core_io=self._project_core_io,
            student_id=student_id,
            locker=lambda: self.__begin_session_for_student(student_id),
            unlocker=lambda: self.__end_session_for_student(student_id),
        )
