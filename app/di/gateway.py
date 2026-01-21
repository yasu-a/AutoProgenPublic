# from app.di.path_config import *
# from app.di.repository import get_current_project_repository, get_student_repository
# from app.di.state import get_current_project_id_state
# from app.di.system import get_current_project_core_io, get_project_core_io, get_project_database_io
# from feature.export.domain.interface.gateway import ISimpleScoreExportGateway, IExcelBackupGateway
# from feature.projman.domain.interface.gateway import IProjectListGateway, \
#     IProjectConfigStateGateway, IProjectFileSystemGateway, \
#     IStudentSubmissionListSourceRelativePathGateway, IStudentSubmissionGetFileContentGateway
# from feature.setting.domain.interface.gateway import IFindCompilerPathGateway
# from shared.domain.interface.gateway import IDatabaseInitializeGateway, \
#     IStudentSubmissionGetSourceContentGateway, IStudentSubmissionGetChecksumGateway, \
#     IStudentSubmissionFolderShowGateway, ICurrentDatetimeGateway, IResourceUsageGateway, \
#     IFolderShowInExplorerGateway, IExcelGateway
#
#
# def get_project_list_gateway() -> IProjectListGateway:
#     path_config = get_path_config()
#     from feature.projman.infra.gateway.project import ProjectListGateway
#     return ProjectListGateway(
#         project_list_dir=path_config.project_list_folder_fullpath,
#     )
#
#
# def get_project_config_state_gateway() -> IProjectConfigStateGateway:
#     from app.di.provider import get_app_version_provider
#     path_config = get_path_config()
#     from feature.projman.infra.gateway.project import ProjectConfigStateGateway
#     return ProjectConfigStateGateway(
#         config_json_path=path_config.project_config_json_fullpath,
#         project_core_io=get_project_core_io(),
#         app_version_provider=get_app_version_provider(),
#     )
#
#
# def get_project_file_system_gateway() -> IProjectFileSystemGateway:
#     path_config = get_path_config()
#     from feature.projman.infra.gateway.project import ProjectFileSystemGateway
#     return ProjectFileSystemGateway(
#         project_folder_fullpath=path_config.project_folder_fullpath,
#         project_list_folder_fullpath=path_config.project_list_folder_fullpath,
#         project_core_io=get_project_core_io(),
#         folder_show_in_explorer_gateway=get_folder_show_in_explorer_gateway(),
#     )
#
#
# def get_student_submission_list_source_relative_path_gateway() -> IStudentSubmissionListSourceRelativePathGateway:
#     path_config = get_path_config()
#     current_project_id = get_current_project_id_state().get()
#     from feature.projman.infra.gateway.student_submission import \
#         StudentSubmissionListSourceRelativePathGateway
#     return StudentSubmissionListSourceRelativePathGateway(
#         student_submission_folder_fullpath=lambda
#             s_id: path_config.student_submission_folder_fullpath(current_project_id, s_id),
#         current_project_core_io=get_current_project_core_io(),
#         current_project_repo=get_current_project_repository(),
#     )
#
#
# def get_student_submission_get_file_content_gateway() -> IStudentSubmissionGetFileContentGateway:
#     path_config = get_path_config()
#     current_project_id = get_current_project_id_state().get()
#     from feature.projman.infra.gateway.student_submission import \
#         StudentSubmissionGetFileContentGateway
#     return StudentSubmissionGetFileContentGateway(
#         student_submission_folder_fullpath=lambda
#             s_id: path_config.student_submission_folder_fullpath(current_project_id, s_id),
#         current_project_core_io=get_current_project_core_io(),
#     )
#
#
# def get_student_submission_get_source_content_gateway() -> IStudentSubmissionGetSourceContentGateway:
#     from shared.infra.gateway.student_submission import StudentSubmissionGetSourceContentGateway
#     return StudentSubmissionGetSourceContentGateway(
#         student_submission_list_source_relative_path_gateway=get_student_submission_list_source_relative_path_gateway(),
#         student_submission_get_file_content_gateway=get_student_submission_get_file_content_gateway(),
#         student_repo=get_student_repository(),
#     )
#
#
# def get_student_submission_get_checksum_gateway() -> IStudentSubmissionGetChecksumGateway:
#     path_config = get_path_config()
#     current_project_id = get_current_project_id_state().get()
#     from shared.infra.gateway.student_submission import StudentSubmissionGetChecksumGateway
#     return StudentSubmissionGetChecksumGateway(
#         student_submission_folder_fullpath=lambda
#             s_id: path_config.student_submission_folder_fullpath(current_project_id, s_id),
#         current_project_core_io=get_current_project_core_io(),
#     )
#
#
# def get_student_submission_folder_show_gateway() -> IStudentSubmissionFolderShowGateway:
#     path_config = get_path_config()
#     current_project_id = get_current_project_id_state().get()
#     from shared.infra.gateway.student_submission import StudentSubmissionFolderShowGateway
#     return StudentSubmissionFolderShowGateway(
#         student_submission_folder_fullpath=lambda
#             s_id: path_config.student_submission_folder_fullpath(current_project_id, s_id),
#         folder_show_in_explorer_gateway=get_folder_show_in_explorer_gateway(),
#     )
#
#
# def get_current_datetime_gateway() -> ICurrentDatetimeGateway:
#     from shared.infra.gateway.current_datetime import CurrentDatetimeGateway
#     return CurrentDatetimeGateway()
#
#
# def get_resource_usage_gateway() -> IResourceUsageGateway:
#     from shared.infra.gateway.resource_usage import ResourceUsageGateway
#     return ResourceUsageGateway()
#
#
# def get_folder_show_in_explorer_gateway() -> IFolderShowInExplorerGateway:
#     from shared.infra.gateway.folder_show_in_explorer import FolderShowInExplorerGateway
#     return FolderShowInExplorerGateway()
#
#
# def get_find_compiler_path_gateway() -> IFindCompilerPathGateway:
#     from pathlib import Path
#     from feature.setting.infra.gateway.compiler_location import VSFindCompilerPathGateway
#     return VSFindCompilerPathGateway(
#         start_locations=[Path(r"C:\Program Files\Microsoft Visual Studio")],
#     )
#
#
# # Export Gateways
# def get_json_score_export_gateway() -> ISimpleScoreExportGateway:
#     from feature.export.infra.gateway.json_export import JsonScoreExportGateway
#     return JsonScoreExportGateway()
#
#
# def get_csv_score_export_gateway() -> ISimpleScoreExportGateway:
#     from feature.export.infra.gateway.csv_export import CsvScoreExportGateway
#     return CsvScoreExportGateway()
#
#
# def get_excel_gateway() -> IExcelGateway:
#     from shared.infra.gateway.excel_gateway import ExcelGateway
#     return ExcelGateway()
#
#
# def get_excel_backup_gateway() -> IExcelBackupGateway:
#     from feature.export.infra.gateway.excel_backup import ExcelBackupGateway
#     return ExcelBackupGateway()
#
#
# def get_database_initialize_gateway() -> IDatabaseInitializeGateway:
#     from shared.infra.gateway.database_initialize_gateway import DatabaseInitializeGateway
#     return DatabaseInitializeGateway(db_io=get_project_database_io())
