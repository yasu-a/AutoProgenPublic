from application.dependency.services import *
from usecases.project_create import ProjectCreateUseCase
from usecases.project_get import ProjectNameExistUseCase
from usecases.project_static_initialize import ProjectStaticInitializeUseCase
from usecases.recent_project_list import RecentProjectListUseCase


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
