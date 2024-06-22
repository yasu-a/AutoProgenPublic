from dataclasses import dataclass
from pathlib import Path


@dataclass
class GlobalSettings:
    compiler_tool_fullpath: Path | None
    compiler_timeout: float
    max_workers: int

    @classmethod
    def create_default(cls) -> "GlobalSettings":
        return cls(
            compiler_tool_fullpath=Path(  # TODO: remove this path
                r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat",
            ),
            compiler_timeout=10,
            max_workers=8,
        )

    def to_json(self):
        return dict(
            compiler_tool_fullpath=str(self.compiler_tool_fullpath),
            compiler_timeout=self.compiler_timeout,
            max_workers=self.max_workers,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            compiler_tool_fullpath=Path(body["compiler_tool_fullpath"]),
            compiler_timeout=body["compiler_timeout"],
            max_workers=body["max_workers"],
        )
