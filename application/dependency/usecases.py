from application.dependency.services import *
from usecases.build import StudentRunBuildStageUseCase
from usecases.compile import CompileTestUseCase, StudentRunCompileStageUseCase
from usecases.compiler_search import CompilerSearchUseCase
from usecases.current_project_summary_get import CurrentProjectSummaryGetUseCase
from usecases.execute import StudentRunExecuteStageUseCase
from usecases.global_config import GlobalConfigGetUseCase, GlobalConfigPutUseCase
from usecases.project_create import ProjectCreateUseCase
from usecases.project_name_exist import ProjectNameExistUseCase
from usecases.project_static_initialize import ProjectStaticInitializeUseCase
from usecases.recent_project_list import RecentProjectListUseCase
from usecases.student_id_list_usecase import StudentIDListUseCase
from usecases.student_run_next_stage import StudentRunNextStageUseCase
from usecases.student_submission_folder_show import StudentSubmissionFolderShowUseCase
from usecases.student_table_cell_data import StudentTableGetStudentIDCellDataUseCase, \
    StudentTableGetStudentNameCellDataUseCase, StudentTableGetStudentStageStateCellDataUseCase, \
    StudentTableGetStudentErrorCellDataUseCase
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


def get_recent_project_list_usecase():
    return RecentProjectListUseCase(
        project_list_service=get_project_list_service(),
    )


def get_project_create_usecase():
    return ProjectCreateUseCase(
        project_create_service=get_project_create_service(),
    )


def get_project_static_initialize_usecase(manaba_report_archive_fullpath: Path):
    return ProjectStaticInitializeUseCase(
        student_master_create_service=get_student_master_create_service(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        student_submission_extract_service=get_student_submission_extract_service(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
    )


def get_project_name_exist_usecase():
    return ProjectNameExistUseCase(
        project_list_service=get_project_list_service(),
    )


def get_current_project_summary_get_usecase():
    return CurrentProjectSummaryGetUseCase(
        current_project_get_service=get_current_project_get_service(),
    )


def get_student_id_list_usecase():
    return StudentIDListUseCase(
        student_list_service=get_student_list_service(),
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
        stage_path_list_service=get_stage_path_list_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
    )


def get_student_table_get_student_error_cell_data_usecase():
    return StudentTableGetStudentErrorCellDataUseCase(
        stage_path_list_service=get_stage_path_list_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
    )


def get_compiler_search_usecase():
    return CompilerSearchUseCase()


def get_compile_test_usecase():
    return CompileTestUseCase(
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
        stage_list_child_sub_service=get_stage_list_child_sub_service(),
        stage_path_list_service=get_stage_path_list_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
        student_submission_get_checksum_service=get_student_submission_get_checksum_service(),
        testcase_config_get_execute_config_mtime_service=get_testcase_config_get_execute_config_mtime_service(),
        testcase_config_get_test_config_mtime_service=get_testcase_config_get_test_config_mtime_service(),
        student_stage_rollback_service=get_student_stage_rollback_service(),
        student_run_build_stage_usecase=get_student_run_build_stage_usecase(),
        student_run_compile_stage_usecase=get_student_run_compile_stage_usecase(),
        student_run_execute_stage_usecase=get_student_run_execute_stage_usecase(),
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
        output_files_create_from_storage_diff_service=get_output_files_create_from_storage_diff_service(),
        storage_write_stdout_file_service=get_storage_write_stdout_file_service(),
    )
