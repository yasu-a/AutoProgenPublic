from application.dependency.path_provider import *
from application.state.current_project import require_current_project_id
from domain.model.value import ProjectID
from infra.io.compile_tool import CompileToolIO
from infra.io.executable import ExecutableIO
from infra.io.project_base_folder_show_in_explorer import ProjectFolderShowInExplorerIO
from infra.io.project_database import ProjectDatabaseIO
from infra.io.report_archive import ManabaReportArchiveIO
from infra.io.resource_usage import ResourceUsageIO
from infra.io.score_excel import ScoreExcelIO
from infra.io.student_folder_show_in_explorer import StudentFolderShowInExplorerIO


def get_manaba_report_archive_io(manaba_report_archive_fullpath: Path):
    return ManabaReportArchiveIO(
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


def get_compile_tool_io():
    return CompileToolIO()


def get_executable_io():
    return ExecutableIO()


def get_score_excel_io(excel_fullpath: Path):
    return ScoreExcelIO(
        excel_fullpath=excel_fullpath,
    )


def get_student_folder_show_in_explorer_io():
    return create_student_folder_show_in_explorer_io(require_current_project_id())


def create_student_folder_show_in_explorer_io(project_id: ProjectID):
    return StudentFolderShowInExplorerIO(
        student_submission_path_provider=create_student_submission_path_provider(project_id),
    )


def get_project_folder_show_in_explorer_io():
    return ProjectFolderShowInExplorerIO(
        project_list_path_provider=get_project_list_path_provider(),
    )


def create_project_database_io(project_id: ProjectID):
    return ProjectDatabaseIO(
        database_path_provider=create_database_path_provider(project_id),
    )


def get_project_database_io():
    return create_project_database_io(require_current_project_id())


def get_resource_usage_io():
    return ResourceUsageIO()
