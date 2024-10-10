from domain.models.student_stage_result import *
from domain.models.values import StudentID, TestCaseID
from files.core.current_project import CurrentProjectCoreIO
from files.path_providers.project_dynamic import StudentStageResultPathProvider
from transaction import transactional_with


class BuildStudentStageResultRepository:
    def __init__(
            self,
            *,
            student_stage_result_path_provider: StudentStageResultPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_stage_result_path_provider = student_stage_result_path_provider
        self._current_project_core_io = current_project_core_io

    @classmethod
    def __get_type_name_of_result_type(
            cls,
            result_type: type[BuildStudentStageResultType],
    ) -> str:
        return result_type.__name__

    @classmethod
    def __get_result_type_from_type_name(
            cls,
            result_type_name: str,
    ) -> type[BuildStudentStageResultType]:
        if result_type_name \
                == cls.__get_type_name_of_result_type(BuildSuccessStudentStageResult):
            return BuildSuccessStudentStageResult
        elif result_type_name \
                == cls.__get_type_name_of_result_type(BuildFailureStudentStageResult):
            return BuildFailureStudentStageResult
        else:
            assert False, result_type_name

    @transactional_with("student_id")
    def put(
            self,
            student_id: StudentID,
            result: BuildStudentStageResultType,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.build_result_json_fullpath(student_id)
        )
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)

        self._current_project_core_io.write_json(
            json_fullpath=json_fullpath,
            body={
                "__type__": self.__get_type_name_of_result_type(type(result)),
                **result.to_json(),
            },
        )

    @transactional_with("student_id")
    def exists(
            self,
            student_id: StudentID,
    ) -> bool:
        json_fullpath = (
            self._student_stage_result_path_provider.build_result_json_fullpath(student_id)
        )
        return json_fullpath.exists()

    @transactional_with("student_id")
    def get(
            self,
            student_id: StudentID,
    ) -> BuildStudentStageResultType:
        json_fullpath = (
            self._student_stage_result_path_provider.build_result_json_fullpath(student_id)
        )
        if not json_fullpath.exists():
            raise ValueError(f"Build result for student {student_id} not found")

        body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
        type_name = body.pop("__type__")
        result_type = self.__get_result_type_from_type_name(type_name)
        return result_type.from_json(body)

    @transactional_with("student_id")
    def delete(
            self,
            student_id: StudentID,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.build_result_json_fullpath(student_id)
        )
        if not json_fullpath.exists():
            raise ValueError(f"Build result for student {student_id} not found")

        self._current_project_core_io.unlink(
            path=json_fullpath,
        )


class CompileStudentStageResultRepository:
    def __init__(
            self,
            *,
            student_stage_result_path_provider: StudentStageResultPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_stage_result_path_provider = student_stage_result_path_provider
        self._current_project_core_io = current_project_core_io

    @classmethod
    def __get_type_name_of_result_type(
            cls,
            result_type: type[CompileStudentStageResultType],
    ) -> str:
        return result_type.__name__

    @classmethod
    def __get_result_type_from_type_name(
            cls,
            result_type_name: str,
    ) -> type[CompileStudentStageResultType]:
        if result_type_name \
                == cls.__get_type_name_of_result_type(CompileSuccessStudentStageResult):
            return CompileSuccessStudentStageResult
        elif result_type_name \
                == cls.__get_type_name_of_result_type(CompileFailureStudentStageResult):
            return CompileFailureStudentStageResult
        else:
            assert False, result_type_name

    @transactional_with("student_id")
    def put(
            self,
            student_id: StudentID,
            result: CompileStudentStageResultType,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.compile_result_json_fullpath(student_id)
        )
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)

        self._current_project_core_io.write_json(
            json_fullpath=json_fullpath,
            body={
                "__type__": self.__get_type_name_of_result_type(type(result)),
                **result.to_json(),
            },
        )

    @transactional_with("student_id")
    def exists(
            self,
            student_id: StudentID,
    ) -> bool:
        json_fullpath = (
            self._student_stage_result_path_provider.compile_result_json_fullpath(student_id)
        )
        return json_fullpath.exists()

    @transactional_with("student_id")
    def get(
            self,
            student_id: StudentID,
    ) -> CompileStudentStageResultType:
        json_fullpath = (
            self._student_stage_result_path_provider.compile_result_json_fullpath(student_id)
        )
        if not json_fullpath.exists():
            raise ValueError(f"Compile result for student {student_id} not found")

        body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
        type_name = body.pop("__type__")
        result_type = self.__get_result_type_from_type_name(type_name)
        return result_type.from_json(body)

    @transactional_with("student_id")
    def delete(
            self,
            student_id: StudentID,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.compile_result_json_fullpath(student_id)
        )
        if not json_fullpath.exists():
            raise ValueError(f"Compile result for student {student_id} not found")

        self._current_project_core_io.unlink(
            path=json_fullpath,
        )


