import sys
from dataclasses import dataclass
from pathlib import Path

from domain.model.value import ProjectID, StorageID, StudentID, TestCaseID


@dataclass(frozen=True)
class AppPathConfig:
    """
    production / testing で異なる root 設定を持つ値オブジェクト。

    このクラスは「root がどこか」だけを知る。
    settings.json や project 内部構造などの具体的な配置規則は知らない。
    """

    app_base_dir: Path
    project_store_dir: Path

    @classmethod
    def production(cls) -> "AppPathConfig":
        app_base_dir = Path(sys.argv[0]).resolve().parent
        return cls(
            app_base_dir=app_base_dir,
            project_store_dir=Path("~/AutoProgenProjects").expanduser().resolve(),
        )

    @classmethod
    def testing(cls, test_root: Path) -> "AppPathConfig":
        return cls(
            app_base_dir=(test_root / "global").resolve(),
            project_store_dir=(test_root / "AutoProgenProjects").resolve(),
        )


@dataclass(frozen=True)
class AppPathLayout:
    """
    アプリ全体の固定ファイル配置を表す値オブジェクト。

    project_store_dir の中で何を1プロジェクトとみなすか、
    project_id をどの project folder に対応させるか、
    project folder 内の config.json をどう読むかは知らない。
    それらは ProjectRepository の責務とする。
    """

    config: AppPathConfig

    @property
    def settings_json(self) -> Path:
        return self.config.app_base_dir / "settings.json"

    @property
    def app_version_json(self) -> Path:
        return self.config.app_base_dir / "app_version.json"

    @property
    def compiler_test_source_file(self) -> Path:
        return self.config.app_base_dir / "vctest" / "test.c"


@dataclass(frozen=True)
class ProjectPathLayout:
    """
    1プロジェクト内部のファイル配置を表す値オブジェクト。

    project_id から root をどう決めるかは知らない。
    すでに決定された root の内側で、config / database / testcase /
    submission / storage がどこにあるかだけを知る。
    """

    project_id: ProjectID
    root: Path

    @property
    def config_json(self) -> Path:
        return self.root / "config.json"

    @property
    def database_path(self) -> Path:
        return self.dynamic_dir / "database.sqlite3"

    @property
    def testcases_dir(self) -> Path:
        return self.root / "testcases"

    def testcase_dir(self, testcase_id: TestCaseID) -> Path:
        return self.testcases_dir / str(testcase_id)

    def execute_config_json(self, testcase_id: TestCaseID) -> Path:
        return self.testcase_dir(testcase_id) / "execute_config.json"

    def test_config_json(self, testcase_id: TestCaseID) -> Path:
        return self.testcase_dir(testcase_id) / "test_config.json"

    @property
    def static_dir(self) -> Path:
        return self.root / "static"

    @property
    def reports_dir(self) -> Path:
        return self.static_dir / "reports"

    def student_submission_dir(self, student_id: StudentID) -> Path:
        return self.reports_dir / str(student_id)

    @property
    def dynamic_dir(self) -> Path:
        return self.root / "dynamic"

    @property
    def storage_root_dir(self) -> Path:
        return self.dynamic_dir / "storage"

    def storage_dir(self, storage_id: StorageID) -> Path:
        return self.storage_root_dir / str(storage_id)
