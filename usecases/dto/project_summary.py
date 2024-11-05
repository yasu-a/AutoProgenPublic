from dataclasses import dataclass
from datetime import datetime

from domain.models.values import ProjectID


@dataclass
class ProjectSummary:
    project_id: ProjectID
    project_name: str
    target_number: int
    zip_name: str
    open_at: datetime

    def __lt__(self, other):
        if not isinstance(other, ProjectSummary):
            return NotImplemented
        return self.open_at < other.open_at
