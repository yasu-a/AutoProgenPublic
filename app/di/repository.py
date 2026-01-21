# from functools import cache

# from app.di.path_config import *
# from app.di.state import get_current_project_id_state
# from app.di.system import get_project_database_io, get_global_core_io, get_project_core_io, \
#     get_current_project_core_io
# from shared.infra.repository.current_project import CurrentProjectRepository
# from shared.infra.repository.project import ProjectRepository
# from shared.infra.repository.setting import SettingRepository
# from shared.infra.repository.storage import StorageRepository
# from shared.infra.repository.student import StudentRepository
# from shared.infra.repository.student_dynamic import StudentExecutableRepository, \
#     StudentSourceRepository
# from shared.infra.repository.student_mark import StudentScoreRepository
# from shared.infra.repository.student_stage_path_result import StudentStageResultRepository
# from shared.infra.repository.test_source import TestSourceRepository
# from shared.infra.repository.testcase import TestCaseRepository


# # FIXME: @cacheを付けるとテストのときにステートが残ってしまう
# #        invalidate_cached_providersで一つ一つinvalidateすることで対応している
# #        エンティティのキャッシュはアプリケーションで実装すべき？
# #        ロックはどうする？アプリケーション？

# @cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
# def get_setting_repository():
#     path_config = get_path_config()
#     return SettingRepository(
#         setting_json_path=path_config.settings_json_fullpath,
#         global_core_io=get_global_core_io(),
#     )


# def get_project_repository():
#     path_config = get_path_config()
#     return ProjectRepository(
#         project_folder_fullpath=path_config.project_folder_fullpath,
#         project_config_json_fullpath=path_config.project_config_json_fullpath,
#         project_core_io=get_project_core_io(),
#     )


# @cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
# def get_current_project_repository():
#     current_project_id = get_current_project_id_state().get()
#     if current_project_id is None:
#         raise ValueError("No ProjectEntity is currently open. Open a ProjectEntity first.")
#     return CurrentProjectRepository(
#         current_project_id=current_project_id,
#         project_repo=get_project_repository(),
#     )


# @cache  # インスタンス内部にロックを持つのでプロジェクト内ステートフル
# def get_student_repository():
#     return StudentRepository(
#         project_database_io=get_project_database_io(),
#     )


# @cache  # プロジェクト内ステートフル
# def get_student_stage_result_repository():
#     return StudentStageResultRepository(
#         project_database_io=get_project_database_io(),
#     )


# @cache  # インスタンス内部にキャッシュを持つのでプロジェクト内ステートフル
# def get_testcase_config_repository():
#     return TestCaseRepository(
#         project_database_io=get_project_database_io(),
#     )


# def get_storage_repository():
#     path_config = get_path_config()
#     current_project_id = get_current_project_id_state().get()
#     return StorageRepository(
#         storage_folder_fullpath=lambda st_id: path_config.storage_folder_fullpath(current_project_id, st_id),
#         current_project_core_io=get_current_project_core_io(),
#     )


# # StudentExecutableRepository
# def get_student_executable_repository():
#     return StudentExecutableRepository(
#         project_database_io=get_project_database_io(),
#     )


# def get_student_source_repository():
#     return StudentSourceRepository(
#         project_database_io=get_project_database_io(),
#     )


# def get_test_source_repository():
#     path_config = get_path_config()
#     return TestSourceRepository(
#         test_source_file_fullpath=path_config.test_source_file_fullpath,
#         global_core_io=get_global_core_io(),
#     )


# @cache  # インスタンス内部にロックを持つのでプロジェクト内ステートフル
# def get_student_mark_repository():
#     return StudentScoreRepository(
#         project_database_io=get_project_database_io(),
#     )
