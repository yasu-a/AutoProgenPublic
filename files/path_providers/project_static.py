from pathlib import Path

from domain.models.values import StudentID
from files.path_providers.project import ProjectPathProvider


class ProjectStaticPathProvider:
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
    ):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.static_data_folder_fullpath()

    # 生徒マスタ
    def student_master_json_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "student_master.json"

    # テストケース構成群
    def testcase_folder_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "testcases"

    # 提出レポートデータ群
    def report_submission_folder_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "reports"


class ReportSubmissionPathProvider:
    def __init__(self, *, static_path_provider: ProjectStaticPathProvider):
        self._static_path_provider = static_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._static_path_provider.report_submission_folder_fullpath()

    # 提出レポートに付属するマスターデータ
    def master_excel_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "reportlist.xlsx"


class StudentReportPathProvider:
    def __init__(
            self,
            *,
            student_id: StudentID,
            report_submission_path_provider: ReportSubmissionPathProvider,
    ):
        self._student_id = student_id
        self._report_submission_path_provider = report_submission_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._report_submission_path_provider.base_folder_fullpath() / str(self._student_id)
