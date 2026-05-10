from application.dependency.service import *
from application.state.current_project import require_current_project_id
from domain.model.value import ProjectID
from usecase.app_version import AppVersionGetTextUseCase, AppVersionCheckIsStableUseCase
from usecase.compiler import CompilerSearchUseCase
from usecase.current_project import CurrentProjectSummaryGetUseCase, \
    CurrentProjectInitializeStaticUseCase
from usecase.global_settings import GlobalSettingsGetUseCase, GlobalSettingsPutUseCase
from usecase.project import ProjectCheckExistByNameUseCase, ProjectCreateUseCase, \
    ProjectListRecentSummaryUseCase, ProjectBaseFolderShowUseCase, \
    ProjectFolderShowUseCase, ProjectDeleteUseCase, ProjectGetSizeQueryUseCase, ProjectOpenUseCase
from usecase.resource_usage import ResourceUsageGetUseCase
from usecase.student import StudentListIDUseCase
from usecase.student_dynamic import StudentDynamicTakeDiffSnapshotUseCase
from usecase.student_mark import StudentMarkGetUseCase, StudentMarkPutUseCase, \
    StudentMarkListUseCase
from usecase.student_mark_view_data import StudentMarkViewDataGetTestResultUseCase, \
    StudentMarkViewDataGetMarkSummaryUseCase
from usecase.student_run_build import StudentRunBuildStageUseCase
from usecase.student_run_compile import StudentRunCompileStageUseCase
from usecase.student_run_execute import StudentRunExecuteStageUseCase
from usecase.student_run_next_stage import StudentRunNextStageUseCase
from usecase.student_run_test import StudentRunTestStageUseCase
from usecase.student_source_code import StudentSourceCodeGetUseCase
from usecase.student_stage_result import StudentStageResultClearUseCase
from usecase.student_submission_folder_show import StudentSubmissionFolderShowUseCase
from usecase.student_table_cell_data import StudentTableGetStudentIDCellDataUseCase, \
    StudentTableGetStudentNameCellDataUseCase, StudentTableGetStudentStageStateCellDataUseCase, \
    StudentTableGetStudentErrorCellDataUseCase
from usecase.test_compile_stage import TestCompileStageUseCase
from usecase.test_test_stage import TestTestStageUseCase
from usecase.testcase_config import TestCaseConfigGetUseCase, TestCaseConfigPutUseCase, \
    TestCaseConfigListIDUseCase, TestCaseConfigDeleteUseCase
from usecase.testcase_list_edit import TestCaseListEditListSummaryUseCase, \
    TestCaseListEditCreateNewNameUseCase, TestCaseListEditCreateTestCaseUseCase, \
    TestCaseListEditCopyTestCaseUseCase


def get_global_settings_get_usecase():
    return GlobalSettingsGetUseCase(
        global_settings_repo=get_global_settings_repository(),
    )


def get_global_settings_put_usecase():
    return GlobalSettingsPutUseCase(
        global_settings_repo=get_global_settings_repository(),
    )


# AppVersionGetTextUseCase
def get_app_version_get_text_usecase():
    return AppVersionGetTextUseCase(
        app_version_repo=get_app_version_repository(),
    )


# AppVersionCheckIsStableUseCase
def create_app_version_check_is_stable_usecase():
    return AppVersionCheckIsStableUseCase(
        app_version_repo=get_app_version_repository(),
    )


def get_project_list_recent_summary_usecase():
    return ProjectListRecentSummaryUseCase(
        project_list_id_query_service=get_project_list_id_query_service(),
        project_get_config_state_query_service=get_project_get_config_state_query_service(),
        project_repo=get_project_repository(),
    )


# ProjectBaseFolderShowUseCase
def get_project_base_folder_show_usecase():
    return ProjectBaseFolderShowUseCase(
        project_folder_show_in_explorer_io=get_project_folder_show_in_explorer_io(),
    )


# ProjectFolderShowUseCase
def get_project_folder_show_usecase():
    return ProjectFolderShowUseCase(
        project_folder_show_in_explorer_io=get_project_folder_show_in_explorer_io(),
    )


def get_project_create_usecase():
    return ProjectCreateUseCase(
        project_repo=get_project_repository(),
        app_version_repo=get_app_version_repository(),
    )


# ProjectDeleteUseCase
def get_project_delete_usecase():
    return ProjectDeleteUseCase(
        project_repo=get_project_repository(),
    )


# ProjectGetSizeQueryUseCase
def get_project_get_size_query_usecase():
    return ProjectGetSizeQueryUseCase(
        project_get_size_query_service=get_project_get_size_query_service(),
    )


