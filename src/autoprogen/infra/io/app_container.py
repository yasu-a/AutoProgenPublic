"""AppContainer 実行の最小試作（Windows のみ・本番採用前の検証用）。"""

import ctypes
import math
import os
import shutil
import subprocess
import tempfile
import uuid
import warnings
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

if os.name == "nt":
    import msvcrt


class _StartupInfo(ctypes.Structure):
    """STARTUPINFOW の Windows API レイアウト。"""

    _fields_ = [
        ("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class _StartupInfoEx(ctypes.Structure):
    """STARTUPINFOEXW の Windows API レイアウト。"""

    _fields_ = [("StartupInfo", _StartupInfo), ("lpAttributeList", ctypes.c_void_p)]


class _ProcessInfo(ctypes.Structure):
    """PROCESS_INFORMATION の Windows API レイアウト。"""

    _fields_ = [
        ("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD),
    ]


class _SecurityCapabilities(ctypes.Structure):
    """SECURITY_CAPABILITIES の Windows API レイアウト。"""

    _fields_ = [
        ("AppContainerSid", ctypes.c_void_p),
        ("Capabilities", ctypes.c_void_p),
        ("CapabilityCount", wintypes.DWORD),
        ("Reserved", wintypes.DWORD),
    ]


@dataclass(frozen=True)
class AppContainerResult:
    """実行結果。result_files は明示要求した相対ファイル名だけを含む。"""

    returncode: int
    stdout: bytes
    stderr: bytes
    result_files: dict[str, bytes]


class AppContainerRunner:
    """一時フォルダに実行ファイルを複製し、AppContainer 内で実行する試作。"""

    _MAX_CAPTURE = 1024 * 1024

    def __init__(self) -> None:
        """Windows API を取得し、引数型と戻り値型を宣言する。"""
        if os.name != "nt":
            raise OSError("AppContainerRunner requires Windows")
        self._kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._userenv = ctypes.WinDLL("userenv", use_last_error=True)
        self._advapi = ctypes.WinDLL("advapi32", use_last_error=True)

        def bind(dll, name, restype, *argtypes):
            """WinAPI の型を指定して取得する。"""
            fn = getattr(dll, name)
            fn.restype = restype
            fn.argtypes = list(argtypes)
            return fn

        P = ctypes.c_void_p
        D = wintypes.DWORD
        B = wintypes.BOOL
        S = ctypes.c_size_t
        W = wintypes.LPCWSTR
        self._create_profile = bind(self._userenv, "CreateAppContainerProfile", ctypes.c_int32,
                                    W, W, W, P, D, ctypes.POINTER(P))
        self._delete_profile = bind(self._userenv, "DeleteAppContainerProfile", ctypes.c_int32, W)
        self._free_sid = bind(self._advapi, "FreeSid", P, P)
        self._sid_string = bind(self._advapi, "ConvertSidToStringSidW", B, P, ctypes.POINTER(P))
        self._local_free = bind(self._kernel, "LocalFree", P, P)
        self._init_attr = bind(self._kernel, "InitializeProcThreadAttributeList", B,
                               P, D, D, ctypes.POINTER(S))
        self._update_attr = bind(self._kernel, "UpdateProcThreadAttribute", B,
                                 P, D, S, P, S, P, P)
        self._delete_attr = bind(self._kernel, "DeleteProcThreadAttributeList", None, P)
        self._create_process = bind(self._kernel, "CreateProcessW", B,
                                    W, wintypes.LPWSTR, P, P, B, D, P, W, P,
                                    ctypes.POINTER(_ProcessInfo))
        self._wait = bind(self._kernel, "WaitForSingleObject", D, P, D)
        self._terminate = bind(self._kernel, "TerminateProcess", B, P, D)
        self._get_exit = bind(self._kernel, "GetExitCodeProcess", B, P, ctypes.POINTER(D))
        self._close = bind(self._kernel, "CloseHandle", B, P)

    @staticmethod
    def _validate_file_name(name: str) -> None:
        """一時領域の外側を指す名前を拒否する。"""
        if (not name or name in (".", "..") or "/" in name or "\\" in name
                or ":" in name or name.startswith("_") or name.endswith(".")
                or name.endswith(" ")):
            raise ValueError(f"unsafe file name: {name!r}")

    @classmethod
    def _read_bounded(cls, path: Path) -> bytes:
        """結果ファイルをサイズ上限付きで読み出す。"""
        if path.is_symlink():
            raise RuntimeError(f"symlink result is not supported: {path.name}")
        with path.open("rb") as stream:
            data = stream.read(cls._MAX_CAPTURE + 1)
        if len(data) > cls._MAX_CAPTURE:
            raise RuntimeError(f"output exceeds size limit: {path.name}")
        return data

    def _new_profile(self) -> tuple[str, ctypes.c_void_p, str]:
        """毎回別の AppContainer プロファイルを作成する。"""
        name = "AutoProgenTest." + uuid.uuid4().hex
        sid = ctypes.c_void_p()
        hr = self._create_profile(name, name, "Temporary AutoProgen test", None, 0, ctypes.byref(sid))
        if hr != 0:
            raise OSError(f"CreateAppContainerProfile HRESULT=0x{hr & 0xffffffff:08x}")
        sid_text_ptr = ctypes.c_void_p()
        try:
            if not self._sid_string(sid, ctypes.byref(sid_text_ptr)):
                raise ctypes.WinError(ctypes.get_last_error())
            sid_text = ctypes.wstring_at(sid_text_ptr)
            return name, sid, sid_text
        except BaseException:
            self._free_sid(sid)
            self._delete_profile(name)
            raise
        finally:
            if sid_text_ptr:
                self._local_free(sid_text_ptr)

    @staticmethod
    def _grant_workspace(workspace: Path, sid: str) -> None:
        """自動生成した一時フォルダのみに SID 権限と低整合性ラベルを付ける。"""
        icacls = Path(os.environ["SystemRoot"]) / "System32" / "icacls.exe"
        for args in (("/grant", f"*{sid}:(OI)(CI)M", "/T"),
                     ("/setintegritylevel", "(OI)(CI)L", "/T")):
            subprocess.run([str(icacls), str(workspace), *args],
                           check=True, capture_output=True, text=True, errors="replace")

    def _launch(self, exe: Path, args: Sequence[str], workspace: Path, sid: ctypes.c_void_p,
                stdin_path: Path, stdout_path: Path, stderr_path: Path,
                timeout: float) -> int:
        """制限付きプロセスを起動し、終了・タイムアウトを処理する。"""
        size = ctypes.c_size_t()
        self._init_attr(None, 3, 0, ctypes.byref(size))
        if ctypes.get_last_error() != 122 or not size.value:
            raise ctypes.WinError(ctypes.get_last_error())
        attrbuf = ctypes.create_string_buffer(size.value)
        attrlist = ctypes.cast(attrbuf, ctypes.c_void_p)
        if not self._init_attr(attrlist, 3, 0, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            caps = _SecurityCapabilities(sid, None, 0, 0)
            child_policy = wintypes.DWORD(1)  # PROCESS_CREATION_CHILD_PROCESS_RESTRICTED
            with stdin_path.open("rb") as fin, stdout_path.open("wb") as fout, stderr_path.open("wb") as ferr:
                raw_handles = [msvcrt.get_osfhandle(f.fileno()) for f in (fin, fout, ferr)]
                handles = (wintypes.HANDLE * 3)(*raw_handles)
                si = _StartupInfoEx()
                si.StartupInfo.cb = ctypes.sizeof(si)
                si.StartupInfo.dwFlags = 0x100  # STARTF_USESTDHANDLES
                si.StartupInfo.hStdInput = handles[0]
                si.StartupInfo.hStdOutput = handles[1]
                si.StartupInfo.hStdError = handles[2]

                for attribute, value, byte_count in (
                    (0x00020009, ctypes.byref(caps), ctypes.sizeof(caps)),
                    (0x00020002, ctypes.byref(handles), ctypes.sizeof(handles)),
                    (0x0002000E, ctypes.byref(child_policy), ctypes.sizeof(child_policy)),
                ):
                    if not self._update_attr(attrlist, 0, attribute, value, byte_count, None, None):
                        raise ctypes.WinError(ctypes.get_last_error())
                si.lpAttributeList = attrlist

                system_root = Path(os.environ["SystemRoot"])
                system32 = system_root / "System32"
                env = {
                    "SystemRoot": str(system_root), "WINDIR": str(system_root),
                    "ComSpec": str(system32 / "cmd.exe"), "PATH": str(system32),
                    # AppContainerプロファイルの場所をWindowsが解決するために必要。
                    "LOCALAPPDATA": os.environ["LOCALAPPDATA"],
                    "TEMP": str(workspace), "TMP": str(workspace),
                }
                env_block = ctypes.create_unicode_buffer(
                    "\0".join(f"{key}={value}" for key, value in sorted(env.items())) + "\0\0"
                )
                command = ctypes.create_unicode_buffer(subprocess.list2cmdline([str(exe), *args]))
                process = _ProcessInfo()
                for handle in raw_handles:
                    os.set_handle_inheritable(handle, True)
                try:
                    if not self._create_process(
                        str(exe), command, None, None, True,
                        # コンソールを分離するとAppContainer内のDLL初期化が失敗するため、親の状態を継承する。
                        0x00080000 | 0x00000400,  # EXTENDED_STARTUPINFO, UNICODE_ENV
                        ctypes.cast(env_block, ctypes.c_void_p), str(workspace),
                        ctypes.byref(si), ctypes.byref(process),
                    ):
                        raise ctypes.WinError(ctypes.get_last_error())
                finally:
                    for handle in raw_handles:
                        os.set_handle_inheritable(handle, False)

                try:
                    self._close(process.hThread)
                    wait_result = self._wait(process.hProcess, math.ceil(timeout * 1000))
                    if wait_result == 258:
                        if not self._terminate(process.hProcess, 0x102):
                            raise ctypes.WinError(ctypes.get_last_error())
                        self._wait(process.hProcess, 5000)
                        raise TimeoutError(f"AppContainer timed out after {timeout} seconds")
                    if wait_result != 0:
                        raise ctypes.WinError(ctypes.get_last_error())
                    exit_code = wintypes.DWORD()
                    if not self._get_exit(process.hProcess, ctypes.byref(exit_code)):
                        raise ctypes.WinError(ctypes.get_last_error())
                    return exit_code.value
                finally:
                    self._close(process.hProcess)
        finally:
            self._delete_attr(attrlist)

    def run(self, executable: Path, args: Sequence[str] = (), *,
            input_data: bytes = b"", input_files: Mapping[str, bytes] | None = None,
            result_files: Sequence[str] = (), timeout: float = 5.0) -> AppContainerResult:
        """独立した一時環境で実行し、標準入出力と指定結果ファイルを返す。"""
        if not (math.isfinite(timeout) and 0 < timeout < 3600):
            raise ValueError("timeout must be between 0 and 3600 seconds")
        exe = Path(executable).resolve(strict=True)
        if not exe.is_file():
            raise ValueError("executable must be a file")
        inputs = dict(input_files or {})
        for name in (*inputs.keys(), *result_files):
            self._validate_file_name(name)
        reserved = {exe.name.casefold(), "_stdin.bin", "_stdout.bin", "_stderr.bin"}
        if any(name.casefold() in reserved for name in (*inputs.keys(), *result_files)):
            raise ValueError("reserved internal file name")
        if len({name.casefold() for name in inputs}) != len(inputs):
            raise ValueError("input file names collide on Windows")
        for name in inputs:
            if not isinstance(inputs[name], bytes):
                raise TypeError("input_files values must be bytes")

        with tempfile.TemporaryDirectory(prefix="autoprogen-ac-poc-") as directory:
            workspace = Path(directory)
            staged_exe = workspace / exe.name
            shutil.copyfile(exe, staged_exe)
            for name, body in inputs.items():
                (workspace / name).write_bytes(body)
            stdin_path = workspace / "_stdin.bin"
            stdout_path = workspace / "_stdout.bin"
            stderr_path = workspace / "_stderr.bin"
            stdin_path.write_bytes(input_data)
            profile_name, sid, sid_text = self._new_profile()
            try:
                self._grant_workspace(workspace, sid_text)
                returncode = self._launch(staged_exe, args, workspace, sid,
                                          stdin_path, stdout_path, stderr_path, timeout)
                result = {}
                for name in result_files:
                    path = workspace / name
                    if path.is_file():
                        result[name] = self._read_bounded(path)
                return AppContainerResult(returncode, self._read_bounded(stdout_path),
                                          self._read_bounded(stderr_path), result)
            finally:
                self._free_sid(sid)
                hr = self._delete_profile(profile_name)
                if hr != 0:
                    warnings.warn(f"DeleteAppContainerProfile failed: 0x{hr & 0xffffffff:08x}",
                                  RuntimeWarning, stacklevel=2)
