from datetime import datetime
from typing import Callable

from PyQt5.QtCore import QMutex

from app_logging import create_logger
from domain.models.mark import Mark
from domain.models.result_build import BuildResult
from domain.models.result_compile import CompileResult
from domain.models.result_execute import ExecuteResult
from domain.models.stages import StudentProgressStage, StudentProgressWithFinishedStage, \
    AbstractStudentProgress, StudentProgressUnstarted
from domain.models.values import StudentID
from files.project import ProjectIO
from files.project_core import ProjectCoreIO
from files.project_path_provider import ProjectPathProvider
from files.testcase import TestCaseIO


class ProgressIOWithContext:
    _logger = create_logger()

    # 生徒のステージ進捗に関するデータの読み書き（ProgressIOのセッション管理を委譲されたインスタンス）
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
            project_io: ProjectIO,
            testcase_io: TestCaseIO,
            student_id: StudentID,
            lock_delegate: Callable[[], None],
            unlock_delegate: Callable[[], None],
    ):
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io
        self._project_io = project_io
        self._testcase_io = testcase_io
        self._student_id = student_id
        self._lock_delegate = lock_delegate
        self._unlock_delegate = unlock_delegate

    # @property
    # def student_id(self) -> StudentID:
    #     return self._student_id

    def __enter__(self):
        self._lock_delegate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._unlock_delegate()
        return False

    def clear_student_build_data(self) -> None:
        # 生徒のビルド用のプロジェクトデータを削除する
        build_folder_fullpath = self._project_path_provider.student_build_folder_fullpath(
            student_id=self._student_id,
        )
        if not build_folder_fullpath.exists():
            return
        return self._project_core_io.rmtree_folder(build_folder_fullpath)

    def clear_student_test_data(self) -> None:
        # 生徒の実行用のプロジェクトデータを削除する
        test_base_folder_fullpath = self._project_path_provider.student_test_base_folder_fullpath(
            student_id=self._student_id,
        )
        if not test_base_folder_fullpath.exists():
            return
        return self._project_core_io.rmtree_folder(test_base_folder_fullpath)

    def clear_student_to_start_stage(self, stage: StudentProgressStage) -> None:
        # stageを含むstage以降の生徒のステージの進捗で生成されるプロジェクトデータを削除する
        if stage == StudentProgressStage.BUILD:
            self.clear_student_build_data()
            self.clear_student_test_data()
        elif stage == StudentProgressStage.COMPILE:
            # TODO: COMPILEとBUILDのデータフォルダを分離する
            #       COMPILEステージはBUILDとフォルダを共有するためクリアできない
            # 代わりにCOMPILEの結果が存在しないことを確認する
            assert not self.is_student_compile_finished(), self._student_id
        elif stage == StudentProgressStage.EXECUTE:
            self.clear_student_test_data()
        else:
            assert False, stage

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

    def write_mark_data(self, mark: Mark):
        json_fullpath = self._project_path_provider.student_mark_data_json_fullpath(
            student_id=self._student_id,
        )
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        self._project_core_io.write_json(
            json_fullpath=json_fullpath,
            body=mark.to_json(),
        )

    def read_mark_data(self) -> Mark:
        json_fullpath = self._project_path_provider.student_mark_data_json_fullpath(
            student_id=self._student_id,
        )
        body = self._project_core_io.read_json(json_fullpath=json_fullpath)
        return Mark.from_json(body)

    def read_mark_data_or_create_default_if_absent(self) -> Mark:
        try:
            return self.read_mark_data()
        except FileNotFoundError:
            return Mark.create_default()

    # ステージ系

    def is_student_stage_finished(self, stage: StudentProgressStage) -> bool:
        # 生徒の指定されたステージが終了しているかを返す
        if stage == StudentProgressStage.BUILD:
            return self.is_student_build_finished()
        if stage == StudentProgressStage.COMPILE:
            return self.is_student_compile_finished()
        if stage == StudentProgressStage.EXECUTE:
            return self.is_student_execute_finished()
        assert False, stage

    def get_student_stage_result(self, stage: StudentProgressStage) \
            -> StudentProgressWithFinishedStage:
        # 生徒の指定されたステージの結果を読み出してProgressとして返す
        if stage == StudentProgressStage.BUILD:
            result = self.read_student_build_result()
            return StudentProgressWithFinishedStage[BuildResult](
                stage=StudentProgressStage.BUILD,
                result=result,
            )
        if stage == StudentProgressStage.COMPILE:
            result = self.read_student_compile_result()
            return StudentProgressWithFinishedStage[CompileResult](
                stage=StudentProgressStage.COMPILE,
                result=result,
            )
        if stage == StudentProgressStage.EXECUTE:
            result = self.read_student_execute_result()
            return StudentProgressWithFinishedStage[ExecuteResult](
                stage=StudentProgressStage.EXECUTE,
                result=result,
            )
        assert False, stage

    def get_student_progress_of_stage_if_finished(self, stage: StudentProgressStage) \
            -> StudentProgressWithFinishedStage | None:  # stageがそもそも終了していなければNone
        # 生徒の指定されたステージが終了しているか確認して結果をProgressとして返す
        is_finished = self.is_student_stage_finished(
            stage=stage,
        )
        if not is_finished:
            return None
        return self.get_student_stage_result(
            stage=stage,
        )

    def get_student_progress(self) -> AbstractStudentProgress:
        # 生徒の現時点で終了したところまでのProgressを返す
        stages = StudentProgressStage.list_stages()

        consecutive_finish_count = 0
        for i, stage in enumerate(stages):
            if self.is_student_stage_finished(
                    stage=stage,
            ):
                consecutive_finish_count += 1
            else:
                break

        if consecutive_finish_count == 0:
            return StudentProgressUnstarted()
        else:
            return self.get_student_stage_result(
                stage=stages[consecutive_finish_count - 1],
            )

    def determine_student_next_stage_with_result(self, ) -> StudentProgressStage | None:
        progress = self.get_student_progress()
        expected_next_stage = progress.get_expected_next_stage()  # None if all stages are finished

        # レポートフォルダのハッシュをとって変更が検出されたときはステージをBUILDに巻き戻す
        if expected_next_stage is None or expected_next_stage > StudentProgressStage.BUILD:
            result = self.read_student_build_result()
            h = self._project_io.calculate_student_submission_folder_hash(
                student_id=self._student_id,
            )
            if not result.has_same_hash(h):
                self._logger.info(f"Changes are detected in submission folder: {self._student_id}")
                return StudentProgressStage.BUILD

        # コンパイルが失敗している場合はステージをBUILDに巻き戻す
        # TODO: COMPILEとBUILDのデータフォルダを分離する
        #       COMPILEステージはBUILDとフォルダを共有するためBUILDまで巻き戻す
        if not progress.is_success() \
                and progress.get_finished_stage() == StudentProgressStage.COMPILE:
            self._logger.info(f"Revert to build stage due to compile failure: {self._student_id}")
            return StudentProgressStage.BUILD

        # テストケースが変更されたときはステージをEXECUTEに巻き戻す
        if expected_next_stage is None or expected_next_stage > StudentProgressStage.EXECUTE:
            result = self.read_student_execute_result()
            if not result.has_same_hash_of_testcase_execute_config(
                    self._testcase_io.read_testcase_execute_config_mapping(),
            ):
                self._logger.info(f"Changes are detected in testcase: {self._student_id}")
                return StudentProgressStage.EXECUTE

        return expected_next_stage


class ProgressIO:
    # 生徒のステージ進捗に関するデータの読み書き（セッション管理を提供）
    # TODO: Unit of Workの導入

    _logger = create_logger()

    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
            project_io: ProjectIO,
            testcase_io: TestCaseIO,
    ):
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io
        self._project_io = project_io
        self._testcase_io = testcase_io
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
            project_io=self._project_io,
            testcase_io=self._testcase_io,
            student_id=student_id,
            lock_delegate=lambda: self.__begin_session_for_student(student_id),
            unlock_delegate=lambda: self.__end_session_for_student(student_id),
        )
