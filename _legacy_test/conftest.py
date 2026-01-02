from pathlib import Path

import pytest

TEST_DATA_ROOT_FULLPATH: Path = Path("~/AutoProgenProjectsTest").expanduser().absolute()
print(f"{TEST_DATA_ROOT_FULLPATH=!s}")


def override_dependency():
    import app.di.path_config

    def get_project_list_folder_fullpath_override():
        return TEST_DATA_ROOT_FULLPATH / "test_project_list"

    app.di.path_config.get_project_list_folder_fullpath \
        = get_project_list_folder_fullpath_override

    def get_global_base_path_override():
        return TEST_DATA_ROOT_FULLPATH / "test_global"

    app.di.path_config.get_global_base_path \
        = get_global_base_path_override


@pytest.fixture(autouse=True)
def setup_test():
    print("setup_test")

    from app.di import invalidate_cached_providers
    invalidate_cached_providers()

    from application.state.debug import set_debug
    set_debug(True)
    from application.state.current_project import get_current_project_id
    if get_current_project_id() is None:
        from shared.domain.value.identifier import ProjectID
        from application.state.current_project import set_current_project_id
        set_current_project_id(ProjectID("test_project_id"))
    override_dependency()

    import shutil
    from app.di.path_config import get_global_base_path
    from app.di.path_config import get_project_list_folder_fullpath
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

    from app.di.path_config import get_database_path_provider
    database_fullpath = get_database_path_provider().fullpath()
    assert not database_fullpath.exists()


@pytest.fixture
def sample_students():
    from app.di.repository import get_student_repository
    from shared.domain.value.identifier import StudentID
    from shared.domain.entity.student import StudentEntity
    from datetime import datetime

    repo = get_student_repository()
    students = []
    for i in range(10):
        student_id = StudentID(f"00D00{i:05d}A")
        StudentEntity = StudentEntity(
            student_id=student_id,
            name=f"StudentEntity-{i}",
            name_en=f"StudentEntity-{i}-en",
            email_address=f"StudentEntity-{i}@example.com",
            submitted_at=datetime.fromtimestamp(i * 10000 + 86400),
            # ^ add 86,400 to avoid a bug in datetime.timestamp()
            num_submissions=i + 1,
            submission_folder_name=str(student_id),
        )
        students.append(StudentEntity)
    repo.create_all(students)
    return students


@pytest.fixture
def sample_student_ids(sample_students):
    return [StudentEntity.student_id for StudentEntity in sample_students]
