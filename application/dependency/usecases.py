from application.dependency.services import *
from usecases.compile_test import CompileTestRunUseCase
from usecases.compiler import CompilerSearchUseCase
from usecases.current_project import CurrentProjectSummaryGetUseCase
from usecases.global_config import GlobalConfigGetUseCase, GlobalConfigPutUseCase
from usecases.project import ProjectCheckExistByNameUseCase, ProjectCreateUseCase, \
    ProjectInitializeStaticUseCase, ProjectListRecentSummaryUseCase
from usecases.student import StudentListIDUseCase
from usecases.student_dynamic import StudentDynamicTakeDiffSnapshotUseCase
from usecases.student_mark import StudentMarkGetUseCase, StudentMarkPutUseCase, \
    StudentMarkListUseCase
from usecases.student_mark_view_data import StudentMarkViewDataGetTestResultUseCase, \
    StudentMarkViewDataGetMarkSummaryUseCase
from usecases.student_run_build import StudentRunBuildStageUseCase
from usecases.student_run_compile import StudentRunCompileStageUseCase
from usecases.student_run_execute import StudentRunExecuteStageUseCase
from usecases.student_run_next_stage import StudentRunNextStageUseCase
from usecases.student_run_test import StudentRunTestStageUseCase
from usecases.student_source_code import StudentSourceCodeGetUseCase
from usecases.student_stage_result import StudentStageResultClearUseCase
from usecases.student_submission_folder_show import StudentSubmissionFolderShowUseCase
from usecases.student_table_cell_data import StudentTableGetStudentIDCellDataUseCase, \
    StudentTableGetStudentNameCellDataUseCase, StudentTableGetStudentStageStateCellDataUseCase, \
    StudentTableGetStudentErrorCellDataUseCase
from usecases.testcase_config import TestCaseConfigGetUseCase, TestCaseConfigPutUseCase, \
    TestCaseConfigListIDUseCase
from usecases.testcase_list_edit import TestCaseListEditListSummaryUseCase, \
    TestCaseListEditCreateNewNameUseCase, TestCaseListEditCreateTestCaseUseCase


def get_global_config_get_usecase():
    return GlobalConfigGetUseCase(
        global_config_get_service=get_global_config_get_service(),
    )


def get_global_config_put_usecase():
    return GlobalConfigPutUseCase(
        global_config_put_service=get_global_config_put_service(),
    )


def get_project_list_recent_summary_usecase():
    return ProjectListRecentSummaryUseCase(
        project_list_service=get_project_list_service(),
    )


def get_project_create_usecase():
    return ProjectCreateUseCase(
        project_create_service=get_project_create_service(),
    )


def get_project_initialize_static_usecase(manaba_report_archive_fullpath: Path):
    return ProjectInitializeStaticUseCase(
        student_master_create_service=get_student_master_create_service(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        student_submission_extract_service=get_student_submission_extract_service(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
    )


def get_project_check_exist_by_name_usecase():
    return ProjectCheckExistByNameUseCase(
        project_list_service=get_project_list_service(),
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


def get_compile_test_run_usecase():
    return CompileTestRunUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_test_source_service=get_storage_load_test_source_service(),
        storage_run_compiler_service=get_storage_run_compiler_service(),
        storage_delete_service=get_storage_delete_service(),
    )


def get_student_run_build_stage_usecase():
    return StudentRunBuildStageUseCase(
        student_submission_get_source_content_service=get_student_submission_get_source_content_service(),
        student_stage_result_repo=get_student_stage_result_repository(),
        student_dynamic_clear_service=get_student_dynamic_clear_service(),
        student_dynamic_set_source_content_service=get_student_dynamic_set_source_content_service(),
        student_submission_get_checksum_service=get_student_submission_get_checksum_service(),
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


# StudentRunCompileStageUseCase
def get_student_run_compile_stage_usecase():
    return StudentRunCompileStageUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_student_source_service=get_storage_load_student_source_service(),
        storage_store_student_executable_service=get_storage_store_student_executable_service(),
        storage_run_compiler_service=get_storage_run_compiler_service(),
        storage_delete_service=get_storage_delete_service(),
        student_stage_result_repo=get_student_stage_result_repository(),
    )


# StudentRunExecuteStageUseCase
def get_student_run_execute_stage_usecase():
    return StudentRunExecuteStageUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_student_executable_service=get_storage_load_student_executable_service(),
        storage_load_execute_config_input_files_service=get_storage_load_execute_config_input_files_service(),
        storage_take_snapshot_service=get_storage_take_snapshot_service(),
        storage_delete_service=get_storage_delete_service(),
        student_stage_result_repo=get_student_stage_result_repository(),
        testcase_config_get_execute_config_mtime_service=get_testcase_config_get_execute_config_mtime_service(),
        storage_run_executable_service=get_storage_run_executable_service(),
        testcase_config_get_execute_options_service=get_testcase_config_get_execute_options_service(),
        storage_create_output_file_mapping_from_diff_service=get_storage_create_output_file_mapping_from_diff_service(),
        storage_write_stdout_file_service=get_storage_write_stdout_file_service(),
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


# StudentRunTestUseCase
def get_student_run_test_stage_usecase():
    return StudentRunTestStageUseCase(
        testcase_config_get_service=get_testcase_config_get_service(),
        student_stage_result_repo=get_student_stage_result_repository(),
        testcase_config_get_test_config_mtime_service=get_testcase_config_get_test_config_mtime_service(),
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
        student_source_code_get_query_service=get_student_source_code_get_query_service(),
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
