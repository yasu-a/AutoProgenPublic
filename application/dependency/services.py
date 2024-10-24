from application.dependency.io import get_manaba_report_archive_io
from application.dependency.repositories import *
from services.current_project_get import CurrentProjectGetService
from services.project_create import ProjectCreateService
from services.project_list import ProjectListService
from services.stage import StageListRootSubService, StageListChildSubService, \
    StageGetParentSubService
from services.stage_path import StagePathListService
from services.student_get import StudentGetService
from services.student_list import StudentListService
from services.student_master_create import StudentMasterCreateService
from services.student_stage_path_result import StudentProgressCheckTimestampQueryService, \
    StudentStagePathResultGetService
from services.student_submission_exist import StudentSubmissionExistService
from services.student_submission_extract import StudentSubmissionExtractService
from services.student_submission_folder_show import \
    StudentSubmissionFolderShowService
from services.testcase import TestCaseListIDSubService


def get_project_list_service():
    return ProjectListService(
        project_repo=get_project_repository(),
    )


def get_project_create_service():
    return ProjectCreateService(
        project_repo=get_project_repository(),
    )


def get_student_master_create_service(manaba_report_archive_fullpath: Path):
    return StudentMasterCreateService(
        student_repo=get_student_repository(),
        manaba_report_archive_io=get_manaba_report_archive_io(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
    )


def get_student_submission_extract_service(manaba_report_archive_fullpath: Path):
    return StudentSubmissionExtractService(
        student_repo=get_student_repository(),
        manaba_report_archive_io=get_manaba_report_archive_io(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        current_project_core_io=get_current_project_core_io(),
        report_submission_path_provider=get_report_submission_path_provider(),
    )


def get_current_project_get_service():
    return CurrentProjectGetService(
        current_project_repo=get_current_project_repository(),
    )


def get_student_list_service():
    return StudentListService(
        student_repo=get_student_repository(),
    )


def get_student_submission_folder_show_service():
    return StudentSubmissionFolderShowService(
        student_folder_show_in_explorer_io=get_student_folder_show_in_explorer_io(),
    )


def get_student_submission_exist_service():
    return StudentSubmissionExistService(
        student_repo=get_student_repository(),
    )


def get_student_get_service():
    return StudentGetService(
        student_repo=get_student_repository(),
    )


def get_testcase_list_id_sub_service():
    return TestCaseListIDSubService(
        testcase_config_repo=get_testcase_config_repository(),
    )


def get_stage_list_root_sub_service():
    return StageListRootSubService()


def get_stage_list_child_sub_service():
    return StageListChildSubService(
        testcase_list_id_sub_service=get_testcase_list_id_sub_service(),
    )


def get_stage_get_parent_sub_service():
    return StageGetParentSubService()


def get_stage_path_list_service():
    return StagePathListService(
        stage_list_root_sub_service=get_stage_list_root_sub_service(),
        stage_list_child_sub_service=get_stage_list_child_sub_service(),
    )


def get_student_stage_path_result_get_service():
    return StudentStagePathResultGetService(
        student_stage_result_repo=get_student_stage_result_repository(),
    )


def get_student_progress_check_timestamp_query_service():
    return StudentProgressCheckTimestampQueryService(
        student_stage_result_path_provider=get_student_stage_result_path_provider(),
        testcase_config_repo=get_testcase_config_repository(),
    )
