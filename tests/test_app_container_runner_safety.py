"""AppContainerRunner の隔離・C互換性に関する追加の回帰テスト。"""

import math
import os
import subprocess
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from autoprogen.infra.io.app_container import AppContainerRunner


# 実機テストは既存の試作と同じ環境変数で明示的に有効化する。
WINDOWS_INTEGRATION = pytest.mark.skipif(
    os.name != "nt" or os.environ.get("AUTOPROGEN_TEST_APPCONTAINER") != "1",
    reason="Windows で AUTOPROGEN_TEST_APPCONTAINER=1 を指定した場合のみ実行",
)


PROBE_SOURCE = r"""
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include <string.h>

int wmain(int argc, wchar_t **argv) {
    if (argc < 2) return 91;

    if (wcscmp(argv[1], L"identity") == 0) {
        HANDLE token = NULL;
        DWORD in_container = 0;
        DWORD size = 0;
        if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &token)) return 92;
        BOOL ok = GetTokenInformation(token, TokenIsAppContainer,
                                      &in_container, sizeof(in_container), &size);
        CloseHandle(token);
        if (!ok) return 93;
        printf("APP_CONTAINER=%lu\n", (unsigned long)in_container);
        return 0;
    }

    if (wcscmp(argv[1], L"stdio") == 0) {
        int a, b;
        FILE *file = NULL;
        int value;
        if (scanf_s("%d %d", &a, &b) != 2) return 94;
        if (fopen_s(&file, "savedata.txt", "r+") != 0 || file == NULL) return 95;
        if (fscanf_s(file, "%d", &value) != 1) { fclose(file); return 96; }
        rewind(file);
        if (fprintf(file, "%d\n", value + 1) < 0) { fclose(file); return 97; }
        fclose(file);
        printf("SUM=%d\n", a + b);
        fprintf(stderr, "STDERR_OK\n");
        return 0;
    }

    if (wcscmp(argv[1], L"exit") == 0) {
        puts("STDOUT_BEFORE_EXIT");
        fputs("STDERR_BEFORE_EXIT\n", stderr);
        return 23;
    }

    if (wcscmp(argv[1], L"read") == 0 || wcscmp(argv[1], L"write") == 0) {
        if (argc < 3) return 98;
        BOOL is_write = wcscmp(argv[1], L"write") == 0;
        HANDLE handle = CreateFileW(
            argv[2], is_write ? GENERIC_WRITE : GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL, NULL
        );
        if (handle != INVALID_HANDLE_VALUE) {
            if (is_write) {
                const char marker[] = "CHANGED";
                DWORD written = 0;
                if (!WriteFile(handle, marker, sizeof(marker) - 1, &written, NULL)) {
                    CloseHandle(handle);
                    return 99;
                }
            }
            CloseHandle(handle);
            puts("ALLOWED");
            return 42;
        }
        DWORD err = GetLastError();
        printf("WIN_ERROR=%lu\n", (unsigned long)err);
        return err == ERROR_ACCESS_DENIED ? 0 : 43;
    }

    if (wcscmp(argv[1], L"child") == 0) {
        wchar_t executable[MAX_PATH] = {0};
        DWORD length = GetEnvironmentVariableW(L"ComSpec", executable, MAX_PATH);
        if (length == 0 || length >= MAX_PATH) return 47;
        wchar_t command[] = L"cmd.exe /d /c exit 0";
        STARTUPINFOW si = {0};
        PROCESS_INFORMATION pi = {0};
        si.cb = sizeof(si);
        BOOL created = CreateProcessW(
            executable, command, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi
        );
        if (created) {
            WaitForSingleObject(pi.hProcess, 5000);
            CloseHandle(pi.hThread);
            CloseHandle(pi.hProcess);
            puts("CHILD_CREATED");
            return 48;
        }
        printf("CHILD_FAILED=%lu\n", (unsigned long)GetLastError());
        return 0;
    }

    if (wcscmp(argv[1], L"loop") == 0) {
        for (;;) Sleep(100);
    }

    if (wcscmp(argv[1], L"large_stdout") == 0) {
        char chunk[4096];
        memset(chunk, 'A', sizeof(chunk));
        for (int i = 0; i < 257; i++) {
            if (fwrite(chunk, 1, sizeof(chunk), stdout) != sizeof(chunk)) return 44;
        }
        return 0;
    }

    if (wcscmp(argv[1], L"args") == 0) {
        if (argc < 3) return 45;
        if (wcscmp(argv[2], L"space and \"quote\"") != 0) return 46;
        puts("ARG_OK");
        return 0;
    }

    return 90;
}
"""


