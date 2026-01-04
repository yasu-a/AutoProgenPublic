from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from shared.domain.entity.project import ProjectEntity
from shared.domain.entity.storage import StorageEntity
from shared.domain.entity.student import StudentEntity
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.entity.testcase_config import TestCaseConfigEntity
from shared.domain.model.stage import StageElement
from shared.domain.model.student_result import StudentStageStatusEntity, \
    AbstractStageResultEntity, BuildStageResultEntity, CompileStageResultEntity, \
    ExecuteStageResultEntity, TestStageResultEntity
from shared.domain.value.app_version import AppVersion
from shared.domain.value.file_item import ExecutableFileItem, SourceFileItem
from shared.domain.value.identifier import (
    ProjectID,
    StudentID,
    StorageID,
    TestCaseID,
)
from shared.domain.value.setting import Setting


class IAppNameProvider(ABC):
    """アプリケーション名を提供するインターフェース"""

    @abstractmethod
    def provide(self) -> str:
        """アプリケーション名を提供"""
        raise NotImplementedError()


class IAppVersionProvider(ABC):
    """アプリケーションバージョンを提供するインターフェース"""

    @abstractmethod
    def provide(self) -> AppVersion:
        """アプリケーションバージョンを提供"""
        raise NotImplementedError()


class IStudentRepository(ABC):
    """生徒リポジトリのインターフェース"""

    @abstractmethod
    def create_all(self, students: list[StudentEntity]) -> None:
        """すべての生徒を保存"""
        raise NotImplementedError()

    @abstractmethod
    def exists_any(self) -> bool:
        """生徒データが存在するか"""
        raise NotImplementedError()

    @abstractmethod
    def get(self, student_id: StudentID) -> StudentEntity:
        """生徒を取得"""
        raise NotImplementedError()

    @abstractmethod
    def list(self) -> list[StudentEntity]:
        """すべての生徒を取得"""
        raise NotImplementedError()


class IStudentScoreRepository(ABC):
    """生徒点数リポジトリのインターフェース"""

    @abstractmethod
    def create(self, student_id: StudentID) -> StudentMarkEntity:
        """未採点の点数データを作成"""
        raise NotImplementedError()

    @abstractmethod
    def put(self, mark: StudentMarkEntity) -> StudentMarkEntity:
        """点数データを保存"""
        raise NotImplementedError()

    @abstractmethod
    def exists(self, student_id: StudentID) -> bool:
        """点数データが存在するか"""
        raise NotImplementedError()

    @abstractmethod
    def get(self, student_id: StudentID) -> StudentMarkEntity:
        """点数データを取得"""
        raise NotImplementedError()

    @abstractmethod
    def list(self) -> list[StudentMarkEntity]:
        """すべての点数データを取得"""
        raise NotImplementedError()


class ISettingRepository(ABC):
    """設定リポジトリのインターフェース"""

    @abstractmethod
    def get(self) -> Setting:
        """設定を取得"""
        raise NotImplementedError()

    @abstractmethod
    def put(self, setting: Setting) -> None:
        """設定を保存"""
        raise NotImplementedError()


class IProjectRepository(ABC):
    """プロジェクトリポジトリのインターフェース"""

    @abstractmethod
    def get(self, project_id: ProjectID) -> ProjectEntity:
        """プロジェクトを取得"""
        raise NotImplementedError()

    @abstractmethod
    def put(self, project_entity: ProjectEntity) -> None:
        """プロジェクトを保存"""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, project_id: ProjectID) -> None:
        """プロジェクトを削除"""
        raise NotImplementedError()


class ICurrentProjectRepository(ABC):
    """現在のプロジェクトリポジトリのインターフェース"""

    @abstractmethod
    def get(self) -> ProjectEntity:
        """現在のプロジェクトを取得"""
        raise NotImplementedError()

    @abstractmethod
    def put(self, project_entity: ProjectEntity) -> None:
        """現在のプロジェクトを保存"""
        raise NotImplementedError()


