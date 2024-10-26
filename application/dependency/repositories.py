from functools import cache

from application.dependency.core_io import *
from application.dependency.path_provider import *
from files.repositories.current_project import CurrentProjectRepository
from files.repositories.global_config import GlobalConfigRepository
from files.repositories.project import ProjectRepository
from files.repositories.storage import StorageRepository
from files.repositories.student import StudentRepository
from files.repositories.student_dynamic import StudentDynamicRepository
from files.repositories.student_stage_result import StudentStageResultRepository
from files.repositories.test_source import TestSourceRepository
from files.repositories.testcase_config import TestCaseConfigRepository


@cache  # キャッシュを持つのでプロジェクト内ステートフル
def get_global_config_repository():
    return GlobalConfigRepository(
        global_path_provider=get_global_path_provider(),
    )


def get_project_repository():
    return ProjectRepository(
        project_list_path_provider=get_project_list_path_provider(),
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
    )


def get_current_project_repository():
    return CurrentProjectRepository(
        current_project_id=get_current_project_id(),
        project_repo=get_project_repository(),
    )


@cache  # キャッシュを持つのでプロジェクト内ステートフル
def get_student_repository():
    return StudentRepository(
        project_static_path_provider=get_project_static_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_student_stage_result_repository():
    return StudentStageResultRepository(
        student_stage_result_path_provider=get_student_stage_result_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_testcase_config_repository():
    return TestCaseConfigRepository(
        testcase_config_path_provider=get_testcase_config_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_storage_repository():
    return StorageRepository(
        storage_path_provider=get_storage_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_student_dynamic_repository():
    return StudentDynamicRepository(
        student_dynamic_path_provider=get_student_dynamic_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_test_source_repository():
    return TestSourceRepository(
        global_path_provider=get_global_path_provider(),
        global_core_io=get_global_core_io(),
    )
