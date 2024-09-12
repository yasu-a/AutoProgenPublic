from pathlib import Path
from typing import Iterable

from domain.models.values import StudentID, TestCaseID, ProjectName


class ProjectPathProviderWithoutDependency:  # TODO: ProjectPathProviderと機能が重複
    def __init__(self, project_list_folder_fullpath: Path):
        self._base = project_list_folder_fullpath

    def config_json_fullpath(self, project_name: ProjectName) -> Path:
        return self._base / str(project_name) / "config.json"


class ProjectPathProvider:
    def __init__(self, *, project_folder_fullpath):
        self._base = project_folder_fullpath

    # プロジェクトフォルダ
    def base_folder_fullpath(self) -> Path:
        return self._base

    # プロジェクトの設定
    def config_json_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "config.json"

    # 生徒マスタ
    def student_master_json_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "student_master.json"


# テストケース
class TestCasePathProvider:
    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.base_folder_fullpath() / "testcase"

    def config_json_fullpath(self, testcase_id: TestCaseID) -> Path:
        return self.base_folder_fullpath() / f"{testcase_id}.json"


class ReportPathProvider:
    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    # 提出レポート
    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.base_folder_fullpath() / "reports"

    # 提出レポートに付属するマスターデータ
    def master_excel_fullpath(self) -> Path:
        return self.base_folder_fullpath() / "reportlist.xlsx"


class StudentReportPathProvider:
    def __init__(self, *, report_path_provider: ReportPathProvider):
        self._report_path_provider = report_path_provider

    def submission_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._report_path_provider.base_folder_fullpath() / f"{student_id}"


class BuildPathProvider:
    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.base_folder_fullpath() / "build"


# 環境構築
class StudentBuildPathProvider:
    def __init__(self, *, build_path_provider: BuildPathProvider):
        self._build_path_provider = build_path_provider

    def base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._build_path_provider.base_folder_fullpath() / str(student_id)

    def target_source_file_fullpath(self, student_id: StudentID) -> Path:
        return self.base_folder_fullpath(student_id) / "main.c"


class CompilePathProvider:
    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        # TODO: move to / "compile"
        return self._project_path_provider.base_folder_fullpath() / "build"


# コンパイル
class StudentCompilePathProvider:
    def __init__(self, *, compile_path_provider: CompilePathProvider):
        self._compile_path_provider = compile_path_provider

    def base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._compile_path_provider.base_folder_fullpath() / str(student_id)

    def executable_fullpath(self, student_id: StudentID) -> Path:
        return self.base_folder_fullpath(student_id) / "main.exe"


# 実行
class ExecutePathProvider:
    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.base_folder_fullpath() / "execute"


class StudentExecutePathProvider:
    def __init__(self, *, execute_path_provider: ExecutePathProvider):
        self._execute_path_provider = execute_path_provider

    def base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._execute_path_provider.base_folder_fullpath() / str(student_id)


class StudentTestCaseExecutePathProvider:
    def __init__(self, *, student_execute_path_provider: StudentExecutePathProvider):
        self._student_execute_path_provider = student_execute_path_provider

    def base_folder_fullpath(self, student_id: StudentID, testcase_id: TestCaseID) -> Path:
        return self._student_execute_path_provider.base_folder_fullpath(student_id) \
            / str(testcase_id)

    def student_execute_stdin_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.base_folder_fullpath(student_id, testcase_id) / "__stdin__"

    def student_execute_stdout_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.base_folder_fullpath(student_id, testcase_id) / "__stdout__"

    def student_execute_executable_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.base_folder_fullpath(student_id, testcase_id) / "main.exe"


# テスト
class TestPathProvider:
    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.base_folder_fullpath() / "test"


class StudentTestPathProvider:
    def __init__(self, *, test_path_provider: TestPathProvider):
        self._test_path_provider = test_path_provider

    def base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._test_path_provider.base_folder_fullpath() / str(student_id)


class StudentTestCaseTestPathProvider:
    def __init__(
            self,
            *,
            student_test_path_provider: StudentTestPathProvider,
    ):
        self._student_test_path_provider = student_test_path_provider

    def base_folder_fullpath(self, student_id: StudentID, testcase_id: TestCaseID) -> Path:
        return self._student_test_path_provider.base_folder_fullpath(student_id) \
            / str(testcase_id)


# 進捗
class StudentProgressPathProvider:
    def __init__(
            self,
            *,
            student_build_path_provider: StudentBuildPathProvider,
            student_compile_path_provider: StudentCompilePathProvider,
            student_execute_path_provider: StudentExecutePathProvider,
            student_test_path_provider: StudentTestPathProvider,
    ):
        self._student_build_path_provider = student_build_path_provider
        self._student_compile_path_provider = student_compile_path_provider
        self._student_execute_path_provider = student_execute_path_provider
        self._student_test_path_provider = student_test_path_provider

    def student_build_result_json_fullpath(self,
                                           student_id: StudentID) -> Path:
        return self._student_build_path_provider.base_folder_fullpath(
            student_id) / "__build_result.json"

    def student_compile_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self._student_compile_path_provider.base_folder_fullpath(
            student_id) / "__compile_result.json"

    def student_execute_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self._student_execute_path_provider.base_folder_fullpath(
            student_id) / "__execute_result.json"

    def student_test_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self._student_test_path_provider.base_folder_fullpath(
            student_id) / "__test_result.json"

    def iter_student_dynamic_folder_fullpath(self, student_id: StudentID) -> Iterable[Path]:
        # 生徒のプロジェクトデータの最終更新時刻を確認するフォルダのパスをイテレートする

        # ビルド
        yield self._student_build_path_provider.base_folder_fullpath(student_id)

        # コンパイル
        yield self._student_compile_path_provider.base_folder_fullpath(student_id)

        # 実行
        yield self._student_execute_path_provider.base_folder_fullpath(student_id)

        # テスト
        yield self._student_test_path_provider.base_folder_fullpath(student_id)


# 採点
class MarkPathProvider:
    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.base_folder_fullpath() / "mark"


class StudentMarkPathProvider:
    def __init__(self, *, mark_path_provider: MarkPathProvider):
        self._mark_path_provider = mark_path_provider

    def student_mark_folder_fullpath(self, student_id: StudentID) -> Path:
        return self._mark_path_provider.base_folder_fullpath() / "mark" / str(student_id)

    def student_mark_data_json_fullpath(self, student_id: StudentID) -> Path:
        return self.student_mark_folder_fullpath(student_id) / "__mark_data.json"


# テストセッション（コンパイラと実行の試験）
class TestSessionPathProvider:
    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def base_folder_fullpath(self) -> Path:
        return self._project_path_provider.base_folder_fullpath() / "__compile_test_sessions__"

    def test_session_folder_fullpath(self, session_name: str) -> Path:
        return self.base_folder_fullpath() / session_name

    def test_session_source_fullpath(self, session_name: str) -> Path:
        return self.test_session_folder_fullpath(session_name) / "test.c"

    def test_session_executable_fullpath(self, session_name: str) -> Path:
        return self.test_session_folder_fullpath(session_name) / "test.exe"
