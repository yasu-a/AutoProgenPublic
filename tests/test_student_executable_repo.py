from datetime import datetime
from pathlib import Path

import pytest

from application.dependency.path_provider import get_database_path_provider
from application.dependency.repositories import get_student_executable_repository, \
    get_student_repository
from application.state.current_project import set_current_project_id, get_current_project_id
from application.state.debug import set_debug
from domain.models.file_item import ExecutableFileItem
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
def fake_student_ids():
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
    return [student.student_id for student in students]


def test_get_not_found(fake_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = fake_student_ids

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id)


def test_put_and_get(fake_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = fake_student_ids

    repo.put(fake_student_id, ExecutableFileItem(content_bytes=b"\0\1\2\3\4\5\6\7"))

    assert repo.get(fake_student_id).content_bytes == b"\0\1\2\3\4\5\6\7"


def test_put_and_get_multiple(fake_student_ids):
    repo = get_student_executable_repository()
    fake_student_id_1, fake_student_id_2, *_ = fake_student_ids

    repo.put(fake_student_id_1, ExecutableFileItem(content_bytes=b"\0\1\2\3"))
    repo.put(fake_student_id_2, ExecutableFileItem(content_bytes=b"\4\5\6\7"))

    assert repo.get(fake_student_id_1).content_bytes == b"\0\1\2\3"
    assert repo.get(fake_student_id_2).content_bytes == b"\4\5\6\7"


def test_exists(fake_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = fake_student_ids

    assert not repo.exists(fake_student_id)

    repo.put(fake_student_id, ExecutableFileItem(content_bytes=b"\0\1\2\3\4\5\6\7"))

    assert repo.exists(fake_student_id)


def test_delete_not_found(fake_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = fake_student_ids

    with pytest.raises(FileNotFoundError):
        repo.delete(fake_student_id)


def test_put_and_delete(fake_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = fake_student_ids

    repo.put(fake_student_id, ExecutableFileItem(content_bytes=b"\0\1\2\3\4\5\6\7"))
    repo.delete(fake_student_id)

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id)


def test_put_and_delete_multiple(fake_student_ids):
    repo = get_student_executable_repository()
    fake_student_id_1, fake_student_id_2, *_ = fake_student_ids

    repo.put(fake_student_id_1, ExecutableFileItem(content_bytes=b"\0\1\2\3"))
    repo.put(fake_student_id_2, ExecutableFileItem(content_bytes=b"\4\5\6\7"))
    repo.delete(fake_student_id_1)

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id_1)

    assert repo.get(fake_student_id_2).content_bytes == b"\4\5\6\7"


def test_overwrite(fake_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = fake_student_ids
    test_content_1 = b"\0\1\2\3"
    test_content_2 = b"\4\5\6\7"

    repo.put(fake_student_id, ExecutableFileItem(content_bytes=test_content_1))
    assert repo.get(fake_student_id).content_bytes == test_content_1
    repo.put(fake_student_id, ExecutableFileItem(content_bytes=test_content_2))
    assert repo.get(fake_student_id).content_bytes == test_content_2
