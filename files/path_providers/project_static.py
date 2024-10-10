from pathlib import Path

from domain.models.values import StudentID, ProjectID
from files.path_providers.project import ProjectPathProvider


class ProjectStaticPathProvider:
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            current_project_id: ProjectID,
    ):
        self._project_path_provider = project_path_provider
        self._current_project_id = current_project_id

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.static_data_folder_fullpath(
            project_id=self._current_project_id,
        )

    # 生徒マスタ
    def student_master_json_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "student_master.json"

    # テストケース構成群
    def testcase_folder_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "testcases"

    # 展開した提出レポートデータ群
    def report_submission_folder_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "reports"


class ReportSubmissionPathProvider:
    def __init__(self, *, project_static_path_provider: ProjectStaticPathProvider):
        self._project_static_path_provider = project_static_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_static_path_provider.report_submission_folder_fullpath()

    # 生徒の展開した提出データが入るフォルダ
    def student_submission_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.base_folder_fullpath() / str(student_id)