class ExecuteStudentStageResultRepository:
    def __init__(
            self,
            *,
            student_stage_result_path_provider: StudentStageResultPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_stage_result_path_provider = student_stage_result_path_provider
        self._current_project_core_io = current_project_core_io

    @classmethod
    def __get_type_name_of_result_type(
            cls,
            result_type: type[ExecuteStudentStageResultType],
    ) -> str:
        return result_type.__name__

    @classmethod
    def __get_result_type_from_type_name(
            cls,
            result_type_name: str,
    ) -> type[ExecuteStudentStageResultType]:
        if result_type_name \
                == cls.__get_type_name_of_result_type(ExecuteSuccessStudentStageResult):
            return ExecuteSuccessStudentStageResult
        elif result_type_name \
                == cls.__get_type_name_of_result_type(ExecuteFailureStudentStageResult):
            return ExecuteFailureStudentStageResult
        else:
            assert False, result_type_name

    @transactional_with("student_id")
    def put(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
            result: ExecuteStudentStageResultType,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.execute_result_json_fullpath(
                student_id,
                testcase_id,
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

    @transactional_with("student_id")
    def exists(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> bool:
        json_fullpath = (
            self._student_stage_result_path_provider.execute_result_json_fullpath(
                student_id,
                testcase_id,
            )
        )
        return json_fullpath.exists()

    @transactional_with("student_id")
    def get(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> ExecuteStudentStageResultType:
        json_fullpath = (
            self._student_stage_result_path_provider.execute_result_json_fullpath(
                student_id,
                testcase_id,
            )
        )
        if not json_fullpath.exists():
            raise ValueError(f"Execute result for student {student_id} not found")

        body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
        type_name = body.pop("__type__")
        result_type = self.__get_result_type_from_type_name(type_name)
        return result_type.from_json(body)

    @transactional_with("student_id")
    def delete(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.execute_result_json_fullpath(
                student_id,
                testcase_id,
            )
        )
        if not json_fullpath.exists():
            raise ValueError(f"Execute result for student {student_id} not found")

        self._current_project_core_io.unlink(
            path=json_fullpath,
        )


class TestStudentStageResultRepository:
    def __init__(
            self,
            *,
            student_stage_result_path_provider: StudentStageResultPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_stage_result_path_provider = student_stage_result_path_provider
        self._current_project_core_io = current_project_core_io

    @classmethod
    def __get_type_name_of_result_type(
            cls,
            result_type: type[TestStudentStageResultType],
    ) -> str:
        return result_type.__name__

    @classmethod
    def __get_result_type_from_type_name(
            cls,
            result_type_name: str,
    ) -> type[TestStudentStageResultType]:
        if result_type_name \
                == cls.__get_type_name_of_result_type(TestSuccessStudentStageResult):
            return TestSuccessStudentStageResult
        elif result_type_name \
                == cls.__get_type_name_of_result_type(TestFailureStudentStageResult):
            return TestFailureStudentStageResult
        else:
            assert False, result_type_name

    @transactional_with("student_id")
    def put(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
            result: TestStudentStageResultType,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.test_result_json_fullpath(
                student_id,
                testcase_id,
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

    @transactional_with("student_id")
    def exists(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> bool:
        json_fullpath = (
            self._student_stage_result_path_provider.test_result_json_fullpath(
                student_id,
                testcase_id,
            )
        )
        return json_fullpath.exists()

    @transactional_with("student_id")
    def get(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> TestStudentStageResultType:
        json_fullpath = (
            self._student_stage_result_path_provider.test_result_json_fullpath(
                student_id,
                testcase_id,
            )
        )
        if not json_fullpath.exists():
            raise ValueError(f"Test result for student {student_id} not found")

        body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
        type_name = body.pop("__type__")
        result_type = self.__get_result_type_from_type_name(type_name)
        return result_type.from_json(body)

    @transactional_with("student_id")
    def delete(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.test_result_json_fullpath(
                student_id,
                testcase_id,
            )
        )
        if not json_fullpath.exists():
            raise ValueError(f"Test result for student {student_id} not found")

        self._current_project_core_io.unlink(
            path=json_fullpath,
        )

# class StudentStageResultRepository:
#     def __init__(
#             self,
#             *,
#             student_stage_result_path_provider: StudentStageResultPathProvider,
#     ):
#         self._student_stage_result_path_provider = student_stage_result_path_provider
#
#     def clear_build_data(self) -> None:
#         # 生徒のビルド用のプロジェクトデータを削除する
#         build_folder_fullpath = self._student_build_path_provider.base_folder_fullpath(
#             student_id=self._student_id,
#         )
#         if not build_folder_fullpath.exists():
#             return
#         return self._project_core_io.rmtree_folder(build_folder_fullpath)
#
#     def clear_execute_data(self) -> None:
#         # 生徒の実行用のプロジェクトデータを削除する
#         execute_base_folder_fullpath = self._student_execute_path_provider.base_folder_fullpath(
#             student_id=self._student_id,
#         )
#         if not execute_base_folder_fullpath.exists():
#             return
#         return self._project_core_io.rmtree_folder(execute_base_folder_fullpath)
#
#     def clear_test_data(self) -> None:
#         # 生徒のテスト用のプロジェクトデータを削除する
#         test_base_folder_fullpath = self._student_test_path_provider.base_folder_fullpath(
#             student_id=self._student_id,
#         )
#         if not test_base_folder_fullpath.exists():
#             return
#         return self._project_core_io.rmtree_folder(test_base_folder_fullpath)
#
#     def clear_to_start_stage(self, stage_to_be_started: StudentProgressStage) -> None:
#         # stageを含むstage以降の生徒のステージの進捗で生成されるプロジェクトデータを削除する
#         for stage in StudentProgressStage.list_stages():
#             if stage < stage_to_be_started:
#                 continue
#             if stage == StudentProgressStage.BUILD:
#                 self.clear_build_data()
#                 self.clear_execute_data()
#             elif stage == StudentProgressStage.COMPILE:
#                 # TODO: COMPILEとBUILDのデータフォルダを分離する
#                 #       COMPILEステージはBUILDとフォルダを共有するためクリアできない
#                 # 代わりにCOMPILEの結果が存在しないことを確認する
#                 assert not self.is_compile_finished(), self._student_id
#             elif stage == StudentProgressStage.EXECUTE:
#                 self.clear_execute_data()
#             elif stage == StudentProgressStage.TEST:
#                 self.clear_test_data()
#             else:
#                 assert False, stage
#
#     def get_mtime(self) -> datetime | None:
#         # 生徒のプロジェクトデータの最終更新日時を取得する
#         mtime_max = None
#         path_it = self._student_progress_path_provider.iter_student_dynamic_folder_fullpath(
#             student_id=self._student_id,
#         )
#         for folder_fullpath in path_it:
#             if not folder_fullpath.exists():
#                 continue
#             mtime = folder_fullpath.stat().st_mtime
#             if mtime_max is None or mtime > mtime_max:
#                 mtime_max = mtime
#         return mtime_max and datetime.fromtimestamp(mtime_max)
#
#     def write_build_result(self, result: BuildStudentStageResult) -> None:
#         # 生徒のビルド結果を永続化する
#         result_json_fullpath = self._student_progress_path_provider.build_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         self._project_core_io.write_json(
#             json_fullpath=result_json_fullpath,
#             body=result.to_json(),
#         )
#
#     def is_build_finished(self) -> bool:
#         # 生徒のビルドが終了したかどうかを確認する
#         result_json_fullpath = self._student_progress_path_provider.build_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         return result_json_fullpath.exists()
#
#     def read_build_result(self) -> BuildStudentStageResult:
#         # 生徒のビルド結果を読み込む
#         result_json_fullpath = self._student_progress_path_provider.build_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
#         body = self._project_core_io.read_json(
#             json_fullpath=result_json_fullpath,
#         )
#         assert body is not None, result_json_fullpath
#         return BuildStudentStageResult.from_json(body)
#
#     def write_compile_result(self, result: CompileStudentStageResult) -> None:
#         # 生徒のコンパイル結果を永続化する
#         result_json_fullpath = self._student_progress_path_provider.compile_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         self._project_core_io.write_json(
#             json_fullpath=result_json_fullpath,
#             body=result.to_json(),
#         )
#
#     def is_compile_finished(self) -> bool:
#         # 生徒のコンパイルが終了したかどうかを確認する
#         result_json_fullpath = self._student_progress_path_provider.compile_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         return result_json_fullpath.exists()
#
#     def read_compile_result(self) -> CompileStudentStageResult:
#         # 生徒のコンパイル結果を読み込む
#         result_json_fullpath = self._student_progress_path_provider.compile_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
#         body = self._project_core_io.read_json(
#             json_fullpath=result_json_fullpath,
#         )
#         assert body is not None, result_json_fullpath
#         return CompileStudentStageResult.from_json(body)
#
#     def write_execute_result(self, result: ExecuteStudentStageResult) -> None:
#         # 生徒の実行結果を永続化する
#         result_json_fullpath = self._student_progress_path_provider.execute_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         self._project_core_io.write_json(
#             json_fullpath=result_json_fullpath,
#             body=result.to_json(),
#         )
#
#     def is_execute_finished(self) -> bool:
#         # 生徒の実行が終了したかどうかを確認する
#         result_json_fullpath = self._student_progress_path_provider.execute_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         return result_json_fullpath.exists()
#
#     def read_execute_result(self) -> ExecuteStudentStageResult:
#         # 生徒の実行結果を読み込む
#         result_json_fullpath = self._student_progress_path_provider.execute_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
#         body = self._project_core_io.read_json(
#             json_fullpath=result_json_fullpath,
#         )
#         assert body is not None, result_json_fullpath
#         return ExecuteStudentStageResult.from_json(body)
#
#     def write_test_result(self, result: TestStudentStageResult) -> None:
#         # 生徒のテスト結果を永続化する
#         result_json_fullpath = self._student_progress_path_provider.test_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         self._project_core_io.write_json(
#             json_fullpath=result_json_fullpath,
#             body=result.to_json(),
#         )
#
#     def is_test_finished(self) -> bool:
#         # 生徒のテストが終了したかどうかを確認する
#         result_json_fullpath = self._student_progress_path_provider.test_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         return result_json_fullpath.exists()
#
#     def read_test_result(self) -> TestStudentStageResult:
#         # 生徒のテスト結果を読み込む
#         result_json_fullpath = self._student_progress_path_provider.test_result_json_fullpath(
#             student_id=self._student_id,
#         )
#         result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
#         body = self._project_core_io.read_json(
#             json_fullpath=result_json_fullpath,
#         )
#         assert body is not None, result_json_fullpath
#         return TestStudentStageResult.from_json(body)
#
#     def write_mark_data(self, mark: Mark):
#         json_fullpath = self._student_mark_path_provider.student_mark_data_json_fullpath(
#             student_id=self._student_id,
#         )
#         json_fullpath.parent.mkdir(parents=True, exist_ok=True)
#         self._project_core_io.write_json(
#             json_fullpath=json_fullpath,
#             body=mark.to_json(),
#         )
#
#     def read_mark_data(self) -> Mark:
#         json_fullpath = self._student_mark_path_provider.student_mark_data_json_fullpath(
#             student_id=self._student_id,
#         )
#         body = self._project_core_io.read_json(json_fullpath=json_fullpath)
#         return Mark.from_json(body)
#
#     def read_mark_data_or_create_default_if_absent(self) -> Mark:
#         try:
#             return self.read_mark_data()
#         except FileNotFoundError:
#             return Mark.create_default()
#
#     # ステージ系
#
#     def is_stage_finished(self, stage: StudentProgressStage) -> bool:
#         # 生徒の指定されたステージが終了しているかを返す
#         if stage == StudentProgressStage.BUILD:
#             return self.is_build_finished()
#         if stage == StudentProgressStage.COMPILE:
#             return self.is_compile_finished()
#         if stage == StudentProgressStage.EXECUTE:
#             return self.is_execute_finished()
#         if stage == StudentProgressStage.TEST:
#             return self.is_test_finished()
#         assert False, stage
#
#     def get_progress_of_stage(self, stage: StudentProgressStage) \
#             -> StudentProgressWithFinishedStage:
#         # 生徒の指定されたステージの結果を読み出してProgressとして返す
#         if stage == StudentProgressStage.BUILD:
#             result = self.read_build_result()
#             return StudentProgressWithFinishedStage[BuildStudentStageResult](
#                 stage=StudentProgressStage.BUILD,
#                 result=result,
#             )
#         if stage == StudentProgressStage.COMPILE:
#             result = self.read_compile_result()
#             return StudentProgressWithFinishedStage[CompileStudentStageResult](
#                 stage=StudentProgressStage.COMPILE,
#                 result=result,
#             )
#         if stage == StudentProgressStage.EXECUTE:
#             result = self.read_execute_result()
#             return StudentProgressWithFinishedStage[ExecuteStudentStageResult](
#                 stage=StudentProgressStage.EXECUTE,
#                 result=result,
#             )
#         if stage == StudentProgressStage.TEST:
#             result = self.read_test_result()
#             return StudentProgressWithFinishedStage[TestStudentStageResult](
#                 stage=StudentProgressStage.TEST,
#                 result=result,
#             )
#         assert False, stage
#
#     def get_progress_of_stage_if_finished(self, stage: StudentProgressStage) \
#             -> StudentProgressWithFinishedStage | None:  # stageがそもそも終了していなければNone
#         # 生徒の指定されたステージが終了しているか確認して結果をProgressとして返す
#         is_finished = self.is_stage_finished(
#             stage=stage,
#         )
#         if not is_finished:
#             return None
#         return self.get_progress_of_stage(
#             stage=stage,
#         )
#
#     def get_current_progress(self) -> AbstractStudentProgress:
#         # 生徒の現時点で終了したところまでのProgressを返す
#         stages = StudentProgressStage.list_stages()
#
#         consecutive_finish_count = 0
#         for i, stage in enumerate(stages):
#             if self.is_stage_finished(
#                     stage=stage,
#             ):
#                 consecutive_finish_count += 1
#             else:
#                 break
#
#         if consecutive_finish_count == 0:
#             return StudentProgressUnstarted()
#         else:
#             return self.get_progress_of_stage(
#                 stage=stages[consecutive_finish_count - 1],
#             )

# class ProgressIO:
#     # 生徒のステージ進捗に関するデータの読み書き（セッション管理を提供）
#     # TODO: Unit of Workの導入
#
#     _logger = create_logger()
#
#     def __init__(
#             self,
#             *,
#             project_path_provider: ProjectPathProvider,
#             student_progress_path_provider: StudentProgressPathProvider,
#             student_build_path_provider: StudentBuildPathProvider,
#             student_compile_path_provider: StudentCompilePathProvider,
#             student_execute_path_provider: StudentExecutePathProvider,
#             student_test_path_provider: StudentTestPathProvider,
#             student_mark_path_provider: StudentMarkPathProvider,
#             project_core_io: ProjectCoreIO,
#             project_io: ProjectIO,
#             testcase_io: TestCaseIO,
#     ):
#         self._project_path_provider = project_path_provider
#         self._student_progress_path_provider = student_progress_path_provider
#         self._student_build_path_provider = student_build_path_provider
#         self._student_compile_path_provider = student_compile_path_provider
#         self._student_execute_path_provider = student_execute_path_provider
#         self._student_test_path_provider = student_test_path_provider
#         self._student_mark_path_provider = student_mark_path_provider
#         self._project_core_io = project_core_io
#         self._project_io = project_io
#         self._testcase_io = testcase_io
#         self._lock_global: QMutex = QMutex()
#         self._lock_student: dict[StudentID, QMutex] = {}
#
#     def __get_lock_for_student(self, student_id: StudentID) -> QMutex:
#         self._lock_global.lock()
#         if student_id not in self._lock_student:
#             self._lock_student[student_id] = QMutex()
#         lock = self._lock_student[student_id]
#         self._lock_global.unlock()
#         return lock
#
#     def __begin_session_for_student(self, student_id: StudentID) -> None:
#         lock = self.__get_lock_for_student(student_id)
#         lock.lock()
#
#     def __end_session_for_student(self, student_id: StudentID) -> None:
#         lock = self.__get_lock_for_student(student_id)
#         lock.unlock()
#
#     def with_student(self, student_id: StudentID) -> ProgressIOWithContext:
#         return ProgressIOWithContext(
#             student_progress_path_provider=self._student_progress_path_provider,
#             student_build_path_provider=self._student_build_path_provider,
#             student_compile_path_provider=self._student_compile_path_provider,
#             student_execute_path_provider=self._student_execute_path_provider,
#             student_test_path_provider=self._student_test_path_provider,
#             student_mark_path_provider=self._student_mark_path_provider,
#             project_core_io=self._project_core_io,
#             project_io=self._project_io,
#             testcase_io=self._testcase_io,
#             student_id=student_id,
#             lock_delegate=lambda: self.__begin_session_for_student(student_id),
#             unlock_delegate=lambda: self.__end_session_for_student(student_id),
#         )
