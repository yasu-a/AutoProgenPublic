from dataclasses import dataclass
from pathlib import Path

from application.state.debug import is_debug


@dataclass
class GlobalConfig:
    compiler_tool_fullpath: Path | None
    compile_timeout: float
    max_workers: int
    backup_before_export: bool

    @classmethod
    def create_default(cls) -> "GlobalConfig":
        return cls(
            compiler_tool_fullpath=Path(
                r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat",
            ) if is_debug() else None,
            compile_timeout=30,
            max_workers=4,
            backup_before_export=True,
        )

    def to_json(self):
        return dict(
            compiler_tool_fullpath=str(self.compiler_tool_fullpath),
            compiler_timeout=self.compile_timeout,
            max_workers=self.max_workers,
            backup_before_export=self.backup_before_export,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            compiler_tool_fullpath=Path(body["compiler_tool_fullpath"]),
            compile_timeout=body["compiler_timeout"],
            max_workers=body["max_workers"],
            backup_before_export=body["backup_before_export"],
        )
