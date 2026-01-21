import pytest
from datetime import datetime
from pathlib import Path

from shared.domain.model.stage import Stage
from shared.domain.model.student_result import (
    BuildStageResultEntity,
    CompileStageResultEntity,
    ExecuteStageResultEntity,
    TestStageResultEntity,
)
from shared.domain.value.identifier import StudentID, TestCaseID

# --- Real Domain Objects ---
# ダミーではなく本物のクラスをインポートします
from shared.domain.entity.student import StudentEntity
from shared.domain.entity.testcase import TestCaseConfigEntity
from shared.domain.value.execute_config import TestCaseExecuteConfig
from shared.domain.value.test_config import TestCaseTestConfig
from shared.domain.value.execute_config_options import ExecuteConfigOptions
from shared.domain.value.test_config_options import TestConfigOptions
from shared.domain.value.input_file import InputFileCollection
from shared.domain.value.expected_output_file import ExpectedOutputFileCollection

from shared.infra.gateway.database_initialize_gateway import DatabaseInitializeGateway
from shared.infra.repository.student_stage_path_result import (
    StudentStageResultRepository,
)
from shared.infra.repository.student import StudentRepository
from shared.infra.repository.testcase import TestCaseRepository
from shared.infra.system.database import DatabaseManager


# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> Path:
    """一時 SQLite DB のパス"""
    return tmp_path / "test.sqlite3"


@pytest.fixture()
def project_database_io(tmp_db_path: Path) -> DatabaseManager:
    return DatabaseManager(db_path=tmp_db_path)


@pytest.fixture()
def init_db(project_database_io: DatabaseManager):
    """DBスキーマを初期化"""
    DatabaseInitializeGateway(project_database_io).initialize()


@pytest.fixture()
def student_repo(project_database_io: DatabaseManager) -> StudentRepository:
    return StudentRepository(project_database_io=project_database_io)


@pytest.fixture()
def testcase_repo(project_database_io: DatabaseManager) -> TestCaseRepository:
    return TestCaseRepository(project_database_io=project_database_io)


@pytest.fixture()
def result_repo(project_database_io: DatabaseManager) -> StudentStageResultRepository:
    return StudentStageResultRepository(project_database_io=project_database_io)


@pytest.fixture()
def sample_students() -> list[StudentEntity]:
    """テスト用の学生データを作成（本物のEntityを使用）"""
    # バリデーションルール(\d{2}[A-Z]\d{7}[A-Z])を満たすIDを使用
    return [
        StudentEntity(
            student_id=StudentID("22B1234567A"),
            name="Test User 1",
            name_en="Test User 1",
            email_address="test1@example.com",
            submitted_at=datetime.now(),
            num_submissions=1,
            submission_folder_name="22B1234567A_TestUser1"
        ),
        StudentEntity(
            student_id=StudentID("22B1234567B"),
            name="Test User 2",
            name_en="Test User 2",
            email_address="test2@example.com",
            submitted_at=datetime.now(),
            num_submissions=1,
            submission_folder_name="22B1234567B_TestUser2"
        ),
    ]


@pytest.fixture()
def sample_testcase_configs() -> list[TestCaseConfigEntity]:
    """テスト用のテストケース設定データを作成（本物のEntityを使用）"""
    
    # 実行設定の作成（デフォルト値を使用）
    execute_config = TestCaseExecuteConfig(
        input_file_collection=InputFileCollection(),
        options=ExecuteConfigOptions(timeout=10.0),
        mtime=datetime.now()
    )
    
    # テスト設定の作成（デフォルト値を使用）
    # ※ TestCaseTestConfigのコンストラクタ引数が不明な場合、適宜調整してください
    test_config = TestCaseTestConfig(
        expected_output_file_collection=ExpectedOutputFileCollection(),
        options=TestConfigOptions(ignore_case=False),
        mtime=datetime.now()
    )

    return [
        TestCaseConfigEntity(
            testcase_id=TestCaseID("T001"),
            execute_config=execute_config,
            test_config=test_config,
        ),
        TestCaseConfigEntity(
            testcase_id=TestCaseID("T002"),
            execute_config=execute_config,
            test_config=test_config,
        ),
    ]


