from pathlib import Path

import pytest

TEST_DATA_ROOT_FULLPATH: Path = Path("~/AutoProgenProjectsTest").expanduser().absolute()
print(f"{TEST_DATA_ROOT_FULLPATH=!s}")


def override_dependency():
    import application.dependency.path_provider

    def get_project_list_folder_fullpath_override():
        return TEST_DATA_ROOT_FULLPATH / "test_project_list"

    application.dependency.path_provider.get_project_list_folder_fullpath \
        = get_project_list_folder_fullpath_override

    def get_global_base_path_override():
        return TEST_DATA_ROOT_FULLPATH / "test_global"

    application.dependency.path_provider.get_global_base_path \
        = get_global_base_path_override


@pytest.fixture(autouse=True)
def setup_test():
    print("setup_test")

    from application.dependency import invalidate_cached_providers
    invalidate_cached_providers()

    from application.state.debug import set_debug
    set_debug(True)
    from application.state.current_project import get_current_project_id
    if get_current_project_id() is None:
        from domain.model.value import ProjectID
        from application.state.current_project import set_current_project_id
        set_current_project_id(ProjectID("test_project_id"))
    override_dependency()

    import shutil
    from application.dependency.path_provider import get_global_base_path
    from application.dependency.path_provider import get_project_list_folder_fullpath
    teardown_folders = [
        get_global_base_path(),
        get_project_list_folder_fullpath(),
    ]
    for folder_fullpath in teardown_folders:
        print(folder_fullpath, TEST_DATA_ROOT_FULLPATH)
        assert folder_fullpath.relative_to(TEST_DATA_ROOT_FULLPATH)
        if folder_fullpath.exists():
            print("rmtree", str(folder_fullpath))
            shutil.rmtree(folder_fullpath)

    from application.dependency.path_provider import get_database_path_provider
    database_fullpath = get_database_path_provider().fullpath()
    assert not database_fullpath.exists()


@pytest.fixture
def sample_students():
    from application.dependency.repository import get_student_repository
    from domain.model.value import StudentID
    from domain.model.student import Student
    from datetime import datetime

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
def sample_student_ids(sample_students):
    return [student.student_id for student in sample_students]
