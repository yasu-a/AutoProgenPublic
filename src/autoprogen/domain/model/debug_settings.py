from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DebugSettings:
    """デバッグ実行時に使用する開発者ごとの入力補助設定を保持する。"""

    # デバッグ時に使用するコンパイラー起動スクリプトの絶対パス。未指定なら通常設定を使用する。
    compiler_tool_fullpath: Path | None = None
    # 新規プロジェクト画面へ初期入力する提出アーカイブのパス。未指定なら初期入力しない。
    report_archive_fullpath: Path | None = None
    # 新規プロジェクト画面で重複しないプロジェクト名を自動生成するかどうか。
    auto_generate_project_name: bool = False
    # 新規プロジェクト画面へ初期入力する設問番号。未指定なら初期入力しない。
    target_number: int | None = None

    def __post_init__(self) -> None:
        """設定値の型と範囲がデバッグ入力として妥当か検証する。"""
        if self.compiler_tool_fullpath is not None and not isinstance(
                self.compiler_tool_fullpath,
                Path,
        ):
            raise TypeError("compiler_tool_fullpathにはPathまたはNoneを指定してください")
        if self.report_archive_fullpath is not None and not isinstance(
                self.report_archive_fullpath,
                Path,
        ):
            raise TypeError("report_archive_fullpathにはPathまたはNoneを指定してください")
        if not isinstance(self.auto_generate_project_name, bool):
            raise TypeError("auto_generate_project_nameにはboolを指定してください")
        if self.target_number is not None:
            if isinstance(self.target_number, bool) or not isinstance(self.target_number, int):
                raise TypeError("target_numberにはintまたはNoneを指定してください")
            if not 0 <= self.target_number <= 99:
                raise ValueError("target_numberは0以上99以下で指定してください")

    @classmethod
    def create_default(cls) -> "DebugSettings":
        """入力補助を行わない既定のデバッグ設定を生成する。"""
        return cls()
