from dataclasses import dataclass, replace
from datetime import datetime

from domain.model.app_version import AppVersion
from domain.model.value import TargetID, ProjectID


@dataclass(slots=True)
class Project:
    app_version: AppVersion
    project_id: ProjectID
    target_id: TargetID
    created_at: datetime
    zip_name: str
    open_at: datetime
    is_initialized: bool

    def set_initialized(self) -> "Project":
        return replace(self, is_initialized=True)

    def is_openable(self) -> bool:
        # このモデルが読み込めたときにプロジェクトが開けるかどうかを返す
        # バージョンの確認はモデルを読み込むときにするのでここではしない
        return self.is_initialized

    def to_json(self):
        return dict(
            app_version=self.app_version.to_json(),
            project_id=self.project_id.to_json(),
            target_id=self.target_id.to_json(),
            created_at=self.created_at.isoformat(),
            zip_name=self.zip_name,
            open_at=self.open_at.isoformat(),
            is_initialized=self.is_initialized,
        )

    @classmethod
    def from_json(cls, body):
        return Project(
            app_version=AppVersion.from_json(body["app_version"]),
            project_id=ProjectID.from_json(body["project_id"]),
            target_id=TargetID.from_json(body["target_id"]),
            created_at=datetime.fromisoformat(body["created_at"]),
            zip_name=body["zip_name"],
            open_at=datetime.fromisoformat(body["open_at"]),
            is_initialized=body["is_initialized"],
        )
