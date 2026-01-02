from datetime import datetime

from shared.domain.value.app_version import AppVersion
from shared.domain.value.identifier import TargetID, ProjectID


class ProjectEntity:
    def __init__(
            self,
            *,
            project_id: ProjectID,
            app_version: AppVersion,
            target_id: TargetID,
            created_at: datetime,
            zip_name: str,
            open_at: datetime,
            is_initialized: bool,
    ):
        self._project_id = project_id  # IDフィールド: immutable
        self.app_version = app_version
        self.target_id = target_id
        self.created_at = created_at
        self.zip_name = zip_name
        self.open_at = open_at
        self.is_initialized = is_initialized

        self._validate()

    def _validate(self):
        if not isinstance(self._project_id, ProjectID):
            raise TypeError(
                f"Expected 'project_id' to be ProjectID, "
                f"got {type(self._project_id).__name__}: {self._project_id!r}"
            )
        if not isinstance(self.app_version, AppVersion):
            raise TypeError(
                f"Expected 'app_version' to be AppVersion, "
                f"got {type(self.app_version).__name__}: {self.app_version!r}"
            )
        if not isinstance(self.target_id, TargetID):
            raise TypeError(
                f"Expected 'target_id' to be TargetID, "
                f"got {type(self.target_id).__name__}: {self.target_id!r}"
            )
        if not isinstance(self.created_at, datetime):
            raise TypeError(
                f"Expected 'created_at' to be datetime, "
                f"got {type(self.created_at).__name__}: {self.created_at!r}"
            )
        if not isinstance(self.zip_name, str):
            raise TypeError(
                f"Expected 'zip_name' to be str, "
                f"got {type(self.zip_name).__name__}: {self.zip_name!r}"
            )
        if not isinstance(self.open_at, datetime):
            raise TypeError(
                f"Expected 'open_at' to be datetime, "
                f"got {type(self.open_at).__name__}: {self.open_at!r}"
            )
        if not isinstance(self.is_initialized, bool):
            raise TypeError(
                f"Expected 'is_initialized' to be bool, "
                f"got {type(self.is_initialized).__name__}: {self.is_initialized!r}"
            )

    @property
    def project_id(self) -> ProjectID:
        """IDフィールド: Getterのみ（変更不可）"""
        return self._project_id

    def set_initialized(self) -> "ProjectEntity":
        """is_initializedをTrueに設定した新しいインスタンスを返す"""
        return ProjectEntity(
            project_id=self._project_id,
            app_version=self.app_version,
            target_id=self.target_id,
            created_at=self.created_at,
            zip_name=self.zip_name,
            open_at=self.open_at,
            is_initialized=True,
        )

    def is_openable(self) -> bool:
        # このモデルが読み込めたときにプロジェクトが開けるかどうかを返す
        # バージョンの確認はモデルを読み込むときにするのでここではしない
        return self.is_initialized

    def __eq__(self, other):
        """IDベースの等価性判定"""
        if not isinstance(other, ProjectEntity):
            return False
        return self._project_id == other._project_id

    def __hash__(self):
        """IDベースのハッシュ"""
        return hash(self._project_id)

    def to_json(self):
        return dict(
            app_version=self.app_version.to_json(),
            project_id=self._project_id.to_json(),
            target_id=self.target_id.to_json(),
            created_at=self.created_at.isoformat(),
            zip_name=self.zip_name,
            open_at=self.open_at.isoformat(),
            is_initialized=self.is_initialized,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            project_id=ProjectID.from_json(body["project_id"]),
            app_version=AppVersion.from_json(body["app_version"]),
            target_id=TargetID.from_json(body["target_id"]),
            created_at=datetime.fromisoformat(body["created_at"]),
            zip_name=body["zip_name"],
            open_at=datetime.fromisoformat(body["open_at"]),
            is_initialized=body["is_initialized"],
        )
