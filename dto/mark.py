from dataclasses import dataclass

from domain.models.mark import Mark
from domain.models.result_execute import ExecuteResult
from domain.models.result_test import TestResult
from domain.models.stages import StudentProgressStage
from domain.models.student_master import Student
from domain.models.testcase import TestCaseTestConfig
from domain.models.values import StudentID, TestCaseID


@dataclass(slots=True)
class StudentMarkSnapshot:
    # 生徒の採点に必要なデータのスナップショット
    student: Student
    detailed_reason: str | None  # 生徒のステージが中断されたdetailed_reason
    next_stage: StudentProgressStage | None  # 生徒の次に実行されるべきステージ
    mark: Mark
    execute_result: ExecuteResult | None
    test_result: TestResult

    def __post_init__(self):
        # 結果データの整合性をチェック
        if self.execute_result is not None:
            assert self.detailed_reason is None
        if self.test_result is not None:
            assert self.detailed_reason is None

    @property
    def is_markable(self) -> bool:
        return self.detailed_reason is None

    @property
    def is_rerun_required(self) -> bool:
        # 現状ではステージが全て完了しているのに次に実行されるべきステージが存在する場合にTrue
        return self.is_markable and self.next_stage is not None


@dataclass(slots=True)
class ProjectMarkSnapshot:
    # プロジェクト全体の採点に必要なデータのスナップショット
    student_snapshot_mapping: dict[StudentID, StudentMarkSnapshot]
    testcase_test_config_mapping: dict[TestCaseID, TestCaseTestConfig]

    def _list_student_ids(self) -> list[StudentID]:
        return list(self.student_snapshot_mapping.keys())

    def get_first_student_id(self) -> StudentID:
        return self._list_student_ids()[0]

    def _list_testcase_ids(self) -> list[TestCaseID]:
        return list(self.testcase_test_config_mapping.keys())

    def get_first_testcase_id(self) -> TestCaseID:
        return self._list_testcase_ids()[0]
