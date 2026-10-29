from dataclasses import dataclass
from pathlib import Path


@dataclass
class GlobalSettings:
    """利用者が変更・保存できるアプリケーション全体の設定を保持する。"""

    # コンパイル前に実行するコンパイラー環境設定スクリプトのパス。未指定なら自動検出する。
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