def get_current_project_initialize_static_usecase(manaba_report_archive_fullpath: Path):
    return create_current_project_initialize_static_usecase(
        project_id=require_current_project_id(),
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


def create_current_project_initialize_static_usecase(project_id: ProjectID, manaba_report_archive_fullpath: Path):
    return CurrentProjectInitializeStaticUseCase(
        student_master_create_service=create_student_master_create_service(
            project_id=project_id,
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        student_submission_extract_service=create_student_submission_extract_service(
            project_id=project_id,
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        current_project_set_initialized_service=create_current_project_set_initialized_service(project_id),
    )


# ProjectOpenUseCase
def get_project_open_usecase():
    return ProjectOpenUseCase(
        project_update_timestamp_service=get_project_update_timestamp_service(),
    )


def get_project_check_exist_by_name_usecase():
    return ProjectCheckExistByNameUseCase(
        project_list_id_query_service=get_project_list_id_query_service(),
    )


def create_current_project_summary_get_usecase(project_id: ProjectID):
    return CurrentProjectSummaryGetUseCase(
        current_project_get_service=create_current_project_get_service(project_id),
    )


def get_student_list_id_usecase():
    return create_student_list_id_usecase(require_current_project_id())


def create_student_list_id_usecase(project_id: ProjectID):
    return StudentListIDUseCase(
        student_list_sub_service=create_student_list_sub_service(project_id),
    )


def create_student_submission_folder_show_usecase(project_id: ProjectID):
    return StudentSubmissionFolderShowUseCase(
        student_folder_show_in_explorer_io=create_student_folder_show_in_explorer_io(project_id),
    )


def create_student_table_get_student_id_cell_data_usecase(project_id: ProjectID):
    return StudentTableGetStudentIDCellDataUseCase(
        student_submission_exist_service=create_student_submission_exist_service(project_id),
    )


def create_student_table_get_student_name_cell_data_usecase(project_id: ProjectID):
    return StudentTableGetStudentNameCellDataUseCase(
        student_get_service=create_student_get_service(project_id),
    )


def create_student_table_get_student_stage_state_cell_data_usecase(project_id: ProjectID):
    return StudentTableGetStudentStageStateCellDataUseCase(
        stage_path_list_sub_service=create_stage_path_list_sub_service(project_id),
        student_stage_path_result_get_service=create_student_stage_path_result_get_service(project_id),
    )


def create_student_table_get_student_error_cell_data_usecase(project_id: ProjectID):
    return StudentTableGetStudentErrorCellDataUseCase(
        stage_path_list_sub_service=create_stage_path_list_sub_service(project_id),
        student_stage_path_result_get_service=create_student_stage_path_result_get_service(project_id),
    )


def get_compiler_search_usecase():
    return CompilerSearchUseCase()


def get_test_compile_stage_usecase():
    return create_test_compile_stage_usecase(require_current_project_id())


def create_test_compile_stage_usecase(project_id: ProjectID):
    return TestCompileStageUseCase(
        storage_create_service=create_storage_create_service(project_id),
        storage_load_test_source_service=create_storage_load_test_source_service(project_id),
        storage_run_compiler_service=create_storage_run_compiler_service(project_id),
        storage_delete_service=create_storage_delete_service(project_id),
    )


def get_test_test_stage_usecase():
    return TestTestStageUseCase(
        match_get_best_service=get_match_get_best_service(),
    )


def get_student_run_build_stage_usecase():
    return create_student_run_build_stage_usecase(require_current_project_id())


def create_student_run_build_stage_usecase(project_id: ProjectID):
    return StudentRunBuildStageUseCase(
        student_submission_get_source_content_service=create_student_submission_get_source_content_service(project_id),
        student_dynamic_clear_service=create_student_dynamic_clear_service(project_id),
        student_dynamic_set_source_content_service=create_student_dynamic_set_source_content_service(project_id),
        student_submission_get_checksum_service=create_student_submission_get_checksum_service(project_id),
        student_put_stage_result_service=create_student_put_stage_result_service(project_id),

    )


# StudentRunCompileStageUseCase
def get_student_run_compile_stage_usecase():
    return create_student_run_compile_stage_usecase(require_current_project_id())


def create_student_run_compile_stage_usecase(project_id: ProjectID):
    return StudentRunCompileStageUseCase(
        storage_create_service=create_storage_create_service(project_id),
        storage_load_student_source_service=create_storage_load_student_source_service(project_id),
        storage_store_student_executable_service=create_storage_store_student_executable_service(project_id),
        storage_run_compiler_service=create_storage_run_compiler_service(project_id),
        storage_delete_service=create_storage_delete_service(project_id),
        student_put_stage_result_service=create_student_put_stage_result_service(project_id),
    )


# StudentRunExecuteStageUseCase
def get_student_run_execute_stage_usecase():
    return create_student_run_execute_stage_usecase(require_current_project_id())


def create_student_run_execute_stage_usecase(project_id: ProjectID):
    return StudentRunExecuteStageUseCase(
        storage_create_service=create_storage_create_service(project_id),
        storage_load_student_executable_service=create_storage_load_student_executable_service(project_id),
        storage_load_execute_config_input_files_service=create_storage_load_execute_config_input_files_service(project_id),
        storage_take_snapshot_service=create_storage_take_snapshot_service(project_id),
        storage_delete_service=create_storage_delete_service(project_id),
        testcase_config_get_execute_config_mtime_service=create_testcase_config_get_execute_config_mtime_service(project_id),
        storage_run_executable_service=create_storage_run_executable_service(project_id),
        testcase_config_repo=create_testcase_config_repository(project_id),
        storage_create_output_file_mapping_from_diff_service=create_storage_create_output_file_mapping_from_diff_service(project_id),
        storage_write_stdout_file_service=create_storage_write_stdout_file_service(project_id),
        student_put_stage_result_service=create_student_put_stage_result_service(project_id),
    )


# StudentRunTestUseCase
def get_student_run_test_stage_usecase():
    return create_student_run_test_stage_usecase(require_current_project_id())


def create_student_run_test_stage_usecase(project_id: ProjectID):
    return StudentRunTestStageUseCase(
        testcase_config_repo=create_testcase_config_repository(project_id),
        testcase_config_get_test_config_mtime_service=create_testcase_config_get_test_config_mtime_service(project_id),
        match_get_best_service=get_match_get_best_service(),
        student_put_stage_result_service=create_student_put_stage_result_service(project_id),
        student_get_stage_result_service=create_student_get_stage_result_service(project_id),
    )


def get_student_run_next_stage_usecase():
    return create_student_run_next_stage_usecase(require_current_project_id())


def create_student_run_next_stage_usecase(project_id: ProjectID):
    return StudentRunNextStageUseCase(
        stage_path_list_sub_service=create_stage_path_list_sub_service(project_id),
        student_stage_path_result_get_service=create_student_stage_path_result_get_service(project_id),
        student_stage_path_result_repo=create_student_stage_path_result_repository(project_id),
        student_run_build_stage_usecase=create_student_run_build_stage_usecase(project_id),
        student_run_compile_stage_usecase=create_student_run_compile_stage_usecase(project_id),
        student_run_execute_stage_usecase=create_student_run_execute_stage_usecase(project_id),
        student_run_test_stage_usecase=create_student_run_test_stage_usecase(project_id),
        student_stage_path_result_check_rollback_service=create_student_stage_path_result_check_rollback_service(project_id),
    )


# TestCaseListEditListSummaryUseCase
def get_testcase_list_edit_list_summary_usecase():
    return create_testcase_list_edit_list_summary_usecase(require_current_project_id())


def create_testcase_list_edit_list_summary_usecase(project_id: ProjectID):
    return TestCaseListEditListSummaryUseCase(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


# TestCaseListEditCreateNewNameUseCase
def get_testcase_list_edit_create_new_name_usecase():
    return create_testcase_list_edit_create_new_name_usecase(require_current_project_id())


def create_testcase_list_edit_create_new_name_usecase(project_id: ProjectID):
    return TestCaseListEditCreateNewNameUseCase(
        testcase_config_list_id_sub_service=create_testcase_config_list_id_sub_service(project_id),
    )


# TestCaseListEditCreateTestCaseUseCase
def get_testcase_list_edit_create_testcase_usecase():
    return create_testcase_list_edit_create_testcase_usecase(require_current_project_id())


def create_testcase_list_edit_create_testcase_usecase(project_id: ProjectID):
    return TestCaseListEditCreateTestCaseUseCase(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


# TestCaseListEditCopyTestCaseUseCase
def get_testcase_list_edit_copy_testcase_usecase():
    return create_testcase_list_edit_copy_testcase_usecase(require_current_project_id())


def create_testcase_list_edit_copy_testcase_usecase(project_id: ProjectID):
    return TestCaseListEditCopyTestCaseUseCase(
        testcase_config_copy_service=create_testcase_config_copy_service(project_id),
    )


# StudentStageResultTakeDiffSnapshotUseCase
def create_student_dynamic_take_diff_snapshot_usecase(project_id: ProjectID):
    return StudentDynamicTakeDiffSnapshotUseCase(
        student_stage_result_check_timestamp_query_service=create_student_stage_result_check_timestamp_query_service(project_id),
        student_mark_check_timestamp_query_service=create_student_mark_check_timestamp_query_service(project_id),
    )


# StudentStageResultClearUseCase
def get_student_stage_result_clear_usecase():
    return create_student_stage_result_clear_usecase(require_current_project_id())


def create_student_stage_result_clear_usecase(project_id: ProjectID):
    return StudentStageResultClearUseCase(
        student_stage_result_clear_service=create_student_stage_result_clear_service(project_id),
    )


# TestCaseConfigGetUseCase
def get_testcase_config_get_usecase():
    return create_testcase_config_get_usecase(require_current_project_id())


def create_testcase_config_get_usecase(project_id: ProjectID):
    return TestCaseConfigGetUseCase(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


# TestCaseConfigPutUseCase
def get_testcase_config_put_usecase():
    return create_testcase_config_put_usecase(require_current_project_id())


def create_testcase_config_put_usecase(project_id: ProjectID):
    return TestCaseConfigPutUseCase(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


def get_testcase_config_delete_usecase():
    return create_testcase_config_delete_usecase(require_current_project_id())


def create_testcase_config_delete_usecase(project_id: ProjectID):
    return TestCaseConfigDeleteUseCase(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


def get_testcase_config_list_id_usecase():
    return create_testcase_config_list_id_usecase(require_current_project_id())


def create_testcase_config_list_id_usecase(project_id: ProjectID):
    return TestCaseConfigListIDUseCase(
        testcase_config_list_id_sub_service=create_testcase_config_list_id_sub_service(project_id),
    )


# StudentMarkViewDataGetTestResultUseCase
def get_student_mark_view_data_get_test_result_usecase():
    return create_student_mark_view_data_get_test_result_usecase(require_current_project_id())


def create_student_mark_view_data_get_test_result_usecase(project_id: ProjectID):
    return StudentMarkViewDataGetTestResultUseCase(
        stage_path_get_by_testcase_id_service=create_stage_path_get_by_testcase_id_service(project_id),
        student_stage_path_result_get_service=create_student_stage_path_result_get_service(project_id),
    )


# StudentMarkViewDataGetMarkSummaryUseCase
def get_student_mark_view_data_get_mark_summary_usecase():
    return create_student_mark_view_data_get_mark_summary_usecase(require_current_project_id())


def create_student_mark_view_data_get_mark_summary_usecase(project_id: ProjectID):
    return StudentMarkViewDataGetMarkSummaryUseCase(
        student_get_service=create_student_get_service(project_id),
        student_mark_get_sub_service=create_student_mark_get_sub_service(project_id),
        stage_path_list_sub_service=create_stage_path_list_sub_service(project_id),
        student_stage_path_result_get_service=create_student_stage_path_result_get_service(project_id),
        student_stage_path_result_check_rollback_service=create_student_stage_path_result_check_rollback_service(project_id),
    )


# StudentSourceCodeGetUseCase
def get_student_source_code_get_usecase():
    return create_student_source_code_get_usecase(require_current_project_id())


def create_student_source_code_get_usecase(project_id: ProjectID):
    return StudentSourceCodeGetUseCase(
        student_source_code_get_query_service=create_student_dynamic_get_source_content_service(project_id),
    )


# StudentMarkGetUseCase
def get_student_mark_get_usecase():
    return create_student_mark_get_usecase(require_current_project_id())


def create_student_mark_get_usecase(project_id: ProjectID):
    return StudentMarkGetUseCase(
        student_mark_get_sub_service=create_student_mark_get_sub_service(project_id),
    )


# StudentMarkPutUseCase
def get_student_mark_put_usecase():
    return create_student_mark_put_usecase(require_current_project_id())


def create_student_mark_put_usecase(project_id: ProjectID):
    return StudentMarkPutUseCase(
        student_mark_put_service=create_student_mark_put_service(project_id),
    )


# StudentMarkListUseCase
def get_student_mark_list_usecase():
    return create_student_mark_list_usecase(require_current_project_id())


def create_student_mark_list_usecase(project_id: ProjectID):
    return StudentMarkListUseCase(
        student_mark_list_service=create_student_mark_list_service(project_id),
    )


# ResourceUsageGetUseCase
def create_resource_usage_get_usecase():
    return ResourceUsageGetUseCase(
        resource_usage_io=get_resource_usage_io(),
    )
