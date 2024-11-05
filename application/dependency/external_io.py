from application.dependency.path_provider import *
from infra.external.compile_tool import CompileToolIO
from infra.external.executable import ExecutableIO
from infra.external.project_base_folder_show_in_explorer import ProjectFolderShowInExplorerIO
from infra.external.report_archive import ManabaReportArchiveIO
from infra.external.score_excel import ScoreExcelIO
from infra.external.student_folder_show_in_explorer import StudentFolderShowInExplorerIO


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
    return StudentFolderShowInExplorerIO(
        student_submission_path_provider=get_student_submission_path_provider(),
    )


def get_project_folder_show_in_explorer_io():
    return ProjectFolderShowInExplorerIO(
        project_list_path_provider=get_project_list_path_provider(),
    )
