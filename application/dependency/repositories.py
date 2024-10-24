from functools import cache

from application.dependency.core_io import *
from application.dependency.path_provider import *
from files.repositories.current_project import CurrentProjectRepository
from files.repositories.global_settings import GlobalSettingsRepository
from files.repositories.project import ProjectRepository
from files.repositories.student import StudentRepository
from files.repositories.student_stage_result import StudentStageResultRepository
from files.repositories.testcase_config import TestCaseConfigRepository


@cache  # ロックを持つのでプロジェクト内ステートフル
def get_global_settings_repository():
    return GlobalSettingsRepository(
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


@cache  # ロックを持つのでプロジェクト内ステートフル
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