class ITestCaseConfigRepository(ABC):
    """テストケース設定リポジトリのインターフェース"""

    @abstractmethod
    def exists(self, testcase_id: TestCaseID) -> bool:
        """テストケース設定が存在するか"""
        raise NotImplementedError()

    @abstractmethod
    def get(self, testcase_id: TestCaseID) -> TestCaseConfigEntity:
        """テストケース設定を取得"""
        raise NotImplementedError()

    @abstractmethod
    def list(self) -> list[TestCaseConfigEntity]:
        """すべてのテストケース設定を取得"""
        raise NotImplementedError()

    @abstractmethod
    def put(self, testcase_config: TestCaseConfigEntity) -> None:
        """テストケース設定を保存"""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, testcase_id: TestCaseID) -> None:
        """テストケース設定を削除"""
        raise NotImplementedError()


class IStorageRepository(ABC):
    """ストレージリポジトリのインターフェース"""

    @abstractmethod
    def create(self, storage_id: StorageID) -> StorageEntity:
        """ストレージを作成"""
        raise NotImplementedError()

    @abstractmethod
    def get(self, storage_id: StorageID) -> StorageEntity:
        """ストレージを取得"""
        raise NotImplementedError()

    @abstractmethod
    def put(self, storage_entity: StorageEntity) -> None:
        """ストレージを保存"""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, storage_id: StorageID) -> None:
        """ストレージを削除"""
        raise NotImplementedError()


class IStudentStageResultRepository(ABC):
    """生徒ステージ結果repository"""

    @abstractmethod
    def get_status(
            self,
            student_id: StudentID,
    ) -> StudentStageStatusEntity:
        raise NotImplementedError()

    @abstractmethod
    def get_build_result(self, student_id: StudentID) -> Optional[BuildStageResultEntity]:
        raise NotImplementedError()

    @abstractmethod
    def get_compile_result(self, student_id: StudentID) -> Optional[CompileStageResultEntity]:
        raise NotImplementedError()

    @abstractmethod
    def get_execute_result(self, student_id: StudentID, testcase_id: TestCaseID) -> Optional[ExecuteStageResultEntity]:
        raise NotImplementedError()

    @abstractmethod
    def get_test_result(self, student_id: StudentID, testcase_id: TestCaseID) -> Optional[TestStageResultEntity]:
        raise NotImplementedError()

    @abstractmethod
    def update(
            self,
            result: AbstractStageResultEntity,
    ) -> None:
        """共通ヘッダーと、型に応じた詳細テーブルの両方を更新(Upsert)する。"""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, student_id: StudentID, stage: StageElement) -> None:
        """指定されたステージの結果を削除する"""
        raise NotImplementedError()


class IStudentExecutableRepository(ABC):
    """生徒実行ファイルリポジトリのインターフェース"""

    @abstractmethod
    def put(self, student_id: StudentID, file_item: ExecutableFileItem) -> None:
        """実行ファイルを保存"""
        raise NotImplementedError()

    @abstractmethod
    def get(self, student_id: StudentID) -> ExecutableFileItem:
        """実行ファイルを取得"""
        raise NotImplementedError()

    @abstractmethod
    def exists(self, student_id: StudentID) -> bool:
        """実行ファイルが存在するか"""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, student_id: StudentID) -> None:
        """実行ファイルを削除"""
        raise NotImplementedError()


class IStudentSourceRepository(ABC):
    """生徒ソースファイルリポジトリのインターフェース"""

    @abstractmethod
    def put(self, student_id: StudentID, file_item: SourceFileItem) -> None:
        """ソースファイルを保存"""
        raise NotImplementedError()

    @abstractmethod
    def get(self, student_id: StudentID) -> SourceFileItem:
        """ソースファイルを取得"""
        raise NotImplementedError()

    @abstractmethod
    def exists(self, student_id: StudentID) -> bool:
        """ソースファイルが存在するか"""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, student_id: StudentID) -> None:
        """ソースファイルを削除"""
        raise NotImplementedError()


class ITestSourceRepository(ABC):
    """テストソースリポジトリのインターフェース"""

    @abstractmethod
    def get(self) -> bytes:
        """テストソースを取得"""
        raise NotImplementedError()


class ITestRunRepository(ABC):
    """テスト実行リポジトリのインターフェース"""

    @abstractmethod
    def create(self, test_run_id: StorageID) -> None:
        """テスト実行セッションを作成"""
        raise NotImplementedError()

    @abstractmethod
    def set_file(self, test_run_id: StorageID, filename: str, content: bytes) -> Path:
        """テスト実行セッションにファイルを設定"""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, test_run_id: StorageID) -> None:
        """テスト実行セッションを削除"""
        raise NotImplementedError()
