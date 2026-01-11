import json
from datetime import datetime

from shared.domain.entity.testcase import TestCaseConfigEntity
from shared.domain.interface.repository import ITestCaseRepository
from shared.domain.value.execute_config import TestCaseExecuteConfig
from shared.domain.value.identifier import TestCaseID
from shared.domain.value.test_config import TestCaseTestConfig
from shared.infra.system.project_database import ProjectDatabaseIO


class _TestCaseHelper:
    """TestCase設定テーブル用Helper"""

    @classmethod
    def upsert(
            cls,
            cursor,
            testcase_id: TestCaseID,
            execute_config_json: str,
            test_config_json: str,
    ) -> None:
        now = datetime.now()
        cursor.execute(
            """
            INSERT INTO testcase_config
            (testcase_id, execute_config_json, test_config_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(testcase_id) DO UPDATE SET
                execute_config_json = excluded.execute_config_json,
                test_config_json = excluded.test_config_json,
                updated_at = excluded.updated_at
            """,
            (
                str(testcase_id),
                execute_config_json,
                test_config_json,
                now,
                now,
            ),
        )

    @classmethod
    def fetch(cls, cursor, testcase_id: TestCaseID) -> dict | None:
        cursor.execute(
            """
            SELECT testcase_id, execute_config_json, test_config_json
            FROM testcase_config
            WHERE testcase_id = ?
            """,
            (str(testcase_id),),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "testcase_id": row["testcase_id"],
            "execute_config_json": row["execute_config_json"],
            "test_config_json": row["test_config_json"],
        }

    @classmethod
    def fetch_all(cls, cursor) -> list[dict]:
        cursor.execute(
            """
            SELECT testcase_id, execute_config_json, test_config_json
            FROM testcase_config
            ORDER BY testcase_id
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "testcase_id": row["testcase_id"],
                "execute_config_json": row["execute_config_json"],
                "test_config_json": row["test_config_json"],
            }
            for row in rows
        ]

    @classmethod
    def exists(cls, cursor, testcase_id: TestCaseID) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM testcase_config
            WHERE testcase_id = ?
            """,
            (str(testcase_id),),
        )
        return cursor.fetchone() is not None

    @classmethod
    def delete(cls, cursor, testcase_id: TestCaseID) -> None:
        cursor.execute(
            """
            DELETE FROM testcase_config
            WHERE testcase_id = ?
            """,
            (str(testcase_id),),
        )


class TestCaseRepository(ITestCaseRepository):
    def __init__(
            self,
            *,
            project_database_io: ProjectDatabaseIO,
    ):
        self._project_database_io = project_database_io
        self._helper = _TestCaseHelper()

    def put(self, testcase_config: TestCaseConfigEntity) -> None:
        # データベースに保存
        execute_config_json = json.dumps(
            testcase_config.execute_config.to_json())
        test_config_json = json.dumps(testcase_config.test_config.to_json())

        with self._project_database_io.connect() as con:
            cur = con.cursor()
            self._helper.upsert(
                cur,
                testcase_config.testcase_id,
                execute_config_json,
                test_config_json,
            )
            con.commit()

    def get(self, testcase_id: TestCaseID) -> TestCaseConfigEntity:
        # データベースから取得
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            row = self._helper.fetch(cur, testcase_id)

        if row is None:
            raise FileNotFoundError(
                f"TestCase config not found: {testcase_id}")

        # デシリアライズ
        execute_config = TestCaseExecuteConfig.from_json(
            json.loads(row["execute_config_json"])
        )
        test_config = TestCaseTestConfig.from_json(
            json.loads(row["test_config_json"])
        )

        # エンティティを作成して返却
        return TestCaseConfigEntity(
            testcase_id=testcase_id,
            execute_config=execute_config,
            test_config=test_config,
        )

    def list_all(self) -> list[TestCaseConfigEntity]:
        # データベースから全件取得
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            rows = self._helper.fetch_all(cur)

        # デシリアライズしてエンティティのリストを作成
        entities: list[TestCaseConfigEntity] = []
        for row in rows:
            execute_config = TestCaseExecuteConfig.from_json(
                json.loads(row["execute_config_json"])
            )
            test_config = TestCaseTestConfig.from_json(
                json.loads(row["test_config_json"])
            )
            entities.append(
                TestCaseConfigEntity(
                    testcase_id=TestCaseID(row["testcase_id"]),
                    execute_config=execute_config,
                    test_config=test_config,
                )
            )
        return entities

    def exists(self, testcase_id: TestCaseID) -> bool:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            return self._helper.exists(cur, testcase_id)

    def delete(self, testcase_id: TestCaseID) -> None:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            self._helper.delete(cur, testcase_id)
            con.commit()
