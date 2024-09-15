from dataclasses import dataclass

from domain.models.mark import Mark
from domain.models.result_execute import TestCaseExecuteResultMapping
from domain.models.result_test import TestCaseTestResultMapping
from domain.models.student_master import Student
from domain.models.values import StudentID, TestCaseID
from dto.result_pair import TestCaseExecuteAndTestResultPairMapping
from dto.testcase_config import TestCaseConfigMapping


class AbstractStudentSnapshot:
    def __init__(
            self,
            student: Student,
            mark: Mark,
    ):
        self._student = student
        self._mark = mark

    @property
    def student(self):
        return self._student

    @property
    def student_id(self) -> StudentID:  # TODO: 使用回数が少ない場合は削除してself.student.student_idにリファクタリング
        return self._student.student_id

    @property
    def mark(self) -> Mark:
        return self._mark

    @property
    def is_ready(self) -> bool:
        raise NotImplementedError()

    @property
    def preparation_state_title(self) -> str:  # 準備完了している場合は空文字を返す
        raise NotImplementedError()

    @property
    def preparation_state_detailed_text(self) -> str:
        raise NotImplementedError()

    @property
    def preparation_state_color(self) -> str | None:  # 採点状況によるイメージ色
        raise NotImplementedError()

    @property
    def mark_state_color(self) -> str:  # 採点準備状態によるイメージ色（採点状況より優先）
        if self._mark.is_marked:
            return "lightgreen"
        else:
            return "lightgray"

    @property
    def indicator_color(self) -> str:  # 全体のイメージ色
        return self.preparation_state_color or self.mark_state_color

    @property
    def testcase_execute_and_test_results(self) -> TestCaseExecuteAndTestResultPairMapping | None:
        raise NotImplementedError()

    @property
    def testcase_test_results(self) -> TestCaseTestResultMapping | None:
        if self.testcase_execute_and_test_results is None:
            return None
        return TestCaseTestResultMapping({
            testcase_id: test_result_pair.test_result
            for testcase_id, test_result_pair in self.testcase_execute_and_test_results.items()
        })


class StudentSnapshotReady(AbstractStudentSnapshot):
    # 採点可能

    def __init__(
            self,
            *,
            student: Student,
            mark: Mark,
            execute_and_test_results: TestCaseExecuteAndTestResultPairMapping,
    ):
        super().__init__(student=student, mark=mark)
        self._execute_and_test_results = execute_and_test_results

    @property
    def is_ready(self) -> bool:
        return True

    @property
    def preparation_state_title(self) -> str:
        return ""

    @property
    def preparation_state_detailed_text(self) -> str:
        return "テストが完了しました"

    @property
    def preparation_state_color(self) -> str | None:
        return None

    @property
    def testcase_execute_and_test_results(self) -> TestCaseExecuteAndTestResultPairMapping | None:
        return self._execute_and_test_results


class StudentSnapshotRerunRequired(AbstractStudentSnapshot):
    # 再実行が必要

    def __init__(
            self,
            *,
            student: Student,
            mark: Mark,
    ):
        super().__init__(student=student, mark=mark)

    @property
    def is_ready(self) -> bool:
        return False

    @property
    def preparation_state_title(self) -> str:
        return "再実行が必要"

    @property
    def preparation_state_detailed_text(self) -> str:
        return "処理の再実行が必要です"

    @property
    def preparation_state_color(self) -> str | None:
        return "orange"

    @property
    def testcase_execute_and_test_results(self) -> TestCaseExecuteResultMapping | None:
        return None


class StudentSnapshotStagesUnfinished(AbstractStudentSnapshot):
    # 処理が未完了

    def __init__(
            self,
            *,
            student: Student,
            mark: Mark,
    ):
        super().__init__(student=student, mark=mark)

    @property
    def is_ready(self) -> bool:
        return False

    @property
    def preparation_state_title(self) -> str:
        return "未完了"

    @property
    def preparation_state_detailed_text(self) -> str:
        return "まだ処理が完了していません"

    @property
    def preparation_state_color(self) -> str | None:
        return "yellow"

    @property
    def testcase_execute_and_test_results(self) -> TestCaseExecuteResultMapping | None:
        return None


class StudentSnapshotStageFinishedWithError(AbstractStudentSnapshot):
    # 処理が完了したがエラーが発生

    def __init__(
            self,
            *,
            student: Student,
            mark: Mark,
            detailed_reason: str,
    ):
        super().__init__(student=student, mark=mark)
        self._detailed_reason = detailed_reason

    @property
    def is_ready(self) -> bool:
        return False

    @property
    def preparation_state_title(self) -> str:
        return "エラー"

    @property
    def preparation_state_detailed_text(self) -> str:
        return "処理中にエラーが発生しました：" + self._detailed_reason

    @property
    def preparation_state_color(self) -> str | None:
        return "red"

    @property
    def testcase_execute_and_test_results(self) -> TestCaseExecuteResultMapping | None:
        return None


class StudentMarkSnapshotMapping(dict[StudentID, AbstractStudentSnapshot]):
    pass


@dataclass(slots=True)
class ProjectSnapshot:
    # プロジェクト全体の採点に必要なデータのスナップショット
    student_snapshots: StudentMarkSnapshotMapping
    testcases: TestCaseConfigMapping

    def _list_student_ids(self) -> list[StudentID]:
        return list(self.student_snapshots.keys())

    def get_first_student_id(self) -> StudentID | None:
        if self._list_student_ids():
            return self._list_student_ids()[0]
        else:
            return None

    def _list_testcase_ids(self) -> list[TestCaseID]:
        return list(self.testcases.keys())

    def get_first_testcase_id(self) -> TestCaseID | None:
        if self._list_testcase_ids():
            return self._list_testcase_ids()[0]
        else:
            return None
