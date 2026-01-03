from functools import cache

from app.di.path_config import *
from app.di.state import get_current_project_id_state
from app.di.system import get_project_database_io, get_global_core_io, get_project_core_io, \
    get_current_project_core_io
from shared.infra.repository.current_project import CurrentProjectRepository
from shared.infra.repository.project import ProjectRepository
from shared.infra.repository.setting import SettingRepository
from shared.infra.repository.storage import StorageRepository
from shared.infra.repository.student import StudentRepository
from shared.infra.repository.student_dynamic import StudentExecutableRepository, \
    StudentSourceRepository
from shared.infra.repository.student_mark import StudentMarkEntityRepository
from shared.infra.repository.student_stage_path_result import StudentStagePathResultEntityRepository
from shared.infra.repository.test_source import TestSourceRepository
from shared.infra.repository.testcase_config import TestCaseConfigRepository


# FIXME: @cacheを付けるとテストのときにステートが残ってしまう
#        invalidate_cached_providersで一つ一つinvalidateすることで対応している
#        エンティティのキャッシュはアプリケーションで実装すべき？
#        ロックはどうする？アプリケーション？

@cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
def get_setting_repository():
    return SettingRepository(
        settings_json_fullpath=get_global_path_provider().settings_json_fullpath(),
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
    current_project_id = get_current_project_id_state().get()
    if current_project_id is None:
        raise ValueError("No ProjectEntity is currently open. Open a ProjectEntity first.")
    return CurrentProjectRepository(
        current_project_id=current_project_id,
        project_repo=get_project_repository(),
    )


@cache  # インスタンス内部にロックを持つのでプロジェクト内ステートフル
def get_student_repository():
    return StudentRepository(
        project_database_io=get_project_database_io(),
    )


@cache  # プロジェクト内ステートフル
def get_student_stage_path_result_repository():
    return StudentStagePathResultEntityRepository(
        project_database_io=get_project_database_io(),
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


# StudentExecutableRepository
def get_student_executable_repository():
    return StudentExecutableRepository(
        project_database_io=get_project_database_io(),
    )


def get_student_source_repository():
    return StudentSourceRepository(
        project_database_io=get_project_database_io(),
    )


def get_test_source_repository():
    return TestSourceRepository(
        global_path_provider=get_global_path_provider(),
        global_core_io=get_global_core_io(),
    )


@cache  # インスタンス内部にロックを持つのでプロジェクト内ステートフル
def get_student_mark_repository():
    return StudentMarkEntityRepository(
        project_database_io=get_project_database_io(),
    )
