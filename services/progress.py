from domain.models.stages import AbstractStage
from domain.models.student_stage_result import ExecuteStudentStageResult, TestStudentStageResult
from domain.models.values import StudentID
from infra.project import ProjectIO
from infra.repositories.student_stage_result import ProgressIO, StudentStageResultRepository
from infra.testcase_config import TestCaseIO
from transaction import transactional


class ProgressService:  # TODO: StudentProgressService?
    def __init__(self, project_io: ProjectIO, testcase_io: TestCaseIO, progress_io: ProgressIO):
        self._project_io = project_io
        self._testcase_io = testcase_io
        self._progress_io = progress_io

    @transactional
    def is_execute_config_changed(self, student_id: StudentID) -> bool:
        # テストケースIDが全て一致するかどうか
        testcase_ids_config = self._testcase_io.list_ids()
        with self._progress_io.with_student(student_id) as student_progress_io:
            execute_result = \
                student_progress_io.get_progress_of_stage(AbstractStage.EXECUTE).get_result()
            assert isinstance(execute_result, ExecuteStudentStageResult), execute_result
        testcase_ids_result = execute_result.testcase_results.keys()
        if set(testcase_ids_config) != set(testcase_ids_result):
            return True

        # テストケースの中身が一致するかどうか
        testcase_ids = testcase_ids_config
        for testcase_id in testcase_ids:
            mtime_config = self._testcase_io.get_execute_config_mtime(testcase_id)
            mtime_result = execute_result.testcase_results[testcase_id].execute_config_mtime
            if mtime_config != mtime_result:
                return True

        return False

    def is_test_config_changed(self, student_id: StudentID) -> bool:
        # テストケースIDが全て一致するかどうか
        testcase_ids_config = self._testcase_io.list_ids()
        with self._progress_io.with_student(student_id) as student_progress_io:
            test_result = student_progress_io.read_test_result()
            assert isinstance(test_result, TestStudentStageResult), test_result
        testcase_ids_test_config = test_result.testcase_results.keys()
        if set(testcase_ids_config) != set(testcase_ids_test_config):
            return True

        # テスト構成が一致するかどうか
        testcase_ids = testcase_ids_config
        for testcase_id in testcase_ids:
            mtime_config = self._testcase_io.read_execute_config(testcase_id)
            mtime_result = test_result.testcase_results[testcase_id].test_config_mtime
            if mtime_config != mtime_result:
                return True

        return False

    @transactional
    def determine_next_stage_with_result_and_get_reason(
            self,
            student_progress_io: StudentStageResultRepository,  # TODO: [!] 変な引数 コンテキストの導入
    ) -> tuple[AbstractStage | None, str | None]:
        # noinspection PyProtectedMember
        student_id = student_progress_io._student_id  # TODO: [!] student_idはどこからとるべき？引数で受け取る？セッションを管理して依存注入？

        progress = student_progress_io.get_current_progress()  ## => StudentProgressGetCurrentService
        expected_next_stage = progress.get_expected_next_stage()

        # すべてのステージが終了したか次のステージにBUILD以降が予期されているとき
        if expected_next_stage is None or expected_next_stage > AbstractStage.BUILD:
            # レポートフォルダのハッシュをとって変更が検出されたときはステージをBUILDに巻き戻す
            result = student_progress_io.read_build_result()
            h = self._project_io.calculate_student_submission_folder_hash(
                student_id=student_id,
            )
            if not result.has_submission_folder_hash_of(h):
                return AbstractStage.BUILD, "提出フォルダに変更が検出された"

        # コンパイルが失敗している場合はステージをBUILDに巻き戻す
        # TODO: COMPILEとBUILDのデータフォルダを分離する
        #       COMPILEステージはBUILDとフォルダを共有するためBUILDまで巻き戻す必要がある
        if not progress.is_success() \
                and progress.get_finished_stage() == AbstractStage.COMPILE:
            return AbstractStage.BUILD, "コンパイルに失敗した"

        # すべてのステージが終了したか次のステージにEXECUTE以降が予期されているとき
        if expected_next_stage is None or expected_next_stage > AbstractStage.EXECUTE:
            # 実行構成が変更されたときはステージをEXECUTEに巻き戻す
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            # FIXME: すでに生徒のセッションを張っているのでis_execute_config_changed()のなかでデッドロック
            if self.is_execute_config_changed(
                    student_id=student_id,
            ):
                return AbstractStage.EXECUTE, "実行構成が変更された"

        # すべてのステージが終了したか次のステージにTEST以降が予期されているとき
        if expected_next_stage is None or expected_next_stage > AbstractStage.TEST:
            # テスト構成が変更されたときはステージをTESTに巻き戻す
            if self.is_test_config_changed(
                    student_id=student_id,
            ):
                return AbstractStage.TEST, "テスト構成が変更された"

        return (
            expected_next_stage,  # すべてのステージが終了していたらNone
            None,  # 巻き戻っていないのでNone
        )

    def determine_next_stage_with_result(
            self,
            student_progress_io: StudentStageResultRepository,  # TODO: [!] 変な引数 コンテキストの��入
    ) -> AbstractStage | None:
        expected_next_stage, _ \
            = self.determine_next_stage_with_result_and_get_reason(student_progress_io)
        return expected_next_stage


    def clear_student_to_start_stage(
            self, student_id: StudentID,
            stage: AbstractStage,
    ) -> None:
        with self._progress_io.with_student(student_id) as student_progress_io:
            student_progress_io.clear_to_start_stage(
                stage_to_be_started=stage,
            )

    def clear_all_stages_of_student(self, student_id: StudentID) -> None:
        self.clear_student_to_start_stage(
            student_id=student_id,
            stage=AbstractStage.get_first_stage(),
        )

