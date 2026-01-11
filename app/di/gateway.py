from app.di.path_config import *
from app.di.repository import get_current_project_repository, get_student_repository
from app.di.state import get_current_project_id_state
from app.di.system import get_current_project_core_io, get_project_core_io, get_project_database_io
from feature.projman.infra.gateway.project import ProjectListGateway, ProjectConfigStateGateway, \
    ProjectFileSystemGateway
from feature.projman.infra.gateway.student_submission import \
    StudentSubmissionListSourceRelativePathGateway, StudentSubmissionGetFileContentGateway
from feature.setting.infra.gateway.compiler_location import VSFindCompilerPathGateway
from shared.domain.interface.gateway import IDatabaseInitializeGateway
from shared.infra.gateway.current_datetime import CurrentDatetimeGateway
from shared.infra.gateway.database_initialize_gateway import DatabaseInitializeGateway
from shared.infra.gateway.student_submission import (
    StudentSubmissionGetSourceContentGateway,
    StudentSubmissionGetChecksumGateway,
    StudentSubmissionFolderShowGateway,
)


def get_project_list_gateway():
    path_config = get_path_config()
    return ProjectListGateway(
        project_list_folder_fullpath=path_config.project_list_folder_fullpath,
    )


def get_project_config_state_gateway():
    from app.di.provider import get_app_version_provider
    path_config = get_path_config()
    return ProjectConfigStateGateway(
        project_config_json_fullpath=path_config.project_config_json_fullpath,
        project_core_io=get_project_core_io(),
        app_version_provider=get_app_version_provider(),
    )


def get_project_file_system_gateway():
    path_config = get_path_config()
    return ProjectFileSystemGateway(
        project_folder_fullpath=path_config.project_folder_fullpath,
        project_list_folder_fullpath=path_config.project_list_folder_fullpath,
        project_core_io=get_project_core_io(),
        folder_show_in_explorer_gateway=get_folder_show_in_explorer_gateway(),
    )


def get_student_submission_list_source_relative_path_gateway():
    path_config = get_path_config()
    current_project_id = get_current_project_id_state().get()
    return StudentSubmissionListSourceRelativePathGateway(
        student_submission_folder_fullpath=lambda
            s_id: path_config.student_submission_folder_fullpath(current_project_id, s_id),
        current_project_core_io=get_current_project_core_io(),
        current_project_repo=get_current_project_repository(),
    )


def get_student_submission_get_file_content_gateway():
    path_config = get_path_config()
    current_project_id = get_current_project_id_state().get()
    return StudentSubmissionGetFileContentGateway(
        student_submission_folder_fullpath=lambda
            s_id: path_config.student_submission_folder_fullpath(current_project_id, s_id),
        current_project_core_io=get_current_project_core_io(),
    )


def get_student_submission_get_source_content_gateway():
    return StudentSubmissionGetSourceContentGateway(
        student_submission_list_source_relative_path_gateway=get_student_submission_list_source_relative_path_gateway(),
        student_submission_get_file_content_gateway=get_student_submission_get_file_content_gateway(),
        student_repo=get_student_repository(),
    )


def get_student_submission_get_checksum_gateway():
    path_config = get_path_config()
    current_project_id = get_current_project_id_state().get()
    return StudentSubmissionGetChecksumGateway(
        student_submission_folder_fullpath=lambda
            s_id: path_config.student_submission_folder_fullpath(current_project_id, s_id),
        current_project_core_io=get_current_project_core_io(),
    )


def get_student_submission_folder_show_gateway():
    path_config = get_path_config()
    current_project_id = get_current_project_id_state().get()
    return StudentSubmissionFolderShowGateway(
        student_submission_folder_fullpath=lambda
            s_id: path_config.student_submission_folder_fullpath(current_project_id, s_id),
        folder_show_in_explorer_gateway=get_folder_show_in_explorer_gateway(),
    )


def get_current_datetime_gateway():
    return CurrentDatetimeGateway()


def get_resource_usage_gateway():
    from shared.infra.gateway.resource_usage import ResourceUsageGateway
    return ResourceUsageGateway()


def get_folder_show_in_explorer_gateway():
    from shared.infra.gateway.folder_show_in_explorer import FolderShowInExplorerGateway
    return FolderShowInExplorerGateway()


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


def get_database_initialize_gateway() -> IDatabaseInitializeGateway:
    return DatabaseInitializeGateway(db_io=get_project_database_io())
