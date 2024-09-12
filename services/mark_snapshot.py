import copy

from domain.models.result_execute import ExecuteResult
from domain.models.result_test import TestResult
from domain.models.stages import StudentProgressStage
from domain.models.values import StudentID
from dto.mark import StudentMarkSnapshot, ProjectMarkSnapshot
from files.progress import ProgressIO
from files.project import ProjectIO
from files.testcase import TestCaseIO


class MarkSnapshotService:
    # 採点に必要なデータのスナップショットを作成する

    def __init__(
            self,
            *,
            project_io: ProjectIO,
            progress_io: ProgressIO,
            testcase_io: TestCaseIO,
    ):
        self._project_io = project_io
        self._progress_io = progress_io
        self._testcase_io = testcase_io

    def take_student_snapshot(self, student_id: StudentID) -> StudentMarkSnapshot:
        # スナップショットに必要な情報を取得
        with self._progress_io.with_student(student_id) as student_progress_io:
            # ステージの進捗を読み出す
            progress = student_progress_io.get_progress()
            # 失敗の理由を取得
            detailed_reason = progress.get_detailed_reason()
            # マークデータを取得
            mark = student_progress_io.read_mark_data_or_create_default_if_absent()
            # 実行結果を取得
            progress_of_execute = student_progress_io.get_progress_of_stage_if_finished(
                stage=StudentProgressStage.EXECUTE,
            )
            if progress_of_execute is None:
                execute_result = None
            else:
                execute_result = copy.deepcopy(progress_of_execute.get_result())
                assert isinstance(execute_result, ExecuteResult), execute_result
            # テスト結果を取得
            progress_of_test = student_progress_io.get_progress_of_stage_if_finished(
                stage=StudentProgressStage.TEST,
            )
            if progress_of_test is None:
                test_result = None
            else:
                test_result = copy.deepcopy(progress_of_test.get_result())
                assert isinstance(test_result, TestResult), test_result
            # 次のステージを取得
            # TODO: 何に使っているかを調べてその情報でスナップショットを生成する
            next_stage = student_progress_io.determine_next_stage_with_result()

        # スナップショットを生成
        return StudentMarkSnapshot(
            student=self._project_io.students[student_id],
            detailed_reason=detailed_reason,
            next_stage=next_stage,
            mark=mark,
            execute_result=copy.deepcopy(execute_result),
            test_result=copy.deepcopy(test_result),
        )

    def take_project_snapshot(self) -> ProjectMarkSnapshot:
        student_snapshot_mapping = {}
        for student in self._project_io.students:
            student_id = student.student_id
            snapshot = self.take_student_snapshot(student_id)
            student_snapshot_mapping[student_id] = snapshot

        testcase_test_config_mapping = self._testcase_io.read_testcase_test_config_mapping()

        return ProjectMarkSnapshot(
            student_snapshot_mapping=student_snapshot_mapping,
            testcase_test_config_mapping=testcase_test_config_mapping,
        )
