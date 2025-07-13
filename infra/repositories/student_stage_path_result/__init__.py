from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.student_stage_path_result import StudentStagePathResult
from domain.models.student_stage_result import (
    AbstractStudentStageResult,
)
from domain.models.values import StudentID
from infra.io.project_database import ProjectDatabaseIO
from infra.lock.student import StudentLockServer
from utils.app_logging import create_logger
from ._abstract_stage_result_helper import _AbstractStageResultHelper
from ._build_result_helper import _BuildResultHelper
from ._compile_result_helper import _CompileResultHelper
from ._execute_result_helper import _ExecuteResultHelper
from ._result_timestamp_helper import _ResultTimestampHelper
from ._test_result_helper import _TestResultHelper


# プロジェクト内ステートフル:
#  - 各Helperが_create_table_if_not_existsをインスタンス生成時に実行するため
#  - student_lock_serverを保持するため
#  - timestamp_repo_helperがキャッシュを持つため
class StudentStagePathResultRepository:
    """
    StudentStagePathResultを集約単位として管理するリポジトリ
    既存の4つのテーブルを使用して、集約の一貫性を保証する
    """

    def __init__(
            self,
            *,
            project_database_io: ProjectDatabaseIO,
    ):
        self._project_database_io = project_database_io

        self._logger = create_logger()

        self._student_lock_server = StudentLockServer()

        # 各ステージタイプに対応するヘルパーを初期化
        self._helpers = {
            BuildStage: _BuildResultHelper(),
            CompileStage: _CompileResultHelper(),
            ExecuteStage: _ExecuteResultHelper(),
            TestStage: _TestResultHelper(),
        }

        # タイムスタンプ管理ヘルパーを初期化
        self._result_timestamp_helper = _ResultTimestampHelper(
            project_database_io=self._project_database_io,
        )

        self._create_tables_if_not_exists()

    def _create_tables_if_not_exists(self):
        """既存の4つのテーブルが存在することを確認"""
        with self._project_database_io.connect() as con:
            cur = con.cursor()

            # 各ヘルパーにテーブル作成を委譲
            for helper in self._helpers.values():
                helper.create_table_if_not_exists(cur)

            con.commit()

    def _find_helper(self, stage: AbstractStage) -> _AbstractStageResultHelper:
        """ステージに対応するヘルパーを取得"""
        for stage_type, helper in self._helpers.items():
            if isinstance(stage, stage_type):
                return helper
        raise ValueError(f"Unknown stage type: {type(stage)}")

    @contextmanager
    def __lock(self, student_id: StudentID):
        """生徒単位でのロックを提供"""
        self._student_lock_server[student_id].lock()
        try:
            yield
        finally:
            self._student_lock_server[student_id].unlock()

    def get(self, student_id: StudentID, stage_path: StagePath) -> StudentStagePathResult:
        """
        指定されたステージパスの結果を集約単位で取得
        既存の4つのテーブルから統合的に取得
        """
        with self.__lock(student_id):
            self._logger.info(f"get: {student_id}, {stage_path}")
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None] \
                    = OrderedDict()

                for stage in stage_path:
                    helper = self._find_helper(stage)
                    stage_result = helper.get_stage_result(cur, student_id, stage)
                    stage_results[stage] = stage_result

                return StudentStagePathResult(
                    student_id=student_id,
                    stage_results=stage_results,
                )

    def put(self, stage_path_result: StudentStagePathResult) -> None:
        """
        ステージパスの結果を集約単位で保存
        既存の4つのテーブルに統合的に保存
        """
        with self.__lock(stage_path_result.student_id):
            self._logger.info(
                f"put: {stage_path_result.student_id}, {stage_path_result.stage_path}")
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                for stage, stage_result in stage_path_result.iter_stage_results():
                    helper = self._find_helper(stage)
                    if stage_result is None:
                        helper.delete_stage_result(cur, stage_path_result.student_id, stage)
                    else:
                        helper.put_stage_result(cur, stage_result)

                # Update timestamp using the same cursor
                self._result_timestamp_helper.update(stage_path_result.student_id, cur)
                con.commit()

    def get_timestamp(self, student_id: StudentID) -> datetime | None:
        """
        指定された生徒IDの最終更新日時を取得します。
        記録がない場合は None を返します。
        """
        with self.__lock(student_id):
            self._logger.info(f"get_timestamp: {student_id}")
            # キャッシュにない場合のみデータベースにアクセス
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                return self._result_timestamp_helper.get(student_id, cur)
