from application.dependency.services import *
from usecases.compile_test import CompileTestUseCase
from usecases.compiler_search import CompilerSearchUseCase
from usecases.current_project_summary_get import CurrentProjectSummaryGetUseCase
from usecases.global_config import GlobalConfigGetUseCase, GlobalConfigPutUseCase
from usecases.project_create import ProjectCreateUseCase
from usecases.project_name_exist import ProjectNameExistUseCase
from usecases.project_static_initialize import ProjectStaticInitializeUseCase
from usecases.recent_project_list import RecentProjectListUseCase
from usecases.student_id_list_usecase import StudentIDListUseCase
from usecases.student_submission_folder_show import StudentSubmissionFolderShowUseCase
from usecases.student_table_get_cell_data import StudentTableGetStudentIDCellDataUseCase, \
    StudentTableGetStudentNameCellDataUseCase, StudentTableGetStudentStageStateCellDataUseCase, \
    StudentTableGetStudentErrorCellDataUseCase


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


def get_student_table_get_student_stage_state_cell_data_use_case():
    return StudentTableGetStudentStageStateCellDataUseCase(
        stage_path_list_service=get_stage_path_list_service(),
        student_stage_path_result_get_service=get_student_stage_path_result_get_service(),
    )


def get_student_table_get_student_error_cell_data_use_case():
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
