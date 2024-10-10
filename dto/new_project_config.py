from dataclasses import dataclass
from pathlib import Path


@dataclass
class NewProjectConfig:
    project_name: str
    target_number: int
    manaba_report_archive_fullpath: Path
