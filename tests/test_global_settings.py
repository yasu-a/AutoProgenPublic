import json
from pathlib import Path

import pytest

from autoprogen.domain.model.global_settings import GlobalSettings


@pytest.mark.parametrize(
    "compiler_tool_fullpath",
    [None, Path(r"C:\Program Files\Microsoft Visual Studio\VsDevCmd.bat")],
)
def test_compiler_tool_fullpath_survives_json_round_trip(
        compiler_tool_fullpath: Path | None,
) -> None:
    """未設定と設定済みのコンパイラーパスをJSON往復後も維持する。"""
    settings = GlobalSettings.create_default(
        compiler_tool_fullpath=compiler_tool_fullpath,
    )

    json_body = json.loads(json.dumps(settings.to_json()))
    restored = GlobalSettings.from_json(json_body)

    assert restored == settings
