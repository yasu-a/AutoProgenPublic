from datetime import datetime
from pathlib import Path

import pytest

from application.dependency.path_provider import get_database_path_provider
from application.dependency.repositories import get_student_repository
from application.state.current_project import set_current_project_id, get_current_project_id
from application.state.debug import set_debug
from domain.models.student import Student
from domain.models.values import ProjectID, StudentID


def override_dependency():
    import application.dependency.path_provider

    def get_project_list_folder_fullpath_override():
        return Path(__file__).parent / "test_project_list"

    application.dependency.path_provider.get_project_list_folder_fullpath \
        = get_project_list_folder_fullpath_override

    def get_global_base_path_override():
        return Path(__file__).parent / "test_global"

    application.dependency.path_provider.get_global_base_path \
        = get_global_base_path_override

    def get_storage_path_provider_override():
        return Path(__file__).parent / "test_storage"

    application.dependency.path_provider.get_storage_path_provider \
        = get_storage_path_provider_override


@pytest.fixture(autouse=True)
def setup_test():
    print("setup_test")
    set_debug(True)
    if get_current_project_id() is None:
        set_current_project_id(ProjectID("test_project_id"))
    override_dependency()
    database_fullpath = get_database_path_provider().fullpath()
    if database_fullpath.exists():
        database_fullpath.unlink()


@pytest.fixture
def fake_students():
    repo = get_student_repository()
    students = []
    for i in range(10):
        student_id = StudentID(f"00D00{i:05d}A")
        student = Student(
            student_id=student_id,
            name=f"student-{i}",
            name_en=f"student-{i}-en",
            email_address=f"student-{i}@example.com",
            submitted_at=datetime.fromtimestamp(i * 10000 + 86400),
            # ^ add 86,400 to avoid a bug in datetime.timestamp()
            num_submissions=i + 1,
            submission_folder_name=str(student_id),
        )
        students.append(student)
    repo.create_all(students)
    return students


@pytest.fixture
def fake_student_ids(fake_students):
    return [student.student_id for student in fake_students]


def test_no_students():
    repo = get_student_repository()
    assert not repo.exists_any()


def test_any_students(fake_student_ids):
    repo = get_student_repository()
    assert repo.exists_any()


def test_get_not_found(fake_student_ids):
    repo = get_student_repository()
    unknown_student_id = StudentID("00D0000000Z")
    assert unknown_student_id not in fake_student_ids
    with pytest.raises(ValueError):
        repo.get(unknown_student_id)


def compare_student(s_1: Student, s_2: Student):
    return s_1.student_id == s_2.student_id \
        and s_1.name == s_2.name \
        and s_1.name_en == s_2.name_en \
        and s_1.email_address == s_2.email_address \
        and s_1.submitted_at == s_2.submitted_at \
        and s_1.num_submissions == s_2.num_submissions \
        and s_1.submission_folder_name == s_2.submission_folder_name


def test_get(fake_students):
    repo = get_student_repository()
    student, *_ = fake_students
    student_by_get = repo.get(student.student_id)
    assert compare_student(student, student_by_get)


def test_list(fake_students):
    repo = get_student_repository()
    students_by_list = repo.list()
    assert len(students_by_list) == len(fake_students)
    for student, student_by_get in zip(fake_students, students_by_list):
        assert compare_student(student, student_by_get)