@pytest.fixture()
def prepared_repo(
    init_db,
    student_repo: StudentRepository,
    testcase_repo: TestCaseRepository,
    result_repo: StudentStageResultRepository,
    sample_students: list[StudentEntity],
    sample_testcase_configs: list[TestCaseConfigEntity]
) -> StudentStageResultRepository:
    """
    親テーブル（Student, TestCase）にデータを挿入済みのリポジトリを返す
    """
    # 1. Studentテーブルへのデータ挿入
    if hasattr(student_repo, "create_all"):
        student_repo.create_all(sample_students)
    else:
        for s in sample_students:
            if hasattr(student_repo, "put"):
                student_repo.put(s)
            elif hasattr(student_repo, "create"):
                student_repo.create(s)

    # 2. TestCaseテーブルへのデータ挿入
    # 本物のEntityを使っているため、Repository内部での .to_json() 呼び出しなども正常に動作します
    for tc in sample_testcase_configs:
        if hasattr(testcase_repo, "put"):
            testcase_repo.put(tc)
        elif hasattr(testcase_repo, "create"):
            testcase_repo.create(tc)

    return result_repo


# --------------------------------------------------
# Helper
# --------------------------------------------------

def make_sample_result(student_id: StudentID,
                       stage: Stage,
                       testcase_id: TestCaseID | None,
                       success: bool):
    ts = datetime(2025, 1, 1, 0, 0, 0)  # 決定論的

    if stage is Stage.BUILD:
        return BuildStageResultEntity(
            student_id=student_id,
            submission_folder_checksum=0xDEADBEEF if success else None,
            timestamp=ts,
            is_success=success,
            error_summary=None if success else "Build failed"
        )

    if stage is Stage.COMPILE:
        return CompileStageResultEntity(
            student_id=student_id,
            output="gcc output" if success else "",
            timestamp=ts,
            is_success=success,
            error_summary=None if success else "Compile failed"
        )

    if stage is Stage.EXECUTE:
        return ExecuteStageResultEntity(
            student_id=student_id,
            testcase_id=testcase_id,
            execute_config_mtime=ts if success else None,
            output_file_collection=None,
            timestamp=ts,
            is_success=success,
            error_summary=None if success else "Execute failed"
        )

    if stage is Stage.TEST:
        return TestStageResultEntity(
            student_id=student_id,
            testcase_id=testcase_id,
            test_config_mtime=ts if success else None,
            test_result_output_file_collection=None,
            failure_reason=None if success else "Failure reason",
            timestamp=ts,
            is_success=success,
            error_summary=None if success else "Test failed"
        )

    raise ValueError(stage)


# --------------------------------------------------
# Parametrized test
# --------------------------------------------------

@pytest.mark.parametrize("stage", [Stage.BUILD, Stage.COMPILE, Stage.EXECUTE, Stage.TEST])
@pytest.mark.parametrize("success", [True, False])
def test_put_and_get(prepared_repo: StudentStageResultRepository,
                     sample_students,
                     sample_testcase_configs,
                     stage: Stage,
                     success: bool):
    # 用意した親データのIDを使用する
    student_id: StudentID = sample_students[0].student_id

    if stage in (Stage.EXECUTE, Stage.TEST):
        testcase_id = sample_testcase_configs[0].testcase_id
    else:
        testcase_id = None

    entity = make_sample_result(student_id, stage, testcase_id, success)

    # PUT/UPDATE
    prepared_repo.update(entity)

    # GET
    if stage is Stage.BUILD:
        loaded = prepared_repo.get_build_result(student_id)
    elif stage is Stage.COMPILE:
        loaded = prepared_repo.get_compile_result(student_id)
    elif stage is Stage.EXECUTE:
        loaded = prepared_repo.get_execute_result(student_id, testcase_id)
    elif stage is Stage.TEST:
        loaded = prepared_repo.get_test_result(student_id, testcase_id)
    else:
        pytest.fail("unknown stage")

    # 検証: 同一属性値
    assert loaded is not None, "Expected result but got None"
    assert loaded.student_id == entity.student_id
    assert loaded.is_success == entity.is_success
    assert loaded.timestamp == entity.timestamp

    # ステージ固有フィールドのチェック
    if stage is Stage.BUILD:
        assert loaded.submission_folder_checksum == entity.submission_folder_checksum
    elif stage is Stage.COMPILE:
        assert loaded.output == entity.output
    elif stage is Stage.EXECUTE:
        assert loaded.execute_config_mtime == entity.execute_config_mtime
    elif stage is Stage.TEST:
        assert loaded.test_config_mtime == entity.test_config_mtime