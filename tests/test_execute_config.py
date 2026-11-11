import pytest

from autoprogen.domain.model.execute_config import TestCaseExecuteConfig
from autoprogen.domain.model.execute_config_options import ExecuteConfigOptions
from autoprogen.domain.model.input_file import InputFile, InputFileCollection
from autoprogen.domain.model.value import FileID


# 製品クラスをpytestのテストクラス候補として収集させない。
TestCaseExecuteConfig.__test__ = False


def test_execute_config_compares_by_content_and_is_unhashable() -> None:
    """実行設定はJSONへの変換・復元後も等価であり、ハッシュ化できないことを確認する。"""
    original = TestCaseExecuteConfig(
        input_file_collection=InputFileCollection([
            InputFile(file_id=FileID.STDIN, content="YES\n"),
        ]),
        options=ExecuteConfigOptions(timeout=10.0),
    )

    restored = TestCaseExecuteConfig.from_json(original.to_json())

    assert restored == original
    with pytest.raises(TypeError):
        hash(original)

    restored.input_file_collection.put(
        InputFile(file_id=FileID("input.txt"), content="changed"),
    )
    assert restored != original
