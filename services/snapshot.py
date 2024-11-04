from dataclasses import dataclass

from domain.models.stages import AbstractStage
from domain.models.values import StudentID
from dto.result_pair import TestCaseExecuteAndTestResultPair, \
    TestCaseExecuteAndTestResultPairMapping
from usecases.dto.mark_view_data import MarkViewData, StudentSnapshotStagesUnfinished, \
    StudentSnapshotReady, StudentSnapshotRerunRequired, AbstractStudentSnapshot, \
    StudentSnapshotStageFinishedWithError, StudentMarkSnapshotMapping
from dto.testcase_config import TestCaseConfigMapping
from infra.project import ProjectIO
from infra.repositories.student import StudentRepository
from infra.repositories.student_stage_result import ProgressIO
from infra.testcase_config import TestCaseIO



class SnapshotService:
    # 採点に必要なデータのスナップショットを作成する

    def __init__(
            self,
            *,
            project_io: ProjectIO,
            progress_io: ProgressIO,
            testcase_io: TestCaseIO,
            student_repo: StudentRepository,
    ):
        self._project_io = project_io
        self._progress_io = progress_io
        self._testcase_io = testcase_io
        self._student_repo = student_repo

    def take_student_snapshot(self, student_id: StudentID) -> AbstractStudentSnapshot:
        # スナップショットに必要な情報を取得
        with self._progress_io.with_student(student_id) as student_progress_io:
            # マークデータを取得
            mark = student_progress_io.read_mark_data_or_create_default_if_absent()

            # 進捗から生成するスナップショットを分岐
            progress_of_last_stage = student_progress_io.get_progress_of_stage_if_finished(
                ## => StudentProgressGetIfFinishedService
                stage=AbstractStage.get_last_stage()
            )  ## => StudentProgressGetIfFinished
            if progress_of_last_stage is not None and progress_of_last_stage.is_success():
                # ↑ 最後のステージの進捗が存在する and それが成功しているとき
                expected_next_stage = student_progress_io.determine_next_stage_with_result()
                if expected_next_stage is None:  # 次のステージが存在しない（再実行の必要がないとき）
                    testcase_execute_results = student_progress_io.read_execute_result().testcase_results
                    testcase_test_results = student_progress_io.read_test_result().testcase_results
                    assert set(testcase_execute_results.keys()) == set(testcase_test_results), \
                        (set(testcase_execute_results.keys()), set(testcase_test_results.keys()))
                    return StudentSnapshotReady(
                        student=self._student_repo.get(student_id),
                        mark=mark,
                        execute_and_test_results=TestCaseExecuteAndTestResultPairMapping(
                            {
                                testcase_id: TestCaseExecuteAndTestResultPair(
                                    testcase_id=testcase_id,
                                    execute_result=testcase_execute_results[testcase_id],
                                    test_result=testcase_test_results[testcase_id],
                                ) for testcase_id in testcase_execute_results.keys()
                            },
                        )
                    )
                else:  # 再実行の必要があるとき
                    # FIXME: 成功したときしか再実行の判定をしていないので、BUILDエラー時にレポートフォルダを
                    #        編集しても「再実行の必要がある」ではなく「エラー」と表示される
                    return StudentSnapshotRerunRequired(  # TODO: なぜ再実行の必要があるか理由をつける
                        student=self._student_repo.get(student_id),
                        mark=mark,
                    )
            else:  # すべてのステージが完了していないとき
                progress = student_progress_io.get_current_progress()  ## => StudentProgressGetCurrentService
                detailed_reason = progress.get_detailed_reason()
                if detailed_reason is None:
                    return StudentSnapshotStagesUnfinished(
                        student=self._student_repo.get(student_id),
                        mark=mark,
                    )
                else:
                    return StudentSnapshotStageFinishedWithError(
                        student=self._student_repo.get(student_id),
                        mark=mark,
                        detailed_reason=detailed_reason,
                    )

    def take_project_snapshot(self) -> MarkViewData:
        return MarkViewData(
            student_snapshots=StudentMarkSnapshotMapping({
                student.student_id: self.take_student_snapshot(student.student_id)
                for student in self._student_repo.list()
            }),
            testcase_configs=TestCaseConfigMapping({
                testcase_id: self._testcase_io.read_config(testcase_id)
                for testcase_id in self._testcase_io.list_ids()
            }),
        )
