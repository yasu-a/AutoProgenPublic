from dataclasses import dataclass
from pathlib import Path


@dataclass
class GlobalSettings:
    """利用者が変更・保存できるアプリケーション全体の設定を保持する。"""

    # コンパイル前に実行するコンパイラー環境設定スクリプトのパス。未指定ならコンパイラー未設定として扱う。
    compiler_tool_fullpath: Path | None
    # コンパイル処理が完了するまで待機する最大秒数。
    compile_timeout: float
    # 並行実行できるワーカーの最大数。
    max_workers: int
    # 採点結果を出力する前に既存ファイルをバックアップするかどうか。
    backup_before_export: bool
    # 標準入出力の表示で編集記号を表示するかどうか。
    show_editing_symbols_in_stream_content: bool
    # ソースコードの表示で編集記号を表示するかどうか。
    show_editing_symbols_in_source_code: bool
    # 標準入出力の表示で行を折り返すかどうか。
    enable_line_wrap_in_stream_content: bool
    # ソースコードの表示で行を折り返すかどうか。
    enable_line_wrap_in_source_code: bool

    def __post_init__(self) -> None:
        """設定値の型と並列タスク実行数の範囲を検証する。"""
        if self.compiler_tool_fullpath is not None and not isinstance(
                self.compiler_tool_fullpath,
                Path,
        ):
            raise TypeError("compiler_tool_fullpathにはPathまたはNoneを指定してください")

        if isinstance(self.compile_timeout, bool) or not isinstance(
                self.compile_timeout,
                (int, float),
        ):
            raise TypeError("compile_timeoutにはfloatを指定してください")
        self.compile_timeout = float(self.compile_timeout)

        if isinstance(self.max_workers, bool) or not isinstance(self.max_workers, int):
            raise TypeError("max_workersにはintを指定してください")
        if self.max_workers < 1:
            raise ValueError("max_workersは1以上で指定してください")

        bool_field_names = (
            "backup_before_export",
            "show_editing_symbols_in_stream_content",
            "show_editing_symbols_in_source_code",
            "enable_line_wrap_in_stream_content",
            "enable_line_wrap_in_source_code",
        )
        for field_name in bool_field_names:
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name}にはboolを指定してください")

    @classmethod
    def create_default(
            cls,
            *,
            compiler_tool_fullpath: Path | None = None,
    ) -> "GlobalSettings":
        """任意のコンパイラーパスを反映した既定設定を生成する。"""
        return cls(
            compiler_tool_fullpath=compiler_tool_fullpath,
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
