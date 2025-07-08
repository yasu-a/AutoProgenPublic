from pathlib import Path

from domain.models.stages import AbstractStage
from domain.models.values import TestCaseID, StudentID, ProjectID, StorageID
from infra.path_providers.project import ProjectPathProvider


# テストケース
class TestCaseConfigPathProvider:
    def __init__(
            self,
            *,
            current_project_id: ProjectID,
            project_path_provider: ProjectPathProvider,
    ):
        self._current_project_id = current_project_id
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.testcase_config_folder_fullpath(
            project_id=self._current_project_id,
        )

    def testcase_folder_fullpath(self, testcase_id: TestCaseID) -> Path:
        return self.base_folder_fullpath() / str(testcase_id)

    def execute_config_json_fullpath(self, testcase_id: TestCaseID) -> Path:
        return self.testcase_folder_fullpath(testcase_id) / "execute_config.json"

    def test_config_json_fullpath(self, testcase_id: TestCaseID) -> Path:
        return self.testcase_folder_fullpath(testcase_id) / "test_config.json"


# 採点データ
class StudentMarkPathProvider:
    def __init__(
            self,
            *,
            current_project_id: ProjectID,
            project_path_provider: ProjectPathProvider,
    ):
        self._current_project_id = current_project_id
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._project_path_provider.mark_data_folder_fullpath(
            project_id=self._current_project_id,
        ) / str(student_id)

    def student_mark_data_json_fullpath(self, student_id: StudentID) -> Path:
        return self.base_folder_fullpath(student_id) / "__mark_data.json"


# プロジェクトの処理過程で生成されるデータ
class DynamicPathProvider:
    def __init__(
            self,
            *,
            current_project_id: ProjectID,
            project_path_provider: ProjectPathProvider,
    ):
        self._current_project_id = current_project_id
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.dynamic_data_folder_fullpath(
            self._current_project_id
        )

    def io_session_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "storage"

    def student_folder_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "students"


# データベースのパス
class DatabasePathProvider:
    def __init__(
            self,
            *,
            dynamic_path_provider: DynamicPathProvider,
    ):
        self._dynamic_path_provider = dynamic_path_provider

    def fullpath(self) -> Path:
        return self._dynamic_path_provider.base_folder_fullpath() / "database.sqlite3"


# コンパイル・実行関連で使うファイル操作を行うためのストレージ領域
class StoragePathProvider:
    def __init__(
            self,
            *,
            dynamic_path_provider: DynamicPathProvider,
    ):
        self._dynamic_path_provider = dynamic_path_provider

    def base_folder_fullpath(self, io_session_id: StorageID):
        return self._dynamic_path_provider.io_session_fullpath() / str(io_session_id)


# 生徒のプロジェクトの処理過程で生成されるデータ
class StudentDynamicPathProvider:
    def __init__(
            self,
            *,
            dynamic_path_provider: DynamicPathProvider,
    ):
        self._dynamic_path_provider = dynamic_path_provider

    def base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._dynamic_path_provider.student_folder_fullpath() / str(student_id)

    def results_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.base_folder_fullpath(student_id) / "__results__"


class StudentStageResultPathProvider:
    def __init__(
            self,
            *,
            student_dynamic_path_provider: StudentDynamicPathProvider,
    ):
        self._student_dynamic_path_provider = student_dynamic_path_provider

    def base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._student_dynamic_path_provider.results_folder_fullpath(student_id)

    def result_json_fullpath(self, student_id: StudentID, stage: AbstractStage) -> Path:
        filename \
            = f"{stage.get_name()}_" + "_".join(stage.list_context_elements_str()) + ".json"
        return self.base_folder_fullpath(student_id) / filename


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

    # 展開した提出レポートデータ群
    def report_submission_folder_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "reports"


class StudentSubmissionPathProvider:
    def __init__(self, *, project_static_path_provider: ProjectStaticPathProvider):
        self._project_static_path_provider = project_static_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_static_path_provider.report_submission_folder_fullpath()

    # 生徒の展開した提出データが入るフォルダ
    def student_submission_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.base_folder_fullpath() / str(student_id)
