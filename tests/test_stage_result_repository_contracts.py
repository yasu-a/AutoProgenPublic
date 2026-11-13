"""ステージ結果のSQLite保存・復元契約を固定する。"""

from datetime import datetime
from pathlib import Path

import pytest

from autoprogen.domain.model.expected_output_file import ExpectedOutputFile
from autoprogen.domain.model.output_file import OutputFile, OutputFileCollection
from autoprogen.domain.model.stage import BuildStage, CompileStage, ExecuteStage, TestStage as StageTest
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student_stage_result import (
    BuildFailureStudentStageResult,
    BuildSuccessStudentStageResult,
    CompileFailureStudentStageResult,
    CompileSuccessStudentStageResult,
    ExecuteFailureStudentStageResult,
    ExecuteSuccessStudentStageResult,
    TestFailureStudentStageResult as StageTestFailureResult,
    TestResultOutputFileCollection as StageTestOutputCollection,
    TestSuccessStudentStageResult as StageTestSuccessResult,
)
from autoprogen.domain.model.test_result_output_file_entry import (
    TestResultAbsentOutputFileEntry as AbsentOutputEntry,
)
from autoprogen.domain.model.value import FileID, StudentID, TestCaseID as CaseID
from autoprogen.infra.io.project_database import ProjectDatabaseIO
from autoprogen.infra.repository.student_stage_path_result import StudentStagePathResultRepository


STUDENT_A = StudentID("20A1234567B")
STUDENT_B = StudentID("20B1234567C")
CASE_A = CaseID("case-a")
CASE_B = CaseID("case-b")
EXECUTE_MTIME = datetime(2026, 11, 1, 12, 34, 56, 123456)
TEST_MTIME = datetime(2026, 11, 2, 14, 15, 16, 654321)


@pytest.fixture
def repository(tmp_path):
    """本番と同じRepositoryに、外部資源から独立したSQLiteを与える。"""
    database = ProjectDatabaseIO(database_path=tmp_path / "stage-results.sqlite3")
    with database.connect() as connection:
        # Repositoryが参照する外部キーの親テーブルだけを準備する。
        connection.execute("CREATE TABLE student (student_id TEXT PRIMARY KEY)")
        connection.executemany(
            "INSERT INTO student (student_id) VALUES (?)",
            [(str(STUDENT_A),), (str(STUDENT_B),)],
        )
        connection.commit()
    return StudentStagePathResultRepository(project_database_io=database), database


def _path(case_id: CaseID = CASE_A) -> StagePath:
    """指定テストケースの4ステージを含む経路を作る。"""
    return StagePath.list_paths([case_id])[0]


def _build_ok(student_id: StudentID = STUDENT_A, checksum: int = 123):
    """BUILD成功結果を作る。"""
    return BuildSuccessStudentStageResult.create_instance(
        student_id=student_id, submission_folder_checksum=checksum,
    )


def _compile_ok(student_id: StudentID = STUDENT_A, output: str = "MSVC: ok\n"):
    """COMPILE成功結果を作る。"""
    return CompileSuccessStudentStageResult.create_instance(
        student_id=student_id, output=output,
    )


def _execute_ok(student_id: StudentID = STUDENT_A, case_id: CaseID = CASE_A):
    """内容のある出力ファイルと時刻を持つEXECUTE成功結果を作る。"""
    outputs = OutputFileCollection([
        OutputFile(file_id=FileID.STDOUT, content="結果: 42\n"),
        OutputFile(file_id=FileID(Path("answer.txt")), content=b"line1\nline2\n"),
    ])
    return ExecuteSuccessStudentStageResult.create_instance(
        student_id=student_id,
        testcase_id=case_id,
        execute_config_mtime=EXECUTE_MTIME,
        output_file_collection=outputs,
    )


def _test_ok(student_id: StudentID = STUDENT_A, case_id: CaseID = CASE_A):
    """出力不足の判定を含むTEST成功結果を作る。"""
    missing = AbsentOutputEntry(
        file_id=FileID.STDOUT,
        expected=ExpectedOutputFile.create_default(FileID.STDOUT),
    )
    return StageTestSuccessResult.create_instance(
        student_id=student_id,
        testcase_id=case_id,
        test_config_mtime=TEST_MTIME,
        test_result_output_file_collection=StageTestOutputCollection([missing]),
    )


