from application.dependency.service import *
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
    TestCaseConfigListIDUseCase
from usecase.testcase_list_edit import TestCaseListEditListSummaryUseCase, \
    TestCaseListEditCreateNewNameUseCase, TestCaseListEditCreateTestCaseUseCase, \
    TestCaseListEditCopyTestCaseUseCase


def get_global_settings_get_usecase():
    return GlobalSettingsGetUseCase(
        global_settings_get_service=get_global_settings_get_service(),
    )


def get_global_settings_put_usecase():
    return GlobalSettingsPutUseCase(
        global_settings_put_service=get_global_settings_put_service(),
    )


# AppVersionGetTextUseCase
def get_app_version_get_text_usecase():
    return AppVersionGetTextUseCase(
        app_version_get_service=get_app_version_get_service(),
    )


# AppVersionCheckIsStableUseCase
def get_app_version_check_is_stable_usecase():
    return AppVersionCheckIsStableUseCase(
        app_version_get_service=get_app_version_get_service(),
    )


def get_project_list_recent_summary_usecase():
    return ProjectListRecentSummaryUseCase(
        project_list_id_query_service=get_project_list_id_query_service(),
        project_get_config_state_query_service=get_project_get_config_state_query_service(),
        project_get_service=get_project_get_service(),
    )


# ProjectBaseFolderShowUseCase
def get_project_base_folder_show_usecase():
    return ProjectBaseFolderShowUseCase(
        project_base_folder_show_service=get_project_base_folder_show_service(),
    )


# ProjectFolderShowUseCase
def get_project_folder_show_usecase():
    return ProjectFolderShowUseCase(
        project_folder_show_service=get_project_folder_show_service(),
    )


def get_project_create_usecase():
    return ProjectCreateUseCase(
        project_create_service=get_project_create_service(),
    )


# ProjectDeleteUseCase
def get_project_delete_usecase():
    return ProjectDeleteUseCase(
        project_delete_service=get_project_delete_service(),
    )


# ProjectGetSizeQueryUseCase
def get_project_get_size_query_usecase():
    return ProjectGetSizeQueryUseCase(
        project_get_size_query_service=get_project_get_size_query_service(),
    )


def get_current_project_initialize_static_usecase(manaba_report_archive_fullpath: Path):
    return CurrentProjectInitializeStaticUseCase(
        student_master_create_service=get_student_master_create_service(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        student_submission_extract_service=get_student_submission_extract_service(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        current_project_set_initialized_service=get_current_project_set_initialized_service(),
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


def get_current_project_summary_get_usecase():
    return CurrentProjectSummaryGetUseCase(
        current_project_get_service=get_current_project_get_service(),
    )


def get_student_list_id_usecase():
    return StudentListIDUseCase(
        student_list_sub_service=get_student_list_sub_service(),
    )


def get_student_submission_folder_show_usecase():
    return StudentSubmissionFolderShowUseCase(
        student_submission_folder_show_service=get_student_submission_folder_show_service(),
    )


def get_student_table_get_student_id_cell_data_usecase():
    return StudentTableGetStudentIDCellDataUseCase(
        student_submission_exist_service=get_student_submission_exist_service(),
    )


def get_student_table_get_student_name_cell_data_usecase():
    return StudentTableGetStudentNameCellDataUseCase(
        student_get_service=get_student_get_service(),
    )


def get_student_table_get_student_stage_state_cell_data_usecase():
    return StudentTableGetStudentStageStateCellDataUseCase(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
    )


def get_student_table_get_student_error_cell_data_usecase():
    return StudentTableGetStudentErrorCellDataUseCase(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
    )


def get_compiler_search_usecase():
    return CompilerSearchUseCase()


def get_test_compile_stage_usecase():
    return TestCompileStageUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_test_source_service=get_storage_load_test_source_service(),
        storage_run_compiler_service=get_storage_run_compiler_service(),
        storage_delete_service=get_storage_delete_service(),
    )


def get_test_test_stage_usecase():
    return TestTestStageUseCase(
        match_get_best_service=get_match_get_best_service(),
    )


def get_student_run_build_stage_usecase():
    return StudentRunBuildStageUseCase(
        student_submission_get_source_content_service=get_student_submission_get_source_content_service(),
        student_dynamic_clear_service=get_student_dynamic_clear_service(),
        student_dynamic_set_source_content_service=get_student_dynamic_set_source_content_service(),
        student_submission_get_checksum_service=get_student_submission_get_checksum_service(),
        student_put_stage_result_service=get_student_put_stage_result_service(),

    )


# StudentRunCompileStageUseCase
def get_student_run_compile_stage_usecase():
    return StudentRunCompileStageUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_student_source_service=get_storage_load_student_source_service(),
        storage_store_student_executable_service=get_storage_store_student_executable_service(),
        storage_run_compiler_service=get_storage_run_compiler_service(),
        storage_delete_service=get_storage_delete_service(),
        student_put_stage_result_service=get_student_put_stage_result_service(),
    )


# StudentRunExecuteStageUseCase
def get_student_run_execute_stage_usecase():
    return StudentRunExecuteStageUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_student_executable_service=get_storage_load_student_executable_service(),
        storage_load_execute_config_input_files_service=get_storage_load_execute_config_input_files_service(),
        storage_take_snapshot_service=get_storage_take_snapshot_service(),
        storage_delete_service=get_storage_delete_service(),
        testcase_config_get_execute_config_mtime_service=get_testcase_config_get_execute_config_mtime_service(),
        storage_run_executable_service=get_storage_run_executable_service(),
        testcase_config_get_execute_options_service=get_testcase_config_get_execute_options_service(),
        storage_create_output_file_mapping_from_diff_service=get_storage_create_output_file_mapping_from_diff_service(),
        storage_write_stdout_file_service=get_storage_write_stdout_file_service(),
        student_put_stage_result_service=get_student_put_stage_result_service(),
    )


