"""Windows AppContainer の最小試作を検証するテスト。"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from autoprogen.infra.io.app_container import AppContainerRunner


@pytest.mark.parametrize("name", ["../escape.txt", "sub/file.txt", r"sub\file.txt", "C:foo.txt", "_stdout.bin", ".", "bad."])
def test_rejects_invalid_file_names(name: str) -> None:
    """作業領域外への参照や予約名を使わせない。"""
    with pytest.raises(ValueError):
        AppContainerRunner._validate_file_name(name)


@pytest.mark.skipif(
    os.name != "nt" or os.environ.get("AUTOPROGEN_TEST_APPCONTAINER") != "1",
    reason="Windows で AUTOPROGEN_TEST_APPCONTAINER=1 を明示した場合のみ実行",
)
def test_appcontainer_reads_and_writes_workspace() -> None:
    """隔離実行でも標準出力と作業フォルダ内のファイル操作は可能。"""
    cmd = Path(os.environ["SystemRoot"]) / "System32" / "cmd.exe"
    result = AppContainerRunner().run(
        cmd, ["/d", "/c", "echo STDOUT_OK & type input.txt & echo WORK_OK>result.txt"],
        input_files={"input.txt": b"INPUT_OK\r\n"},
        result_files=["result.txt"],
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert b"STDOUT_OK" in result.stdout
    assert b"INPUT_OK" in result.stdout
    assert result.result_files["result.txt"].strip() == b"WORK_OK"


@pytest.mark.skipif(
    os.name != "nt" or os.environ.get("AUTOPROGEN_TEST_APPCONTAINER") != "1",
    reason="Windows で AUTOPROGEN_TEST_APPCONTAINER=1 を明示した場合のみ実行",
)
def test_appcontainer_cannot_access_outside_canary() -> None:
    """外部に置いた検証用ファイルは読み書きできない。"""
    cmd = Path(os.environ["SystemRoot"]) / "System32" / "cmd.exe"
    secret = b"AUTOPROGEN_OUTSIDE_SECRET_264103"
    with tempfile.TemporaryDirectory(prefix="ap-canary-") as tmp:
        canary = Path(tmp) / "secret.txt"
        canary.write_bytes(secret)
        read_args = ["/d", "/c", "type", str(canary)]
        # 通常のプロセスなら正常に読めることを先に確認する。
        control = subprocess.run([str(cmd), *read_args], capture_output=True)
        assert secret in control.stdout
        restricted = AppContainerRunner().run(cmd, read_args)
        assert secret not in restricted.stdout
        write_args = ["/d", "/c", "echo", "ALTERED", ">", str(canary)]
        control_write = subprocess.run([str(cmd), *write_args], capture_output=True)
        assert control_write.returncode == 0, control_write.stderr
        assert canary.read_bytes().strip() == b"ALTERED"
        canary.write_bytes(secret)
        AppContainerRunner().run(cmd, write_args)
        assert canary.read_bytes() == secret
