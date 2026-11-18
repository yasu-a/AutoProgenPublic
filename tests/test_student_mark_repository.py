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
    assert repo.exists(first)
    assert not repo.exists(second)
    saved = repo.get(first)
    assert saved.student_id == first
    assert saved.score is None


def test_missing_student_mark_raises(
    repo: StudentMarkRepository, student_ids: tuple[StudentID, StudentID]
) -> None:
    """存在しない採点結果の取得では既存例外を送出する。"""
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(student_ids[0])
    assert repo.get_timestamp(student_ids[0]) is None
    assert repo.list() == []


@pytest.mark.parametrize("score", [None, 0, 50, 99])
def test_put_get_round_trip(
    repo: StudentMarkRepository,
    student_ids: tuple[StudentID, StudentID],
    score: int | None,
) -> None:
    """未採点・0点・通常点を保存して復元する。"""
    student_id = student_ids[0]
    repo.put(StudentMark(student_id=student_id, score=score))
    saved = repo.get(student_id)
    assert saved.student_id == student_id
    assert saved.score == score
    assert saved.marked is (score is not None)
    assert repo.list()[0].score == score


def test_list_multiple_students(
    repo: StudentMarkRepository, student_ids: tuple[StudentID, StudentID]
) -> None:
    """複数学生の点数を独立して保持する。"""
    first, second = student_ids
    repo.put(StudentMark(first, 50))
    repo.put(StudentMark(second, 0))
    marks = {mark.student_id: mark for mark in repo.list()}
    assert set(marks) == set(student_ids)
    assert marks[first].score == 50
    assert marks[second].score == 0


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
    repo.put(StudentMark(student_id, 60))
    updated = repo.get_timestamp(student_id)
    assert isinstance(updated, datetime)
    assert updated >= created


def test_new_schema_stores_only_score_and_timestamp(
    repo: StudentMarkRepository,
    database_io: ProjectDatabaseIO,
    student_ids: tuple[StudentID, StudentID],
) -> None:
    """新規テーブルが採点状態を持たず点数と更新時刻だけを保存する。"""
    repo.create(student_ids[0])
    with database_io.connect() as con:
        columns = {
            row["name"]: row for row in con.execute("PRAGMA table_info(student_mark)")
        }
        row = con.execute(
            "SELECT score, updated_at FROM student_mark WHERE student_id = ?",
            (str(student_ids[0]),),
        ).fetchone()
    assert "confirmed" not in columns
    assert row["score"] is None
    assert row["updated_at"] is not None


def test_foreign_key_is_enforced(
    repo: StudentMarkRepository,
) -> None:
    """登録のない学生に採点結果を保存すると外部キー違反になる。"""
    with pytest.raises(sqlite3.IntegrityError):
        repo.put(StudentMark(StudentID("25D5203184K"), 80))


def test_reopen_preserves_score(
    database_io: ProjectDatabaseIO,
    repo: StudentMarkRepository,
    student_ids: tuple[StudentID, StudentID],
) -> None:
    """新規DBを再度開いたときも点数を保持する。"""
    student_id = student_ids[0]
    repo.put(StudentMark(student_id, 50))
    reopened = StudentMarkRepository(project_database_io=database_io)
    assert reopened.get(student_id).score == 50
