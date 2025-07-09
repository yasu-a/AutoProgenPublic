import pytest

from application.dependency.repositories import get_student_repository
from domain.errors import RepositoryItemNotFoundError
from domain.models.student import Student
from domain.models.values import StudentID
from tests.conftest import sample_student_ids


def _compare_student(s_1: Student, s_2: Student):
    return s_1.student_id == s_2.student_id \
        and s_1.name == s_2.name \
        and s_1.name_en == s_2.name_en \
        and s_1.email_address == s_2.email_address \
        and s_1.submitted_at == s_2.submitted_at \
        and s_1.num_submissions == s_2.num_submissions \
        and s_1.submission_folder_name == s_2.submission_folder_name


def test_no_students():
    repo = get_student_repository()
    assert not repo.exists_any()


def test_any_students(sample_student_ids):
    _ = sample_student_ids  # use fixture to prepare students in database
    repo = get_student_repository()
    assert repo.exists_any()


def test_get_not_found(sample_student_ids):
    repo = get_student_repository()
    unknown_student_id = StudentID("00D0000000Z")
    assert unknown_student_id not in sample_student_ids
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(unknown_student_id)


def test_get(sample_students):
    repo = get_student_repository()
    student, *_ = sample_students
    student_by_get = repo.get(student.student_id)
    assert _compare_student(student, student_by_get)


def test_list(sample_students):
    repo = get_student_repository()
    students_by_list = repo.list()
    assert len(students_by_list) == len(sample_students)
    for student, student_by_get in zip(sample_students, students_by_list):
        assert _compare_student(student, student_by_get)