# StudentRunTestUseCase
def get_student_run_test_stage_usecase():
    return StudentRunTestStageUseCase(
        testcase_config_get_service=get_testcase_config_get_service(),
        testcase_config_get_test_config_mtime_service=get_testcase_config_get_test_config_mtime_service(),
        match_get_best_service=get_match_get_best_service(),
        student_put_stage_result_service=get_student_put_stage_result_service(),
        student_get_stage_result_service=get_student_get_stage_result_service(),
    )


def get_student_run_next_stage_usecase():
    return StudentRunNextStageUseCase(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
        student_stage_result_rollback_service=get_student_stage_result_rollback_service(),
        student_run_build_stage_usecase=get_student_run_build_stage_usecase(),
        student_run_compile_stage_usecase=get_student_run_compile_stage_usecase(),
        student_run_execute_stage_usecase=get_student_run_execute_stage_usecase(),
        student_run_test_stage_usecase=get_student_run_test_stage_usecase(),
        student_stage_path_result_check_rollback_service=get_student_stage_path_result_check_rollback_service(),
    )


# TestCaseListEditListSummaryUseCase
def get_testcase_list_edit_list_summary_usecase():
    return TestCaseListEditListSummaryUseCase(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseListEditCreateNewNameUseCase
def get_testcase_list_edit_create_new_name_usecase():
    return TestCaseListEditCreateNewNameUseCase(
        testcase_config_list_id_sub_service=get_testcase_config_list_id_sub_service(),
    )


# TestCaseListEditCreateTestCaseUseCase
def get_testcase_list_edit_create_testcase_usecase():
    return TestCaseListEditCreateTestCaseUseCase(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseListEditCopyTestCaseUseCase
def get_testcase_list_edit_copy_testcase_usecase():
    return TestCaseListEditCopyTestCaseUseCase(
        testcase_config_copy_service=get_testcase_config_copy_service(),
    )


# StudentStageResultTakeDiffSnapshotUseCase
def get_student_dynamic_take_diff_snapshot_usecase():
    return StudentDynamicTakeDiffSnapshotUseCase(
        student_stage_result_check_timestamp_query_service=get_student_stage_result_check_timestamp_query_service(),
        student_mark_check_timestamp_query_service=get_student_mark_check_timestamp_query_service(),
    )


# StudentStageResultClearUseCase
def get_student_stage_result_clear_usecase():
    return StudentStageResultClearUseCase(
        student_stage_result_clear_service=get_student_stage_result_clear_service(),
    )


# TestCaseConfigGetUseCase
def get_testcase_config_get_usecase():
    return TestCaseConfigGetUseCase(
        testcase_config_get_service=get_testcase_config_get_service(),
    )


# TestCaseConfigPutUseCase
def get_testcase_config_put_usecase():
    return TestCaseConfigPutUseCase(
        testcase_config_put_service=get_testcase_config_put_service(),
    )


def get_testcase_config_list_id_usecase():
    return TestCaseConfigListIDUseCase(
        testcase_config_list_id_sub_service=get_testcase_config_list_id_sub_service(),
    )


# StudentMarkViewDataGetTestResultUseCase
def get_student_mark_view_data_get_test_result_usecase():
    return StudentMarkViewDataGetTestResultUseCase(
        stage_path_get_by_testcase_id_service=get_stage_path_get_by_testcase_id_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
    )


# StudentMarkViewDataGetMarkSummaryUseCase
def get_student_mark_view_data_get_mark_summary_usecase():
    return StudentMarkViewDataGetMarkSummaryUseCase(
        student_get_service=get_student_get_service(),
        student_mark_get_sub_service=get_student_mark_get_sub_service(),
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
        student_stage_path_result_check_rollback_service=get_student_stage_path_result_check_rollback_service(),
    )


# StudentSourceCodeGetUseCase
def get_student_source_code_get_usecase():
    return StudentSourceCodeGetUseCase(
        student_source_code_get_query_service=get_student_dynamic_get_source_content_service(),
    )


# StudentMarkGetUseCase
def get_student_mark_get_usecase():
    return StudentMarkGetUseCase(
        student_mark_get_sub_service=get_student_mark_get_sub_service(),
    )


# StudentMarkPutUseCase
def get_student_mark_put_usecase():
    return StudentMarkPutUseCase(
        student_mark_put_service=get_student_mark_put_service(),
    )


# StudentMarkListUseCase
def get_student_mark_list_usecase():
    return StudentMarkListUseCase(
        student_mark_list_service=get_student_mark_list_service(),
    )


# ResourceUsageGetUseCase
def get_resource_usage_get_usecase():
    return ResourceUsageGetUseCase(
        resource_usage_io=get_resource_usage_io(),
    )
