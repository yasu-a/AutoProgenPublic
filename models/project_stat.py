from dataclasses import dataclass
from datetime import datetime

from models.values import ProjectName, TargetID


@dataclass
class ProjectStat:
    project_name: ProjectName
    target_id: TargetID
    mtime: datetime

    def __lt__(self, other):
        if not isinstance(other, ProjectStat):
            return NotImplemented
        return self.mtime < other.mtime
