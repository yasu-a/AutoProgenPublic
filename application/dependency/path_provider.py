import sys
from pathlib import Path

from application.state.current_project import require_current_project_id
from domain.model.value import ProjectID
from infra.path_provider.current_project import DynamicPathProvider, StudentDynamicPathProvider, \
    StudentStageResultPathProvider, ProjectStaticPathProvider, StudentSubmissionPathProvider, \
    TestCaseConfigPathProvider, StudentMarkPathProvider, StoragePathProvider, DatabasePathProvider
from infra.path_provider.global_ import GlobalPathProvider
from infra.path_provider.project import ProjectListPathProvider, ProjectPathProvider


def get_global_base_path() -> Path:
    return Path(sys.argv[0]).resolve().parent


def get_static_resource_base_path() -> Path:
    return get_global_base_path() / "static"


def get_icon_fullpath(filename: str) -> Path:
    return get_static_resource_base_path() / "icon" / f"{filename}.png"


def get_image_fullpath(filename: str) -> Path:
    return get_static_resource_base_path() / "img" / f"{filename}.jpg"


def get_global_path_provider():
    return GlobalPathProvider(
        global_settings_folder_fullpath=get_global_base_path(),
    )


def get_project_list_folder_fullpath() -> Path:
    return Path("~/AutoProgenProjects").expanduser().resolve()


def get_project_list_path_provider():
    return ProjectListPathProvider(
        project_list_folder_fullpath=get_project_list_folder_fullpath(),
    )


def get_project_path_provider():
    return ProjectPathProvider(
        project_list_path_provider=get_project_list_path_provider(),
    )


def create_testcase_config_path_provider(project_id: ProjectID):
    return TestCaseConfigPathProvider(
        current_project_id=project_id,
        project_path_provider=get_project_path_provider(),
    )


def get_testcase_config_path_provider():
    return create_testcase_config_path_provider(require_current_project_id())


def create_student_mark_path_provider(project_id: ProjectID):
    return StudentMarkPathProvider(
        current_project_id=project_id,
        project_path_provider=get_project_path_provider(),
    )


def get_student_mark_path_provider():
    return create_student_mark_path_provider(require_current_project_id())


def create_dynamic_path_provider(project_id: ProjectID):
    return DynamicPathProvider(
        current_project_id=project_id,
        project_path_provider=get_project_path_provider(),
    )


def get_dynamic_path_provider():
    return create_dynamic_path_provider(require_current_project_id())


def create_database_path_provider(project_id: ProjectID):
    return DatabasePathProvider(
        dynamic_path_provider=create_dynamic_path_provider(project_id),
    )


def get_database_path_provider():
    return create_database_path_provider(require_current_project_id())


def create_storage_path_provider(project_id: ProjectID):
    return StoragePathProvider(
        dynamic_path_provider=create_dynamic_path_provider(project_id),
    )


def get_storage_path_provider():
    return create_storage_path_provider(require_current_project_id())


def create_student_dynamic_path_provider(project_id: ProjectID):
    return StudentDynamicPathProvider(
        dynamic_path_provider=create_dynamic_path_provider(project_id),
    )


def get_student_dynamic_path_provider():
    return create_student_dynamic_path_provider(require_current_project_id())


def create_student_stage_result_path_provider(project_id: ProjectID):
    return StudentStageResultPathProvider(
        student_dynamic_path_provider=create_student_dynamic_path_provider(project_id),
    )


def get_student_stage_result_path_provider():
    return create_student_stage_result_path_provider(require_current_project_id())


def create_project_static_path_provider(project_id: ProjectID):
    return ProjectStaticPathProvider(
        current_project_id=project_id,
        project_path_provider=get_project_path_provider(),
    )


def get_project_static_path_provider():
    return create_project_static_path_provider(require_current_project_id())


def create_student_submission_path_provider(project_id: ProjectID):
    return StudentSubmissionPathProvider(
        project_static_path_provider=create_project_static_path_provider(project_id),
    )


def get_student_submission_path_provider():
    return create_student_submission_path_provider(require_current_project_id())
