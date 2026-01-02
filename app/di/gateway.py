from app.di.path_config import *
from app.di.repository import get_current_project_repository, get_student_repository
from app.di.system import get_current_project_core_io, get_project_core_io, \
    get_project_folder_show_in_explorer_io, get_student_folder_show_in_explorer_io
from shared.infra.gateway.student_submission_projman import (
    StudentSubmissionListSourceRelativePathGateway,
    StudentSubmissionGetFileContentGateway,
)
from feature.setting.infra.gateway.compiler_location import VSFindCompilerPathGateway
from shared.infra.gateway.current_datetime import CurrentDatetimeGateway
from shared.infra.gateway.project import (
    ProjectListGateway,
    ProjectConfigStateGateway,
    ProjectFileSystemGateway,
)
from shared.infra.gateway.student_submission import (
    StudentSubmissionGetSourceContentGateway,
    StudentSubmissionGetChecksumGateway,
    StudentSubmissionFolderShowGateway,
)


def get_project_list_gateway():
    return ProjectListGateway(
        project_list_path_provider=get_project_list_path_provider(),
    )


def get_project_config_state_gateway():
    from app.di.provider import get_app_version_provider
    return ProjectConfigStateGateway(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
        app_version_provider=get_app_version_provider(),
    )


def get_project_file_system_gateway():
    return ProjectFileSystemGateway(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
        project_folder_show_in_explorer_io=get_project_folder_show_in_explorer_io(),
    )


def get_student_submission_list_source_relative_path_gateway():
    return StudentSubmissionListSourceRelativePathGateway(
        student_submission_path_provider=get_student_submission_path_provider(),
        current_project_core_io=get_current_project_core_io(),
        current_project_repo=get_current_project_repository(),
    )


def get_student_submission_get_file_content_gateway():
    return StudentSubmissionGetFileContentGateway(
        student_submission_path_provider=get_student_submission_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_student_submission_get_source_content_gateway():
    return StudentSubmissionGetSourceContentGateway(
        student_submission_list_source_relative_path_gateway=get_student_submission_list_source_relative_path_gateway(),
        student_submission_get_file_content_gateway=get_student_submission_get_file_content_gateway(),
        student_repo=get_student_repository(),
    )


def get_student_submission_get_checksum_gateway():
    return StudentSubmissionGetChecksumGateway(
        student_submission_path_provider=get_student_submission_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_student_submission_folder_show_gateway():
    return StudentSubmissionFolderShowGateway(
        student_folder_show_in_explorer_io=get_student_folder_show_in_explorer_io(),
    )


def get_current_datetime_gateway():
    return CurrentDatetimeGateway()


def get_find_compiler_path_gateway():
    from pathlib import Path
    return VSFindCompilerPathGateway(
        start_locations=[Path(r"C:\Program Files\Microsoft Visual Studio")],
    )


# Export Gateways
def get_json_score_export_gateway():
    from feature.export.infra.gateway.json_export import JsonScoreExportGateway
    return JsonScoreExportGateway()


def get_csv_score_export_gateway():
    from feature.export.infra.gateway.csv_export import CsvScoreExportGateway
    return CsvScoreExportGateway()


def get_excel_gateway():
    from shared.infra.gateway.excel_gateway import ExcelGateway
    return ExcelGateway()


def get_excel_backup_gateway():
    from feature.export.infra.gateway.excel_backup import ExcelBackupGateway
    return ExcelBackupGateway()
