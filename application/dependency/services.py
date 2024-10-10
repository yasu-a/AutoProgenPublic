from application.dependency.io import get_manaba_report_archive_io
from application.dependency.repositories import *
from services.project_create import ProjectCreateService
from services.project_list import ProjectListService
from services.student_master_create import StudentMasterCreateService
from services.student_submission_extract import StudentSubmissionExtractService


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
