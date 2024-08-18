from pathlib import Path
from typing import Iterable

from domain.models.values import StudentID, TestCaseID, ProjectName


class ProjectPathProviderWithoutDependency:
    def __init__(self, project_list_folder_fullpath: Path):
        self._base = project_list_folder_fullpath

    def project_config_json_fullpath(self, project_name: ProjectName) -> Path:
        return self._base / str(project_name) / "config.json"


class ProjectPathProvider:
    def __init__(self, *, project_folder_fullpath):
        self._base = project_folder_fullpath

    # プロジェクト
    def project_folder_fullpath(self) -> Path:
        return self._base

    def project_config_json_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "config.json"

    # 提出レポート
    def report_folder_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "reports"

    def student_submission_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.report_folder_fullpath() / f"{student_id}"

    # 提出レポートに付属するマスターデータ
    def student_master_excel_fullpath(self) -> Path:
        return self.report_folder_fullpath() / "reportlist.xlsx"

    def student_master_json_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "student_master.json"

    # ビルド
    def build_folder_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "build"

    def student_build_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.build_folder_fullpath() / str(student_id)

    def student_target_source_file_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "main.c"

    def student_build_result_json_fullpath(self,
                                           student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "__build_result.json"

    # コンパイル
    def student_executable_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "main.exe"

    def student_compile_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "__compile_result.json"

    # テストケース構成
    def testcase_folder_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "testcase"

    def testcase_config_json_fullpath(self, testcase_id: TestCaseID) -> Path:
        return self.testcase_folder_fullpath() / f"{testcase_id}.json"

    # テスト実行
    def test_folder_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "test"

    def student_test_base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.test_folder_fullpath() / str(student_id)

    def student_test_folder_fullpath(self, student_id: StudentID,
                                     testcase_id: TestCaseID) -> Path:
        return self.student_test_base_folder_fullpath(student_id) / str(testcase_id)

    def student_execute_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self.student_test_base_folder_fullpath(student_id) / "__execute_result.json"

    def student_test_stdin_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.student_test_folder_fullpath(student_id, testcase_id) / "__stdin__"

    def student_test_stdout_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.student_test_folder_fullpath(student_id, testcase_id) / "__stdout__"

    def student_test_executable_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.student_test_folder_fullpath(student_id, testcase_id) / "main.exe"

    # 採点

    def student_mark_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.project_folder_fullpath() / "mark" / str(student_id)

    def student_mark_data_json_fullpath(self, student_id: StudentID) -> Path:
        return self.student_mark_folder_fullpath(student_id) / "__mark_result.json"

    # その他
    def iter_student_dynamic_folder_fullpath(self, student_id: StudentID) -> Iterable[Path]:
        # 生徒のプロジェクトデータの最終更新時刻を確認するフォルダのパスをイテレートする
        build_folder_fullpath = self.student_build_folder_fullpath(student_id)
        yield build_folder_fullpath

        test_base_folder_fullpath = self.student_test_base_folder_fullpath(student_id)
        yield test_base_folder_fullpath
        if test_base_folder_fullpath.exists():
            for path in test_base_folder_fullpath.iterdir():
                if path.is_dir():
                    yield path

    # ビルドテストセッション（コンパイラと実行の試験）
    def test_session_folder_fullpath(self, session_name: str) -> Path:
        return self._base / "__compile_test_sessions__" / session_name

    def test_session_source_fullpath(self, session_name: str) -> Path:
        return self.test_session_folder_fullpath(session_name) / "test.c"

    def test_session_executable_fullpath(self, session_name: str) -> Path:
        return self.test_session_folder_fullpath(session_name) / "test.exe"