def _successes(case_id: CaseID = CASE_A):
    """ステージ順に各成功結果を返す。"""
    return (_build_ok(), _compile_ok(), _execute_ok(case_id=case_id), _test_ok(case_id=case_id))


def _save_through(repository, stage_index: int, case_id: CaseID = CASE_A):
    """指定ステージまでの成功結果を順に登録して保存する。"""
    aggregate = repository.get(STUDENT_A, _path(case_id))
    for result in _successes(case_id)[:stage_index + 1]:
        aggregate.put_result(result)
    repository.put(aggregate)
    return aggregate


@pytest.mark.parametrize("stage_index", range(4), ids=["build", "compile", "execute", "test"])
def test_success_roundtrip_for_each_stage(repository, stage_index: int) -> None:
    """全ステージの成功結果が型・値を保ってSQLiteから復元される。"""
    repo, _ = repository
    _save_through(repo, stage_index)
    loaded = repo.get(STUDENT_A, _path())
    original = _successes()[stage_index]
    stage = _path()[stage_index]
    restored = loaded.get_result(stage)
    assert type(restored) is type(original)
    assert restored.is_success is True
    assert restored.to_json() == original.to_json()


@pytest.mark.parametrize("stage_index", range(4), ids=["build", "compile", "execute", "test"])
def test_failure_roundtrip_for_each_stage(repository, stage_index: int) -> None:
    """全ステージの失敗理由とCOMPILEの生出力を文字単位で保存する。"""
    repo, _ = repository
    reason = "一行目の理由。\n二行目：詳細\n"
    failures = (
        BuildFailureStudentStageResult.create_instance(student_id=STUDENT_A, reason=reason),
        CompileFailureStudentStageResult.create_instance(
            student_id=STUDENT_A, reason=reason, output="compiler stdout\nwarning C1234\n",
        ),
        ExecuteFailureStudentStageResult.create_instance(
            student_id=STUDENT_A, testcase_id=CASE_A, reason=reason,
        ),
        StageTestFailureResult.create_instance(
            student_id=STUDENT_A, testcase_id=CASE_A, reason=reason,
        ),
    )
    aggregate = repo.get(STUDENT_A, _path())
    for success in _successes()[:stage_index]:
        aggregate.put_result(success)
    aggregate.put_result(failures[stage_index])
    repo.put(aggregate)

    loaded = repo.get(STUDENT_A, _path())
    restored = loaded.get_result(_path()[stage_index])
    assert type(restored) is type(failures[stage_index])
    assert restored.is_success is False
    assert restored.reason == reason
    assert restored.to_json() == failures[stage_index].to_json()
    assert restored.detailed_text == (
        reason + "\ncompiler stdout\nwarning C1234\n" if stage_index == 1 else reason
    )
    assert loaded.get_next_stage() == _path()[stage_index]


def test_execute_output_collection_and_timestamp_roundtrip(repository) -> None:
    """実行結果のファイル名・バイト列・時刻が失われない。"""
    repo, _ = repository
    _save_through(repo, 2)
    restored = repo.get(STUDENT_A, _path()).get_result(ExecuteStage(CASE_A))
    assert type(restored) is ExecuteSuccessStudentStageResult
    assert restored.execute_config_mtime == EXECUTE_MTIME
    assert restored.output_file_collection.to_json() == _execute_ok().output_file_collection.to_json()
    assert restored.output_file_collection.find(FileID.STDOUT).content_string == "結果: 42\n"


def test_test_result_success_and_wrong_answer_are_distinct(repository) -> None:
    """出力不足の不正解でもTESTステージ自体は成功とする。"""
    repo, _ = repository
    _save_through(repo, 3)
    restored = repo.get(STUDENT_A, _path()).get_result(StageTest(CASE_A))
    assert type(restored) is StageTestSuccessResult
    assert restored.test_config_mtime == TEST_MTIME
    assert restored.is_success is True
    assert restored.is_accepted is False
    assert restored.test_result_output_file_collection.to_json() == _test_ok().test_result_output_file_collection.to_json()


