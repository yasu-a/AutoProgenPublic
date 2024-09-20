from pathlib import Path

from domain.models.values import StudentID, TestCaseID, IOSessionID
from files.path_providers.project import ProjectPathProvider


# プロジェクトの処理過程で生成されるデータ
class DynamicPathProvider:
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
    ):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.dynamic_data_folder_fullpath()

    def io_session_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "sessions"

    def student_folder_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "students"


# コンパイル・実行関連で使うファイル操作を行うためのセッション
class IOSessionPathProvider:
    def __init__(
            self,
            *,
            dynamic_path_provider: DynamicPathProvider,
    ):
        self._dynamic_path_provider = dynamic_path_provider

    def base_folder_fullpath(self, io_session_id: IOSessionID):
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


class StudentStageResultPathProvider:
    def __init__(
            self,
            *,
            student_dynamic_path_provider: StudentDynamicPathProvider,
    ):
        self._student_dynamic_path_provider = student_dynamic_path_provider

    # 結果
    def result_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._student_dynamic_path_provider.base_folder_fullpath(student_id) / "results"

    def build_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self.result_folder_fullpath(student_id) / "build.json"

    def compile_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self.result_folder_fullpath(student_id) / "compile.json"

    def execute_result_json_fullpath(self, student_id: StudentID, testcase_id: TestCaseID) -> Path:
        return self.result_folder_fullpath(student_id) / f"execute_{testcase_id!s}.json"

    def test_result_json_fullpath(self, student_id: StudentID, testcase_id: TestCaseID) -> Path:
        return self.result_folder_fullpath(student_id) / f"test_{testcase_id!s}.json"
