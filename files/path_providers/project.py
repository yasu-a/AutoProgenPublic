from pathlib import Path

from domain.models.values import StudentID, TestCaseID, ProjectID


class ProjectListPathProvider:
    def __init__(self, project_list_folder_fullpath: Path):
        self._base = project_list_folder_fullpath

    def base_folder_fullpath(self) -> Path:
        return self._base

    def project_folder_fullpath(self, project_id: ProjectID) -> Path:
        return self.base_folder_fullpath() / str(project_id)


class ProjectPathProvider:
    def __init__(self, *, project_list_path_provider: ProjectListPathProvider):
        self._project_list_path_provider = project_list_path_provider

    # プロジェクトフォルダ
    def base_folder_fullpath(self, project_id: ProjectID) -> Path:
        return self._project_list_path_provider.project_folder_fullpath(project_id)

    # プロジェクトの設定
    def config_json_fullpath(self, project_id: ProjectID) -> Path:
        return self.base_folder_fullpath(project_id) / "config.json"

    # テストケース構成群のフォルダ
    def testcase_config_folder_fullpath(self, project_id: ProjectID) -> Path:
        return self.base_folder_fullpath(project_id) / "testcases"

    # 採点データ群のフォルダ
    def mark_data_folder_fullpath(self, project_id: ProjectID) -> Path:
        return self.base_folder_fullpath(project_id) / "marks"

    # プロジェクトが生成された時からある静的データがあるフォルダ
    def static_data_folder_fullpath(self, project_id: ProjectID) -> Path:
        return self.base_folder_fullpath(project_id) / "static"

    # プロジェクトが進行するにつれて自動生成されていく動的データがあるフォルダ
    def dynamic_data_folder_fullpath(self, project_id: ProjectID) -> Path:
        return self.base_folder_fullpath(project_id) / "dynamic"


# テストケース
class TestCaseConfigPathProvider:
    def __init__(
            self,
            *,
            testcase_id: TestCaseID,
            project_path_provider: ProjectPathProvider,
    ):
        self._testcase_id = testcase_id
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.testcase_config_folder_fullpath() / str(
            self._testcase_id)

    def execute_config_json_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "execute_config.json"

    def test_config_json_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "test_config.json"


# 採点データ
class StudentMarkPathProvider:
    def __init__(
            self,
            *,
            student_id: StudentID,
            project_path_provider: ProjectPathProvider,
    ):
        self._student_id = student_id
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.mark_data_folder_fullpath() / str(self._student_id)

    def student_mark_data_json_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "__mark_data.json"
