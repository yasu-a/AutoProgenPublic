"""採点結果のSQLite保存・復元を検証する。"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from autoprogen.domain.error import RepositoryItemNotFoundError
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.io.project_database import ProjectDatabaseIO
from autoprogen.infra.repository.student_mark import StudentMarkRepository


@pytest.fixture
def student_ids() -> tuple[StudentID, StudentID]:
    """外部キー検査用に登録する2名の学生IDを返す。"""
    return StudentID("21D5109047B"), StudentID("24A0007521M")


@pytest.fixture
def database_io(tmp_path: Path, student_ids: tuple[StudentID, StudentID]) -> ProjectDatabaseIO:
    """学生を登録した新規SQLiteデータベースを作成する。"""
    database_io = ProjectDatabaseIO(database_path=tmp_path / "project.db")
    with database_io.connect() as con:
        con.execute("CREATE TABLE student (student_id TEXT NOT NULL PRIMARY KEY)")
        con.executemany(
            "INSERT INTO student (student_id) VALUES (?)",
            [(str(student_id),) for student_id in student_ids],
        )
        con.commit()
    return database_io


@pytest.fixture
def repo(database_io: ProjectDatabaseIO) -> StudentMarkRepository:
    """テスト用データベースに接続する採点結果Repositoryを返す。"""
    return StudentMarkRepository(project_database_io=database_io)


def test_create_get_and_exists(
    repo: StudentMarkRepository, student_ids: tuple[StudentID, StudentID]
) -> None:
    """新規作成では点数がなく、存在確認と取得ができる。"""
    first, second = student_ids
    assert not repo.exists(first)
    assert not repo.exists(second)
    mark = repo.create(first)
    assert mark.score is None
    assert not mark.marked
    assert not mark.confirmed
    assert repo.exists(first)
    assert not repo.exists(second)
    saved = repo.get(first)
    assert saved.student_id == first
    assert saved.score is None
    assert not saved.confirmed


def test_missing_student_mark_raises(
    repo: StudentMarkRepository, student_ids: tuple[StudentID, StudentID]
) -> None:
    """存在しない採点結果の取得では既存例外を送出する。"""
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(student_ids[0])
    assert repo.get_timestamp(student_ids[0]) is None
    assert repo.list() == []


@pytest.mark.parametrize("score, confirmed", [(None, False), (0, True), (50, False), (99, True)])
def test_put_get_round_trip(
    repo: StudentMarkRepository,
    student_ids: tuple[StudentID, StudentID],
    score: int | None,
    confirmed: bool,
) -> None:
    """未採点・0点・未確定・確定の各状態を保存して復元する。"""
    student_id = student_ids[0]
    repo.put(StudentMark(student_id=student_id, score=score, confirmed=confirmed))
    saved = repo.get(student_id)
    assert saved.student_id == student_id
    assert saved.score == score
    assert saved.marked is (score is not None)
    assert saved.confirmed is confirmed
    assert repo.list()[0].confirmed is confirmed


def test_overwrite_preserves_explicit_unconfirmed(
    repo: StudentMarkRepository, student_ids: tuple[StudentID, StudentID]
) -> None:
    """確定済みの点数を未確定で上書きしても勝手に確定しない。"""
    student_id = student_ids[0]
    repo.put(StudentMark(student_id, 80, confirmed=True))
    repo.put(StudentMark(student_id, 80, confirmed=False))
    assert repo.get(student_id).score == 80
    assert not repo.get(student_id).confirmed
    assert not repo.list()[0].confirmed


def test_list_multiple_students(
    repo: StudentMarkRepository, student_ids: tuple[StudentID, StudentID]
) -> None:
    """複数学生の点数と確定状態を独立して保持する。"""
    first, second = student_ids
    repo.put(StudentMark(first, 50, confirmed=False))
    repo.put(StudentMark(second, 0, confirmed=True))
    marks = {mark.student_id: mark for mark in repo.list()}
    assert set(marks) == set(student_ids)
    assert marks[first].score == 50
    assert not marks[first].confirmed
    assert marks[second].score == 0
    assert marks[second].confirmed


def test_timestamps_update_only_on_write(
    repo: StudentMarkRepository, student_ids: tuple[StudentID, StudentID]
) -> None:
    """採点結果の作成・更新で記録時刻を持ち、取得時は変更しない。"""
    student_id = student_ids[0]
    assert repo.get_timestamp(student_id) is None
    repo.create(student_id)
    created = repo.get_timestamp(student_id)
    assert isinstance(created, datetime)
    assert abs((datetime.now() - created).total_seconds()) < 60
    repo.get(student_id)
    repo.list()
    assert repo.get_timestamp(student_id) == created
    repo.put(StudentMark(student_id, 60, confirmed=False))
    updated = repo.get_timestamp(student_id)
    assert isinstance(updated, datetime)
    assert updated >= created


def test_new_schema_has_confirmation_column(
    repo: StudentMarkRepository,
    database_io: ProjectDatabaseIO,
    student_ids: tuple[StudentID, StudentID],
) -> None:
    """新規テーブルが確定状態をNULL不可の整数列として保存する。"""
    repo.create(student_ids[0])
    with database_io.connect() as con:
        columns = {
            row["name"]: row for row in con.execute("PRAGMA table_info(student_mark)")
        }
        row = con.execute(
            "SELECT score, confirmed FROM student_mark WHERE student_id = ?",
            (str(student_ids[0]),),
        ).fetchone()
    assert columns["confirmed"]["type"] == "INTEGER"
    assert columns["confirmed"]["notnull"] == 1
    assert row["score"] is None
    assert row["confirmed"] == 0


def test_foreign_key_is_enforced(
    repo: StudentMarkRepository,
) -> None:
    """登録のない学生に採点結果を保存すると外部キー違反になる。"""
    with pytest.raises(sqlite3.IntegrityError):
        repo.put(StudentMark(StudentID("25D5203184K"), 80, confirmed=True))


def test_reopen_preserves_unconfirmed(
    database_io: ProjectDatabaseIO,
    repo: StudentMarkRepository,
    student_ids: tuple[StudentID, StudentID],
) -> None:
    """新規DBを再度開いたときも未確定状態を保持する。"""
    student_id = student_ids[0]
    repo.put(StudentMark(student_id, 50, confirmed=False))
    reopened = StudentMarkRepository(project_database_io=database_io)
    assert reopened.get(student_id).score == 50
    assert not reopened.get(student_id).confirmed
