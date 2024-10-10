from dataclasses import dataclass
from datetime import datetime

from domain.models.values import TargetID, ProjectID


@dataclass(slots=True)
class Project:
    project_id: ProjectID
    target_id: TargetID
    created_at: datetime
    open_at: datetime

    def to_json(self):
        return dict(
            project_id=self.project_id.to_json(),
            target_id=self.target_id.to_json(),
            created_at=self.created_at.isoformat(),
            open_at=self.open_at.isoformat(),
        )

    @classmethod
    def from_json(cls, body):
        return Project(
            project_id=ProjectID.from_json(body["project_id"]),
            target_id=TargetID.from_json(body["target_id"]),
            created_at=datetime.fromisoformat(body["created_at"]),
            open_at=datetime.fromisoformat(body["open_at"]),
        )
