from functools import cache

from application.dependency.core_io import *
from application.dependency.external_io import create_project_database_io
from application.dependency.path_provider import *
from application.state.current_project import require_current_project_id
from domain.model.value import ProjectID
from infra.repository.app_version import AppVersionRepository
from infra.repository.current_project import CurrentProjectRepository
from infra.repository.global_settings import GlobalSettingsRepository
from infra.repository.project import ProjectRepository
from infra.repository.storage import StorageRepository
from infra.repository.student import StudentRepository
from infra.repository.student_dynamic import StudentExecutableRepository, StudentSourceRepository
from infra.repository.student_mark import StudentMarkRepository
from infra.repository.student_stage_path_result import StudentStagePathResultRepository
from infra.repository.test_source import TestSourceRepository
from infra.repository.testcase_config import TestCaseConfigRepository


# FIXME: @cacheを付けるとテストのときにステートが残ってしまう
#        invalidate_cached_providersで一つ一つinvalidateすることで対応している
#        エンティティのキャッシュはアプリケーションで実装すべき？
#        ロックはどうする？アプリケーション？

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
    # Deprecated: incremental migration compatibility only.
    # New code should use ProjectContainer.current_project_repository.
    return create_current_project_repository(require_current_project_id())


def create_current_project_repository(project_id: ProjectID):
    return CurrentProjectRepository(
        current_project_id=project_id,
        project_repo=get_project_repository(),
    )


@cache  # インスタンス内部にロックを持つのでプロジェクト内ステートフル
def get_student_repository():
    # Deprecated: incremental migration compatibility only.
    # New code should use ProjectContainer.student_repository.
    return create_student_repository(require_current_project_id())


def create_student_repository(project_id: ProjectID):
    return StudentRepository(
        project_database_io=create_project_database_io(project_id),
    )


@cache  # プロジェクト内ステートフル
def get_student_stage_path_result_repository():
    # Deprecated: incremental migration compatibility only.
    # New code should use ProjectContainer.student_stage_path_result_repository.
    return create_student_stage_path_result_repository(require_current_project_id())


def create_student_stage_path_result_repository(project_id: ProjectID):
    return StudentStagePathResultRepository(
        project_database_io=create_project_database_io(project_id),
    )


@cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
def get_testcase_config_repository():
    # Deprecated: incremental migration compatibility only.
    # New code should use ProjectContainer.testcase_config_repository.
    return create_testcase_config_repository(require_current_project_id())


def create_testcase_config_repository(project_id: ProjectID):
    return TestCaseConfigRepository(
        testcase_config_path_provider=create_testcase_config_path_provider(project_id),
        current_project_core_io=create_current_project_core_io(project_id),
    )


def get_storage_repository():
    # Deprecated: incremental migration compatibility only.
    # New code should use ProjectContainer.storage_repository.
    return create_storage_repository(require_current_project_id())


def create_storage_repository(project_id: ProjectID):
    return StorageRepository(
        storage_path_provider=create_storage_path_provider(project_id),
        current_project_core_io=create_current_project_core_io(project_id),
    )


# StudentExecutableRepository
def get_student_executable_repository():
    # Deprecated: incremental migration compatibility only.
    # New code should use ProjectContainer.student_executable_repository.
    return create_student_executable_repository(require_current_project_id())


def create_student_executable_repository(project_id: ProjectID):
    return StudentExecutableRepository(
        project_database_io=create_project_database_io(project_id),
    )


def get_student_source_repository():
    # Deprecated: incremental migration compatibility only.
    # New code should use ProjectContainer.student_source_repository.
    return create_student_source_repository(require_current_project_id())


def create_student_source_repository(project_id: ProjectID):
    return StudentSourceRepository(
        project_database_io=create_project_database_io(project_id),
    )


def get_test_source_repository():
    return TestSourceRepository(
        global_path_provider=get_global_path_provider(),
        global_core_io=get_global_core_io(),
    )


@cache  # インスタンス内部にロックを持つのでプロジェクト内ステートフル
def get_student_mark_repository():
    # Deprecated: incremental migration compatibility only.
    # New code should use ProjectContainer.student_mark_repository.
    return create_student_mark_repository(require_current_project_id())


def create_student_mark_repository(project_id: ProjectID):
    return StudentMarkRepository(
        project_database_io=create_project_database_io(project_id),
    )
