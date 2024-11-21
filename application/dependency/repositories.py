from functools import cache

from application.dependency.core_io import *
from application.dependency.path_provider import *
from infra.repositories.app_version import AppVersionRepository
from infra.repositories.current_project import CurrentProjectRepository
from infra.repositories.global_settings import GlobalSettingsRepository
from infra.repositories.project import ProjectRepository
from infra.repositories.storage import StorageRepository
from infra.repositories.student import StudentRepository
from infra.repositories.student_dynamic import StudentDynamicRepository
from infra.repositories.student_mark import StudentMarkRepository
from infra.repositories.student_stage_result import StudentStageResultRepository
from infra.repositories.test_source import TestSourceRepository
from infra.repositories.testcase_config import TestCaseConfigRepository


@cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
def get_global_settings_repository():
    return GlobalSettingsRepository(
        global_path_provider=get_global_path_provider(),
        global_core_io=get_global_core_io(),
    )


# AppVersionRepository
def get_app_version_repository():
    return AppVersionRepository(
        global_path_provider=get_global_path_provider(),
        global_core_io=get_global_core_io(),
    )


def get_project_repository():
    return ProjectRepository(
        project_list_path_provider=get_project_list_path_provider(),
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
    )


@cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
def get_current_project_repository():
    return CurrentProjectRepository(
        current_project_id=get_current_project_id(),
        project_repo=get_project_repository(),
    )


@cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
def get_student_repository():
    return StudentRepository(
        project_static_path_provider=get_project_static_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


@cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
def get_student_stage_result_repository():
    return StudentStageResultRepository(
        student_stage_result_path_provider=get_student_stage_result_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


@cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
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


def get_student_mark_repository():
    return StudentMarkRepository(
        student_mark_path_provider=get_student_mark_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )
