from dataclasses import dataclass

from domain.models.values import TargetID, ProjectID


@dataclass(frozen=True)
class ProjectConfig:
    project_id: ProjectID
    target_id: TargetID

    def to_json(self):
        return dict(
            target_id=self.target_id.to_json(),
            project_id=self.project_id.to_json(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            target_id=TargetID.from_json(body["target_id"]),
            project_id=ProjectID.from_json(body["project_id"]),
        )
