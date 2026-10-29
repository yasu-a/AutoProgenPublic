import tomllib
from pathlib import Path
from typing import Any

from autoprogen.domain.model.debug_settings import DebugSettings


class DebugSettingsGatewayError(RuntimeError):
    """デバッグ設定TOMLの読み込みに失敗したことを表す。"""


class DebugSettingsTomlGateway:
    """注入された単一のTOMLファイルからデバッグ設定を読み込む。"""

    def __init__(self, *, toml_fullpath: Path) -> None:
        """読み込み対象として使用し続けるTOMLファイルのパスを受け取る。"""
        self._toml_fullpath = toml_fullpath

    def read(self) -> DebugSettings:
        """TOMLファイルを読み込み、デバッグ設定へ変換する。"""
        if not self._toml_fullpath.exists():
            return DebugSettings.create_default()

        try:
            with self._toml_fullpath.open("rb") as file:
                body = tomllib.load(file)
            return self._from_toml_body(body)
        except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError) as error:
            raise DebugSettingsGatewayError(
                f"デバッグ設定の読み込みに失敗しました: {self._toml_fullpath}\n{error!s}"
            ) from error

    def _from_toml_body(self, body: dict[str, Any]) -> DebugSettings:
        """TOMLから読み込んだ値の型を検証してドメインモデルへ変換する。"""
        compiler_tool_fullpath = self._read_optional_path(
            body,
            key="compiler_tool_fullpath",
        )
        report_archive_fullpath = self._read_optional_path(
            body,
            key="report_archive_fullpath",
        )
        auto_generate_project_name = body.get("auto_generate_project_name", False)
        if not isinstance(auto_generate_project_name, bool):
            raise TypeError("auto_generate_project_nameには真偽値を指定してください")

        target_number = body.get("target_number")
        if target_number is not None and (
                isinstance(target_number, bool) or not isinstance(target_number, int)
        ):
            raise TypeError("target_numberには整数を指定してください")

        return DebugSettings(
            compiler_tool_fullpath=compiler_tool_fullpath,
            report_archive_fullpath=report_archive_fullpath,
            auto_generate_project_name=auto_generate_project_name,
            target_number=target_number,
        )

    @staticmethod
    def _read_optional_path(body: dict[str, Any], *, key: str) -> Path | None:
        """任意のパス文字列を読み取り、未指定ならNoneを返す。"""
        value = body.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{key}には文字列を指定してください")
        if not value:
            raise ValueError(f"{key}には空文字列を指定できません")
        return Path(value).expanduser()
