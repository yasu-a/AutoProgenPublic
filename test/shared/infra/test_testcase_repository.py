from datetime import datetime
from pathlib import Path

import pytest

from shared.domain.value.identifier import TestCaseID, FileID, SpecialFileType
from shared.domain.value.input_file import InputFile, InputFileCollection
from shared.domain.value.expected_output_file import ExpectedOutputFile, ExpectedOutputFileCollection
from shared.domain.value.execute_config_options import ExecuteConfigOptions
from shared.domain.value.test_config_options import TestConfigOptions
from shared.domain.value.execute_config import TestCaseExecuteConfig
from shared.domain.value.test_config import TestCaseTestConfig
from shared.domain.entity.testcase import TestCaseConfigEntity
from shared.infra.gateway.database_initialize_gateway import DatabaseInitializeGateway
from shared.infra.repository.testcase import TestCaseRepository
from shared.infra.system.project_database import ProjectDatabaseIO


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo(tmp_path: Path) -> TestCaseRepository:
    db_path = tmp_path / "project.sqlite3"
    db_io = ProjectDatabaseIO(database_fullpath=db_path)
    
    # スキーマ初期化
    DatabaseInitializeGateway(db_io).initialize()
    
    return TestCaseRepository(project_database_io=db_io)


@pytest.fixture
def entity_a() -> TestCaseConfigEntity:
    """テストケースA: input.txt, timeout=1.0, ignore_case=False"""
    return TestCaseConfigEntity(
        testcase_id=TestCaseID("testcase_a"),
        execute_config=TestCaseExecuteConfig(
            input_file_collection=InputFileCollection([
                InputFile(file_id=FileID("input.txt"), content=b"hello"),
            ]),
            options=ExecuteConfigOptions(timeout=1.0),
            mtime=datetime(2024, 1, 1, 10, 0, 0),
        ),
        test_config=TestCaseTestConfig(
            expected_output_file_collection=ExpectedOutputFileCollection([
                ExpectedOutputFile.create_default(FileID("output.txt")),
            ]),
            options=TestConfigOptions(ignore_case=False),
            mtime=datetime(2024, 1, 1, 11, 0, 0),
        ),
    )


@pytest.fixture
def entity_b() -> TestCaseConfigEntity:
    """テストケースB: stdin, timeout=2.5, ignore_case=True"""
    return TestCaseConfigEntity(
        testcase_id=TestCaseID("testcase_b"),
        execute_config=TestCaseExecuteConfig(
            input_file_collection=InputFileCollection([
                InputFile(file_id=FileID(SpecialFileType.STDIN), content=b"world"),
            ]),
            options=ExecuteConfigOptions(timeout=2.5),
            mtime=datetime(2024, 2, 1, 12, 0, 0),
        ),
        test_config=TestCaseTestConfig(
            expected_output_file_collection=ExpectedOutputFileCollection([
                ExpectedOutputFile.create_default(FileID(SpecialFileType.STDOUT)),
            ]),
            options=TestConfigOptions(ignore_case=True),
            mtime=datetime(2024, 2, 1, 13, 0, 0),
        ),
    )


@pytest.fixture
def entity_c() -> TestCaseConfigEntity:
    """テストケースC: data/input.dat, timeout=5.0, ignore_case=False"""
    return TestCaseConfigEntity(
        testcase_id=TestCaseID("testcase_c"),
        execute_config=TestCaseExecuteConfig(
            input_file_collection=InputFileCollection([
                InputFile(file_id=FileID(Path("data/input.dat")), content=b"test data"),
            ]),
            options=ExecuteConfigOptions(timeout=5.0),
            mtime=datetime(2024, 3, 1, 14, 0, 0),
        ),
        test_config=TestCaseTestConfig(
            expected_output_file_collection=ExpectedOutputFileCollection([
                ExpectedOutputFile.create_default(FileID(Path("data/output.dat"))),
            ]),
            options=TestConfigOptions(ignore_case=False),
            mtime=datetime(2024, 3, 1, 15, 0, 0),
        ),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_put_and_get(
    repo: TestCaseRepository,
    entity_a: TestCaseConfigEntity,
) -> None:
    """put()したエンティティがget()で取得できる"""
    repo.put(entity_a)
    loaded = repo.get(entity_a.testcase_id)
    assert loaded == entity_a


def test_upsert_updates_entity(
    repo: TestCaseRepository,
    entity_a: TestCaseConfigEntity,
    entity_b: TestCaseConfigEntity,
) -> None:
    """同一IDでput()すると内容が更新される"""
    # 同一IDで異なる内容のエンティティを作成
    entity_a_updated = TestCaseConfigEntity(
        testcase_id=entity_a.testcase_id,  # 同じID
        execute_config=entity_b.execute_config,  # 異なる内容
        test_config=entity_b.test_config,  # 異なる内容
    )
    
    repo.put(entity_a)
    repo.put(entity_a_updated)
    
    loaded = repo.get(entity_a.testcase_id)

    assert isinstance(loaded, TestCaseConfigEntity)
    
    assert loaded.testcase_id == entity_a.testcase_id
    assert loaded.execute_config == entity_b.execute_config
    assert loaded.test_config == entity_b.test_config


def test_list_returns_all(
    repo: TestCaseRepository,
    entity_a: TestCaseConfigEntity,
    entity_b: TestCaseConfigEntity,
    entity_c: TestCaseConfigEntity,
) -> None:
    """list()は全エンティティをID昇順で返す"""
    repo.put(entity_c)
    repo.put(entity_a)
    repo.put(entity_b)
    
    all_entities = repo.list_all()
    ids = [str(e.testcase_id) for e in all_entities]
    assert ids == ["testcase_a", "testcase_b", "testcase_c"]


def test_exists(
    repo: TestCaseRepository,
    entity_a: TestCaseConfigEntity,
) -> None:
    """exists()は存在確認を正しく行う"""
    repo.put(entity_a)
    
    assert repo.exists(entity_a.testcase_id) is True
    assert repo.exists(TestCaseID("nonexistent")) is False


def test_delete(
    repo: TestCaseRepository,
    entity_a: TestCaseConfigEntity,
) -> None:
    """delete()後はexists()がFalse、get()はFileNotFoundErrorを送出"""
    repo.put(entity_a)
    repo.delete(entity_a.testcase_id)
    
    assert repo.exists(entity_a.testcase_id) is False
    with pytest.raises(FileNotFoundError):
        repo.get(entity_a.testcase_id)


def test_list_empty_when_no_data(
    repo: TestCaseRepository,
) -> None:
    """データがない場合list()は空リストを返す"""
    assert repo.list_all() == []


def test_multiple_entities_independence(
    repo: TestCaseRepository,
    entity_a: TestCaseConfigEntity,
    entity_b: TestCaseConfigEntity,
    entity_c: TestCaseConfigEntity,
) -> None:
    """複数エンティティが独立して管理される"""
    repo.put(entity_a)
    repo.put(entity_b)
    repo.put(entity_c)
    
    # それぞれ独立して取得できる
    assert repo.get(entity_a.testcase_id) == entity_a
    assert repo.get(entity_b.testcase_id) == entity_b
    assert repo.get(entity_c.testcase_id) == entity_c
    
    # 1つ削除しても他に影響しない
    repo.delete(entity_b.testcase_id)
    assert repo.exists(entity_a.testcase_id) is True
    assert repo.exists(entity_b.testcase_id) is False
    assert repo.exists(entity_c.testcase_id) is True