def test_results_can_be_overwritten_without_leaving_old_reason(repository) -> None:
    """失敗から成功へ上書きすると、古いreasonを持つ失敗結果は残らない。"""
    repo, _ = repository
    aggregate = repo.get(STUDENT_A, _path())
    aggregate.put_result(BuildFailureStudentStageResult.create_instance(
        student_id=STUDENT_A, reason="旧エラー\n",
    ))
    repo.put(aggregate)
    assert repo.get(STUDENT_A, _path()).last_stage_main_reason == "旧エラー\n"

    aggregate = repo.get(STUDENT_A, _path())
    aggregate.put_result(_build_ok(checksum=999))
    repo.put(aggregate)
    restored = repo.get(STUDENT_A, _path())
    assert type(restored.get_result(BuildStage())) is BuildSuccessStudentStageResult
    assert restored.get_result(BuildStage()).submission_folder_checksum == 999
    assert restored.last_stage_main_reason is None


def test_result_deletion_in_reverse_order_clears_database(repository) -> None:
    """後段から削除すればすべて未実行に戻り、DBからも消える。"""
    repo, database = repository
    _save_through(repo, 3)
    aggregate = repo.get(STUDENT_A, _path())
    aggregate.delete_all_results()
    repo.put(aggregate)

    restored = repo.get(STUDENT_A, _path())
    assert all(result is None for _, result in restored.iter_stage_results())
    assert restored.get_next_stage() == BuildStage()
    with database.connect() as con:
        for table in ("student_build_result", "student_compile_result", "student_execute_result", "student_test_result"):
            assert con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_deleting_earlier_stage_before_later_stage_is_rejected(repository) -> None:
    """下流結果を残したまま前段だけ消す操作は拒否される。"""
    repo, _ = repository
    _save_through(repo, 2)
    aggregate = repo.get(STUDENT_A, _path())
    with pytest.raises(ValueError, match="next stage"):
        aggregate.delete_result(BuildStage())


def test_shared_and_case_specific_results_remain_independent(repository) -> None:
    """BUILD・COMPILEは共有し、EXECUTE・TESTはケースごとに保存する。"""
    repo, _ = repository
    _save_through(repo, 3, CASE_A)
    loaded_b = repo.get(STUDENT_A, _path(CASE_B))
    assert loaded_b.get_result(BuildStage()).submission_folder_checksum == 123
    assert loaded_b.get_result(CompileStage()).output == "MSVC: ok\n"
    assert loaded_b.get_result(ExecuteStage(CASE_B)) is None
    assert loaded_b.get_result(StageTest(CASE_B)) is None

    loaded_b.put_result(_execute_ok(case_id=CASE_B))
    loaded_b.put_result(_test_ok(case_id=CASE_B))
    repo.put(loaded_b)
    assert repo.get(STUDENT_A, _path(CASE_A)).get_result(ExecuteStage(CASE_A)) is not None
    assert repo.get(STUDENT_A, _path(CASE_B)).get_result(ExecuteStage(CASE_B)) is not None
    assert repo.get(STUDENT_A, _path(CASE_A)).get_result(StageTest(CASE_A)).testcase_id == CASE_A
    assert repo.get(STUDENT_A, _path(CASE_B)).get_result(StageTest(CASE_B)).testcase_id == CASE_B


def test_results_are_isolated_by_student(repository) -> None:
    """同じテストケースでも学生間でステージ結果を共有しない。"""
    repo, _ = repository
    _save_through(repo, 1)
    other = repo.get(STUDENT_B, _path())
    assert all(result is None for _, result in other.iter_stage_results())
    other.put_result(_build_ok(student_id=STUDENT_B, checksum=777))
    repo.put(other)
    assert repo.get(STUDENT_A, _path()).get_result(BuildStage()).submission_folder_checksum == 123
    assert repo.get(STUDENT_B, _path()).get_result(BuildStage()).submission_folder_checksum == 777


def test_timestamp_is_stored_and_visible_to_another_repository(repository) -> None:
    """結果更新時刻はDBへ記録され、別Repositoryでも読み取れる。"""
    repo, database = repository
    assert repo.get_timestamp(STUDENT_A) is None
    _save_through(repo, 0)
    first_timestamp = repo.get_timestamp(STUDENT_A)
    assert isinstance(first_timestamp, datetime)
    reopened = StudentStagePathResultRepository(project_database_io=database)
    assert reopened.get_timestamp(STUDENT_A) == first_timestamp