@pytest.fixture(scope="module")
def compiled_probe(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """既存の開発用設定に指定したMSVCで合成Cプログラムを1回だけ作る。"""
    if os.name != "nt":
        pytest.skip("MSVCコンパイルはWindows専用")
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / ".autoprogen-dev.toml"
    assert config_path.is_file(), (
        f"MSVC結合テストには {config_path} の compiler_tool_fullpath が必要です"
    )
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(config.get("compiler_tool_fullpath"), str)
    vsdev = Path(config["compiler_tool_fullpath"])
    assert vsdev.is_file(), f"VsDevCmd.bat が見つかりません: {vsdev}"

    work = tmp_path_factory.mktemp("appcontainer-c-probe")
    source = work / "probe.c"
    exe = work / "probe.exe"
    batch = work / "compile-probe.cmd"
    source.write_text(PROBE_SOURCE, encoding="utf-8")
    # MSVCの環境設定とコンパイルを同じcmdプロセス内で実行する。
    batch.write_text(
        "@echo off\n"
        + f'call "{vsdev}" -no_logo >nul\n'
        + "if errorlevel 1 exit /b 101\n"
        + f'cl /nologo /W4 /utf-8 /Fe:"{exe}" "{source}" /link advapi32.lib\n'
        + "exit /b %errorlevel%\n",
        encoding="cp932",
    )
    command = [os.environ["ComSpec"], "/d", "/c", str(batch)]
    completed = subprocess.run(
        command, cwd=work, capture_output=True, text=True,
        errors="replace", timeout=90,
    )
    assert completed.returncode == 0 and exe.is_file(), (
        f"Probe compile failed ({completed.returncode})\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    return exe


@pytest.mark.parametrize("timeout", [0, -1, 3600, math.nan, math.inf, -math.inf])
def test_invalid_timeout_is_rejected_before_launch(timeout: float) -> None:
    """危険な時間指定はファイル操作やWindows API呼び出しより前に拒否する。"""
    runner = AppContainerRunner.__new__(AppContainerRunner)
    with pytest.raises(ValueError, match="timeout"):
        runner.run(Path("not-an-executable.exe"), timeout=timeout)


@pytest.mark.parametrize(
    "filename",
    ["", ".", "..", "../outside.txt", "dir/file.txt", r"dir\file.txt",
     "C:relative.txt", "file:stream", "_stdin.bin", "bad.", "bad "],
)
def test_unsafe_file_names_are_rejected(filename: str) -> None:
    """相対パス脱出や代替データストリームを指定できない。"""
    with pytest.raises(ValueError):
        AppContainerRunner._validate_file_name(filename)


def test_rejects_case_colliding_inputs(tmp_path: Path) -> None:
    """大文字小文字だけが違う入力ファイル名の衝突を防止する。"""
    fake_exe = tmp_path / "probe.exe"
    fake_exe.write_bytes(b"fake")
    runner = AppContainerRunner.__new__(AppContainerRunner)
    with pytest.raises(ValueError, match="collide"):
        runner.run(fake_exe, input_files={"data.txt": b"a", "DATA.TXT": b"b"})


def test_rejects_reserved_output_name(tmp_path: Path) -> None:
    """内部管理ファイルへの上書きを禁止する。"""
    fake_exe = tmp_path / "probe.exe"
    fake_exe.write_bytes(b"fake")
    runner = AppContainerRunner.__new__(AppContainerRunner)
    with pytest.raises(ValueError, match="reserved"):
        runner.run(fake_exe, result_files=["_stderr.bin"])


def test_rejects_nonbytes_input_file(tmp_path: Path) -> None:
    """入力ファイルの値にテキストが混入するのを防ぐ。"""
    fake_exe = tmp_path / "probe.exe"
    fake_exe.write_bytes(b"fake")
    runner = AppContainerRunner.__new__(AppContainerRunner)
    with pytest.raises(TypeError, match="bytes"):
        runner.run(fake_exe, input_files={"data.txt": "text"})


def test_oversized_result_is_rejected(tmp_path: Path) -> None:
    """結果ファイルの上限を越えた際に全体を読み込まない。"""
    output = tmp_path / "result.txt"
    output.write_bytes(b"x" * (1024 * 1024 + 1))
    with pytest.raises(RuntimeError, match="size limit"):
        AppContainerRunner._read_bounded(output)


def test_workspace_and_profile_cleanup_on_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """実行失敗でも一時フォルダとプロファイルの後始末を行う。"""
    fake_exe = tmp_path / "probe.exe"
    fake_exe.write_bytes(b"fake")
    runner = AppContainerRunner.__new__(AppContainerRunner)
    events: list[str] = []
    workspaces: list[Path] = []

    def fake_profile() -> tuple[str, None, str]:
        """Windows APIを使わずに擬似プロファイルを返す。"""
        return "test-profile", None, "test-sid"

    def fake_grant(workspace: Path, sid: str) -> None:
        """ACLを変更せず作業領域だけ記録する。"""
        assert sid == "test-sid"
        workspaces.append(workspace)

    def fake_launch(*args, **kwargs) -> int:
        """プロセス起動失敗を再現する。"""
        events.append("launch")
        raise OSError("synthetic launch failure")

    monkeypatch.setattr(runner, "_new_profile", fake_profile)
    monkeypatch.setattr(runner, "_grant_workspace", fake_grant)
    monkeypatch.setattr(runner, "_launch", fake_launch)
    monkeypatch.setattr(runner, "_free_sid", lambda sid: events.append("free_sid"))
    monkeypatch.setattr(runner, "_delete_profile", lambda name: events.append("delete_profile") or 0)
    with pytest.raises(OSError, match="synthetic launch failure"):
        runner.run(fake_exe)

    assert events == ["launch", "free_sid", "delete_profile"]
    assert len(workspaces) == 1
    assert not workspaces[0].exists()


def test_failure_to_create_profile_does_not_launch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """隔離プロファイルが作れなければ通常実行へ切り替えない。"""
    fake_exe = tmp_path / "probe.exe"
    fake_exe.write_bytes(b"fake")
    runner = AppContainerRunner.__new__(AppContainerRunner)
    calls: list[str] = []

    def profile_error() -> None:
        """プロファイル作成失敗を再現する。"""
        calls.append("profile")
        raise OSError("synthetic profile failure")

    def should_not_launch(*args, **kwargs) -> int:
        """予期しない実行経路を検出する。"""
        calls.append("launch")
        return 0

    monkeypatch.setattr(runner, "_new_profile", profile_error)
    monkeypatch.setattr(runner, "_launch", should_not_launch)
    with pytest.raises(OSError, match="synthetic profile failure"):
        runner.run(fake_exe)
    assert calls == ["profile"]


def test_symlink_result_is_not_followed(tmp_path: Path) -> None:
    """結果ファイルがシンボリックリンクの場合はリンク先を読み込まない。"""
    outside = tmp_path / "outside.txt"
    link = tmp_path / "result.txt"
    outside.write_bytes(b"TEST_ONLY")
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("この環境ではシンボリックリンクを作成できない")
    with pytest.raises(RuntimeError, match="symlink"):
        AppContainerRunner._read_bounded(link)


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_real_c_binary_uses_appcontainer_token(compiled_probe: Path) -> None:
    """実際のC実行ファイルのトークンがAppContainerであることを直接確かめる。"""
    control = subprocess.run([str(compiled_probe), "identity"], capture_output=True, check=True)
    assert b"APP_CONTAINER=0" in control.stdout
    result = AppContainerRunner().run(compiled_probe, ["identity"])
    assert result.returncode == 0, result.stderr
    assert b"APP_CONTAINER=1" in result.stdout


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_real_c_stdio_and_input_file_update(compiled_probe: Path) -> None:
    """scanf・printf・stderrと入力ファイル上書きを同時に確認する。"""
    result = AppContainerRunner().run(
        compiled_probe, ["stdio"],
        input_data=b"11 31\n",
        input_files={"savedata.txt": b"7\n"},
        result_files=["savedata.txt"],
    )
    assert result.returncode == 0
    assert b"SUM=42" in result.stdout
    assert b"STDERR_OK" in result.stderr
    assert result.result_files["savedata.txt"] == b"8\r\n" or result.result_files["savedata.txt"] == b"8\n"


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_input_file_can_remain_unchanged(compiled_probe: Path) -> None:
    """入力ファイルを変更せずに終了した場合は元の内容を取得する。"""
    result = AppContainerRunner().run(
        compiled_probe, ["exit"],
        input_files={"savedata.txt": b"7\n"},
        result_files=["savedata.txt", "not-created.txt"],
    )
    assert result.returncode == 23
    assert result.result_files == {"savedata.txt": b"7\n"}


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_real_c_nonzero_exit_code_and_output(compiled_probe: Path) -> None:
    """異常終了しても終了コードと標準出力・標準エラーを取得できる。"""
    result = AppContainerRunner().run(compiled_probe, ["exit"])
    assert result.returncode == 23
    assert b"STDOUT_BEFORE_EXIT" in result.stdout
    assert b"STDERR_BEFORE_EXIT" in result.stderr


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
@pytest.mark.parametrize("mode", ["read", "write"])
def test_real_c_outside_canary_denied(compiled_probe: Path, tmp_path: Path, mode: str) -> None:
    """ホスト上のテスト専用ファイルへのアクセスがERROR_ACCESS_DENIEDになる。"""
    canary = tmp_path / "canary.txt"
    original = b"SYNTHETIC_SECRET_ONLY"
    canary.write_bytes(original)
    # 通常実行でアクセス可能なことを先に確認する。
    baseline = subprocess.run(
        [str(compiled_probe), mode, str(canary)], capture_output=True,
        timeout=5,
    )
    assert baseline.returncode == 42, baseline.stderr
    assert b"ALLOWED" in baseline.stdout
    # baselineの書込み分を戻してから、隔離された同じ実行ファイルを起動する。
    canary.write_bytes(original)
    result = AppContainerRunner().run(compiled_probe, [mode, str(canary)])
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert b"WIN_ERROR=5" in result.stdout
    assert canary.read_bytes() == original


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_real_c_infinite_loop_times_out(compiled_probe: Path) -> None:
    """無限ループするCプログラムをタイムアウトで停止できる。"""
    with pytest.raises(TimeoutError, match="timed out"):
        AppContainerRunner().run(compiled_probe, ["loop"], timeout=0.5)


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_real_c_output_over_limit_fails_closed(compiled_probe: Path) -> None:
    """実行後に1MiBを越える標準出力を正常結果として返さない。"""
    with pytest.raises(RuntimeError, match="size limit"):
        AppContainerRunner().run(compiled_probe, ["large_stdout"], timeout=10)


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_child_process_creation_is_blocked(compiled_probe: Path) -> None:
    """通常実行で可能な子プロセス生成を隔離実行では禁止する。"""
    baseline = subprocess.run(
        [str(compiled_probe), "child"], capture_output=True, timeout=10,
    )
    assert baseline.returncode == 48, (baseline.stdout, baseline.stderr)
    assert b"CHILD_CREATED" in baseline.stdout
    restricted = AppContainerRunner().run(compiled_probe, ["child"])
    assert restricted.returncode == 0, (restricted.stdout, restricted.stderr)
    assert b"CHILD_FAILED=" in restricted.stdout


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_real_c_argument_quoting(compiled_probe: Path) -> None:
    """空白・引用符を含むコマンドライン引数を壊さず渡す。"""
    result = AppContainerRunner().run(compiled_probe, ["args", 'space and "quote"'])
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert b"ARG_OK" in result.stdout


@WINDOWS_INTEGRATION
@pytest.mark.msvc_integration
def test_parallel_isolated_runs(compiled_probe: Path) -> None:
    """複数の隔離実行で結果が混在しない。"""
    def execute(i: int) -> tuple[int, bytes]:
        """独立したAppContainerで指定した足し算を実行する。"""
        result = AppContainerRunner().run(
            compiled_probe, ["stdio"],
            input_data=f"{i} {i + 1}\n".encode("ascii"),
            input_files={"savedata.txt": b"7\n"},
        )
        return result.returncode, result.stdout

    with ThreadPoolExecutor(max_workers=3) as pool:
        actual = list(pool.map(execute, range(3)))
    for i, (returncode, output) in enumerate(actual):
        assert returncode == 0
        assert f"SUM={2 * i + 1}".encode("ascii") in output
