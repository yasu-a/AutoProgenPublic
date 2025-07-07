from dataclasses import dataclass
from pathlib import Path

from application.state.debug import is_debug


@dataclass
class GlobalSettings:
    compiler_tool_fullpath: Path | None
    compile_timeout: float
    max_workers: int
    backup_before_export: bool
    show_editing_symbols_in_stream_content: bool
    show_editing_symbols_in_source_code: bool
    enable_line_wrap_in_stream_content: bool
    enable_line_wrap_in_source_code: bool

    @classmethod
    def create_default(cls) -> "GlobalSettings":
        return cls(
            compiler_tool_fullpath=Path(
                r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat",
            ) if is_debug() else None,
            compile_timeout=60,
            max_workers=4,
            backup_before_export=True,
            show_editing_symbols_in_stream_content=False,
            show_editing_symbols_in_source_code=False,
            enable_line_wrap_in_stream_content=False,
            enable_line_wrap_in_source_code=False,
        )

    def to_json(self):
        return dict(
            compiler_tool_fullpath=str(self.compiler_tool_fullpath),
            compiler_timeout=self.compile_timeout,
            max_workers=self.max_workers,
            backup_before_export=self.backup_before_export,
            show_editing_symbols_in_stream_content=self.show_editing_symbols_in_stream_content,
            show_editing_symbols_in_source_code=self.show_editing_symbols_in_source_code,
            enable_line_wrap_in_stream_content=self.enable_line_wrap_in_stream_content,
            enable_line_wrap_in_source_code=self.enable_line_wrap_in_source_code,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            compiler_tool_fullpath=Path(body["compiler_tool_fullpath"]),
            compile_timeout=body["compiler_timeout"],
            max_workers=body["max_workers"],
            backup_before_export=body["backup_before_export"],
            show_editing_symbols_in_stream_content=body["show_editing_symbols_in_stream_content"],
            show_editing_symbols_in_source_code=body["show_editing_symbols_in_source_code"],
            enable_line_wrap_in_stream_content=body["enable_line_wrap_in_stream_content"],
            enable_line_wrap_in_source_code=body["enable_line_wrap_in_source_code"],
        )
