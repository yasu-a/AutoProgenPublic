from dataclasses import dataclass
from datetime import datetime

from domain.models.values import ProjectID


@dataclass
class RecentProjectSummary:
    project_id: ProjectID
    project_name: str
    target_number: int
    mtime: datetime

    def __lt__(self, other):
        if not isinstance(other, RecentProjectSummary):
            return NotImplemented
        return self.mtime < other.mtime
