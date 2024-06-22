from dataclasses import dataclass

from models.values import TargetID


@dataclass
class ProjectConfig:
    target_id: TargetID

    def to_json(self):
        return dict(
            target_id=self.target_id.to_json(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            target_id=TargetID.from_json(body["target_id"]),
        )
