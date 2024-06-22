from dataclasses import dataclass
from pathlib import Path

from models.values import ProjectName, TargetID


@dataclass
class NewProjectConfig:
    project_name: ProjectName
    manaba_report_archive_fullpath: Path
    target_id: TargetID
