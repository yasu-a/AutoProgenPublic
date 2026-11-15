from collections.abc import Iterator

from autoprogen.domain.model.source_code_check import (
    SourceCodeCheckCatalog,
    SourceCodeCheckEntry,
    SourceCodeCheckGroup,
    SourceCodeCheckMatchType,
)


class SourceCodeCheckCatalogFactory:
    """AutoProgenが提供する固定のソースコードチェック規則を構成する。"""

    @staticmethod
    def _entry(
            check_id: str,
            name: str,
            target_strings: tuple[str, ...],
            description: str,
            match_type: SourceCodeCheckMatchType = SourceCodeCheckMatchType.FUNCTION_CALL,
            example_source_code: str = "",
            example_highlighted_line_numbers: tuple[int, ...] = (),
    ) -> SourceCodeCheckEntry:
        """固定カタログへ登録するチェック規則を生成する。"""
        return SourceCodeCheckEntry(
            check_id=check_id,
            name=name,
            target_strings=target_strings,
            description=description,
            match_type=match_type,
            example_source_code=example_source_code,
            example_highlighted_line_numbers=example_highlighted_line_numbers,
        )

    def _iter_items(self) -> Iterator[SourceCodeCheckEntry | dict[str, str]]:
        """規則を列挙し、各グループの末尾でグループ情報を返す。"""
        entry = self._entry
        # 外部コマンド・プロセス生成
        yield entry(
            "system",
            "外部コマンドの実行",
            ("system", "_wsystem"),
            "コマンドインタプリタを通じた外部コマンドの実行を検出します。",
            example_source_code=r"""#include <stdlib.h>

int main(void) {
    int result = system("echo AutoProgen demo");
    return result == -1 ? 1 : 0;
}
""",
            example_highlighted_line_numbers=(4,),
        )
        yield entry(
            "popen",
            "パイプを使用したプロセス生成",
            ("popen", "_popen", "_wpopen"),
            "外部プロセスを起動してパイプを開く操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <stdio.h>

int main(void) {
    char text[64];
    FILE *pipe = _popen("echo AutoProgen demo", "r");
    if (pipe == NULL) return 1;
    if (fgets(text, sizeof(text), pipe) != NULL) puts(text);
    return _pclose(pipe) == -1 ? 1 : 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "spawn",
            "spawn系プロセス生成",
            ("_spawnl", "_spawnle", "_spawnlp", "_spawnlpe",
             "_spawnv", "_spawnve", "_spawnvp", "_spawnvpe"),
            "Cランタイムのspawn系関数を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <process.h>
#include <stdlib.h>

int main(void) {
    intptr_t status = _spawnl(_P_WAIT, "cmd.exe", "cmd.exe",
                              "/c", "echo AutoProgen demo", NULL);
    return status == -1 ? 1 : 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "exec",
            "exec系プロセス置換",
            ("_execl", "_execle", "_execlp", "_execlpe",
             "_execv", "_execve", "_execvp", "_execvpe"),
            "Cランタイムのexec系関数を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <process.h>
#include <stdlib.h>

int main(void) {
    _execl("cmd.exe", "cmd.exe", "/c", "echo AutoProgen demo", NULL);
    return 1;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "create_process",
            "Windowsプロセス生成",
            ("CreateProcessA", "CreateProcessW", "CreateProcessAsUserA",
             "CreateProcessAsUserW", "CreateProcessWithLogonW", "CreateProcessWithTokenW"),
            "Windows APIによるプロセス生成を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    wchar_t command[] = L"cmd.exe /c echo AutoProgen demo";
    startup.cb = sizeof(startup);
    if (!CreateProcessW(NULL, command, NULL, NULL, FALSE, 0,
                        NULL, NULL, &startup, &process)) return 1;
    WaitForSingleObject(process.hProcess, INFINITE);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(9,),
        )
        yield entry(
            "shell_execute",
            "Windowsシェル実行",
            ("ShellExecuteA", "ShellExecuteW",
             "ShellExecuteExA", "ShellExecuteExW", "WinExec"),
            "Windowsシェルを通じた実行を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#pragma comment(lib, "shell32.lib")

int main(void) {
    /* ファイルを実際に開かない表示専用の例。 */
    if (0) {
        ShellExecuteW(NULL, L"open", L"example.txt", NULL,
                      NULL, SW_SHOWNORMAL);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(9,),
        )
        yield entry(
            "native_create_process",
            "低レベルプロセス生成",
            ("NtCreateProcess", "NtCreateProcessEx",
             "NtCreateUserProcess", "RtlCreateUserProcess"),
            "Native APIによる低レベルなプロセス生成を検出します。",
            example_source_code=r"""/* Native API呼び出しを示す例。複雑な内部構造は表示対象外とする。 */
#if 0
#include <windows.h>
#include <winternl.h>

int main(void) {
    NtCreateUserProcess(&process, &thread, process_access, thread_access,
                        NULL, NULL, 0, 0, parameters, info, attributes);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield {"group_id": 'process', "name": '外部コマンド・プロセス生成'}

        # ファイル操作
        yield entry(
            "open",
            "ファイルを開く操作",
            (
                "fopen", "_wfopen", "fopen_s", "_wfopen_s",
                "freopen", "_wfreopen", "freopen_s", "_wfreopen_s",
                "_fsopen", "_wfsopen", "_fdopen", "_wfdopen",
                "_open", "_wopen", "_sopen", "_wsopen",
                "_sopen_s", "_wsopen_s", "_creat", "_wcreat",
                "CreateFileA", "CreateFileW",
            ),
            "ファイルを開く操作を検出します。",
            example_source_code=r"""#include <stdio.h>

int main(void) {
    FILE *file = fopen("autoprogen_demo.txt", "r");
    if (file == NULL) return 1;
    fclose(file);
    return 0;
}
""",
            example_highlighted_line_numbers=(4,),
        )
        yield entry(
            "read",
            "ファイル読み込み",
            ('_read', 'ReadFile'),
            "ファイルからの読み込みを検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    char buffer[32];
    DWORD count = 0;
    HANDLE file = CreateFileW(L"autoprogen_demo.txt", GENERIC_READ,
                              FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (file == INVALID_HANDLE_VALUE) return 1;
    BOOL ok = ReadFile(file, buffer, sizeof(buffer), &count, NULL);
    CloseHandle(file);
    return ok ? 0 : 1;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(10,),
        )
        yield entry(
            "write",
            "ファイル書き込み",
            ('_write', 'WriteFile', 'WriteFileEx'),
            "ファイルへの書き込みを検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    const char text[] = "AutoProgen demo\n";
    DWORD count = 0;
    HANDLE file = CreateFileW(L"autoprogen_demo.txt", GENERIC_WRITE,
                              0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return 1;
    BOOL ok = WriteFile(file, text, sizeof(text) - 1, &count, NULL);
    CloseHandle(file);
    return ok ? 0 : 1;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(10,),
        )
        yield entry(
            "temporary",
            "一時ファイル操作",
            (
                "tmpfile", "tmpfile_s", "tmpnam", "tmpnam_s",
                "_wtmpnam", "_wtmpnam_s", "_tempnam", "_wtempnam",
                "_rmtmp",
            ),
            "一時ファイルの作成、命名、削除を行う操作を検出します。",
            example_source_code=r"""#include <stdio.h>

int main(void) {
    FILE *temporary_file = tmpfile();
    if (temporary_file == NULL) return 1;
    fputs("temporary data", temporary_file);
    fclose(temporary_file);
    return 0;
}
""",
            example_highlighted_line_numbers=(4,),
        )
        yield entry(
            "delete",
            "ファイル削除",
            ("remove", "_wremove", "DeleteFileA", "DeleteFileW"),
            "ファイルを削除する操作を検出します。",
            example_source_code=r"""#include <stdio.h>

int main(void) {
    FILE *file = fopen("autoprogen_demo.tmp", "w");
    if (file == NULL) return 1;
    fclose(file);
    return remove("autoprogen_demo.tmp") == 0 ? 0 : 1;
}
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "move",
            "ファイル移動・置換",
            ("rename", "_wrename", "MoveFileA", "MoveFileW",
             "MoveFileExA", "MoveFileExW", "ReplaceFileA", "ReplaceFileW"),
            "ファイルの移動、改名、置換を検出します。",
            example_source_code=r"""#include <stdio.h>

int main(void) {
    FILE *file = fopen("autoprogen_before.tmp", "w");
    if (file == NULL) return 1;
    fclose(file);
    if (rename("autoprogen_before.tmp", "autoprogen_after.tmp") != 0) return 1;
    remove("autoprogen_after.tmp");
    return 0;
}
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "remove_directory",
            "ディレクトリ削除",
            ("rmdir", "_rmdir", "_wrmdir",
             "RemoveDirectoryA", "RemoveDirectoryW"),
            "ディレクトリの削除を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <direct.h>

int main(void) {
    if (_mkdir("autoprogen_demo_dir") != 0) return 1;
    return _rmdir("autoprogen_demo_dir") == 0 ? 0 : 1;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "truncate",
            "ファイル切り詰め",
            ("_chsize", "_chsize_s", "SetEndOfFile"),
            "ファイル長の変更を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>

int main(void) {
    int fd = _open("autoprogen_demo.tmp", _O_CREAT | _O_RDWR,
                   _S_IREAD | _S_IWRITE);
    if (fd < 0) return 1;
    int status = _chsize(fd, 0);
    _close(fd);
    return status == 0 ? 0 : 1;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(10,),
        )
        yield entry(
            "link",
            "リンク作成",
            ("CreateHardLinkA", "CreateHardLinkW",
             "CreateSymbolicLinkA", "CreateSymbolicLinkW"),
            "ファイルシステム上のリンク作成を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    /* リンク作成処理を実行しない表示用の例。 */
    if (0) {
        CreateHardLinkW(L"autoprogen_link.txt", L"autoprogen_demo.txt", NULL);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "permission",
            "アクセス権変更",
            ("chmod", "_chmod", "_wchmod",
             "SetFileSecurityA", "SetFileSecurityW"),
            "ファイルのアクセス権変更を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <io.h>
#include <sys/stat.h>

int main(void) {
    int result = _chmod("autoprogen_demo.tmp", _S_IREAD | _S_IWRITE);
    return result == 0 ? 0 : 1;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield {"group_id": 'file', "name": 'ファイル操作'}

        # Windows設定
        yield entry(
            "registry",
            "レジストリ操作",
            ("RegCreateKey", "RegOpenKey", "RegSetValue", "RegDeleteKey",
             "RegDeleteValue", "RegSaveKey", "RegRestoreKey"),
            "Windowsレジストリの参照や変更を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    HKEY key = NULL;
    LONG status = RegOpenKeyA(HKEY_CURRENT_USER, "Software", &key);
    if (status != ERROR_SUCCESS) return 1;
    RegCloseKey(key);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "service",
            "サービス操作",
            ("OpenSCManager", "CreateService", "ChangeServiceConfig",
             "ControlService", "DeleteService", "StartService"),
            "Windowsサービスの操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    SC_HANDLE manager = OpenSCManagerW(NULL, NULL, SC_MANAGER_CONNECT);
    if (manager == NULL) return 1;
    CloseServiceHandle(manager);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(5,),
        )
        yield entry(
            "shutdown",
            "シャットダウン操作",
            ("ExitWindowsEx", "InitiateSystemShutdown",
             "InitiateSystemShutdownEx", "AbortSystemShutdown"),
            "Windowsのシャットダウンや再起動を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    /* 実際にはログオフしない。検出対象の呼び出しのみ示す。 */
    if (0) {
        ExitWindowsEx(EWX_LOGOFF, 0);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "power",
            "電源制御",
            ("SetSuspendState", "SetSystemPowerState"),
            "システムの電源状態変更を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>
#include <powrprof.h>
#pragma comment(lib, "powrprof.lib")

int main(void) {
    /* 実際にはスリープさせない。 */
    if (0) {
        SetSuspendState(FALSE, FALSE, FALSE);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(9,),
        )
        yield entry(
            "firmware",
            "ファームウェア変数変更",
            ("SetFirmwareEnvironmentVariableA", "SetFirmwareEnvironmentVariableW",
             "SetFirmwareEnvironmentVariableExA", "SetFirmwareEnvironmentVariableExW"),
            "ファームウェア環境変数の変更を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    const BYTE example_data[] = {0};
    /* ファームウェア設定は実際に変更しない。 */
    if (0) {
        SetFirmwareEnvironmentVariableW(L"Example", L"{00000000-0000-0000-0000-000000000000}",
                                        (PVOID)example_data, sizeof(example_data));
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(8,),
        )
        yield {"group_id": 'windows_configuration', "name": 'Windows設定'}

        # 他プロセスへの干渉
        yield entry(
            "process_memory",
            "他プロセスのメモリ操作",
            ("ReadProcessMemory", "WriteProcessMemory",
             "VirtualAllocEx", "VirtualProtectEx"),
            "別プロセスのメモリ操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    int value = 42;
    int copied = 0;
    SIZE_T bytes_read = 0;
    /* 例では他プロセスではなく自プロセスのメモリを読む。 */
    BOOL ok = ReadProcessMemory(GetCurrentProcess(), &value,
                                &copied, sizeof(copied), &bytes_read);
    return ok && copied == 42 ? 0 : 1;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(9,),
        )
        yield entry(
            "thread_injection",
            "スレッド注入",
            ("CreateRemoteThread", "CreateRemoteThreadEx",
             "QueueUserAPC", "NtCreateThreadEx"),
            "別プロセスでのコード実行につながる操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

static DWORD WINAPI worker(LPVOID data) {
    (void)data;
    return 0;
}

int main(void) {
    /* 対象は自分自身。外部プロセスへのコード注入は行わない。 */
    HANDLE thread = CreateRemoteThread(GetCurrentProcess(), NULL, 0,
                                       worker, NULL, 0, NULL);
    if (thread == NULL) return 1;
    WaitForSingleObject(thread, INFINITE);
    CloseHandle(thread);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(11,),
        )
        yield entry(
            "terminate",
            "他プロセスの強制終了",
            ("TerminateProcess", "NtTerminateProcess"),
            "別プロセスの強制終了を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    /* 外部プロセスを終了しない。 */
    if (0) {
        TerminateProcess(GetCurrentProcess(), 0);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "token",
            "プロセストークン操作",
            ("OpenProcessToken", "AdjustTokenPrivileges",
             "DuplicateToken", "DuplicateTokenEx", "SetTokenInformation"),
            "アクセストークンや権限の操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    HANDLE token = NULL;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &token)) return 1;
    CloseHandle(token);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "impersonation",
            "ユーザー偽装",
            ("ImpersonateLoggedOnUser", "ImpersonateNamedPipeClient",
             "ImpersonateSelf", "SetThreadToken"),
            "別ユーザーを偽装する操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    /* 自プロセスの識別情報だけを用いる例。 */
    if (!ImpersonateSelf(SecurityIdentification)) return 1;
    RevertToSelf();
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "hook",
            "Windowsフック",
            ("SetWindowsHookExA", "SetWindowsHookExW",
             "UnhookWindowsHookEx"),
            "Windowsフックの操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    /* フックは実際には登録しない。 */
    if (0) {
        SetWindowsHookExW(WH_GETMESSAGE, NULL, NULL, GetCurrentThreadId());
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "input_capture",
            "キーボード・クリップボード取得",
            ("GetAsyncKeyState", "GetKeyState",
             "OpenClipboard", "GetClipboardData"),
            "ユーザー入力やクリップボードの取得を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    /* Shiftキーの現在の状態だけを見る例。 */
    SHORT state = GetAsyncKeyState(VK_SHIFT);
    (void)state;
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(6,),
        )
        yield {"group_id": 'process_interference', "name": '他プロセスへの干渉'}

        # ネットワーク
        yield entry(
            "winsock",
            "Winsock通信",
            ("WSAStartup", "socket", "connect", "bind", "listen",
             "accept", "send", "sendto", "recv", "recvfrom"),
            "Winsockを使用した通信を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

int main(void) {
    WSADATA data;
    if (WSAStartup(MAKEWORD(2, 2), &data) != 0) return 1;
    SOCKET connection = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (connection != INVALID_SOCKET) closesocket(connection);
    WSACleanup();
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(8,),
        )
        yield entry(
            "winhttp",
            "WinHTTP通信",
            ("WinHttpOpen", "WinHttpConnect", "WinHttpOpenRequest",
             "WinHttpSendRequest", "WinHttpReceiveResponse"),
            "WinHTTPを使用した通信を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>
#include <winhttp.h>
#pragma comment(lib, "winhttp.lib")

int main(void) {
    HINTERNET session = WinHttpOpen(L"AutoProgenDemo/1.0",
                                   WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                   NULL, NULL, 0);
    if (session == NULL) return 1;
    WinHttpCloseHandle(session);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "wininet",
            "WinINet通信",
            ("InternetOpen", "InternetConnect", "HttpOpenRequest",
             "HttpSendRequest", "InternetOpenUrl"),
            "WinINetを使用した通信を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>
#include <wininet.h>
#pragma comment(lib, "wininet.lib")

int main(void) {
    HINTERNET session = InternetOpenA("AutoProgenDemo",
                                      INTERNET_OPEN_TYPE_DIRECT,
                                      NULL, NULL, 0);
    if (session == NULL) return 1;
    InternetCloseHandle(session);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "download",
            "URLからのダウンロード",
            ("URLDownloadToFileA", "URLDownloadToFileW",
             "URLDownloadToCacheFileA", "URLDownloadToCacheFileW"),
            "URLからファイルを取得する操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>
#include <urlmon.h>
#pragma comment(lib, "urlmon.lib")

int main(void) {
    /* インターネットへのアクセスは実行しない。 */
    if (0) {
        URLDownloadToFileW(NULL, L"https://example.com/demo.txt",
                           L"autoprogen_demo.txt", 0, NULL);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(9,),
        )
        yield entry(
            "dns",
            "DNS問い合わせ",
            ("DnsQuery_A", "DnsQuery_W", "DnsQuery_UTF8",
             "getaddrinfo", "GetAddrInfoW"),
            "DNSや名前解決の問い合わせを検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

int main(void) {
    WSADATA data;
    struct addrinfo *result = NULL;
    if (WSAStartup(MAKEWORD(2, 2), &data) != 0) return 1;
    int status = getaddrinfo("example.com", "80", NULL, &result);
    if (result != NULL) freeaddrinfo(result);
    WSACleanup();
    return status == 0 ? 0 : 1;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(10,),
        )
        yield entry(
            "configuration",
            "ネットワーク設定変更",
            ("SetIpForwardEntry", "SetIpInterfaceEntry",
             "AddIPAddress", "DeleteIPAddress"),
            "Windowsのネットワーク設定変更を検出します。",
            example_source_code=r"""#if 0
#include <windows.h>
#include <iphlpapi.h>

int main(void) {
    ULONG context = 0, instance = 0;
    /* ネットワーク設定は実際に変更しない。 */
    AddIPAddress(0x0100007F, 0x00FFFFFF, 1, &context, &instance);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(8,),
        )
        yield {"group_id": 'network', "name": 'ネットワーク'}

        # システム操作
        yield entry(
            "device",
            "デバイス制御",
            ("DeviceIoControl",),
            "デバイスへの制御要求を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    DWORD bytes_returned = 0;
    /* デバイス制御要求は実際には行わない。 */
    if (0) {
        DeviceIoControl(GetStdHandle(STD_OUTPUT_HANDLE), 0,
                        NULL, 0, NULL, 0, &bytes_returned, NULL);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(8,),
        )
        yield entry(
            "volume",
            "ボリューム操作",
            ("SetVolumeMountPoint", "DeleteVolumeMountPoint",
             "DefineDosDevice", "SetVolumeLabel"),
            "ドライブやボリュームの構成変更を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    /* ドライブのボリューム名を変更しない。 */
    if (0) {
        SetVolumeLabelW(L"X:\\", L"AutoProgenDemo");
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "block_input",
            "入力ブロック",
            ("BlockInput",),
            "キーボードやマウス入力の遮断を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    /* 実行して入力操作を妨げることはしない。 */
    if (0) {
        BlockInput(TRUE);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "dynamic_library",
            "DLLの動的読み込み",
            ("LoadLibraryA", "LoadLibraryW", "LoadLibraryExA",
             "LoadLibraryExW", "GetProcAddress"),
            "DLLや関数の動的読み込みを検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    HMODULE module = LoadLibraryW(L"kernel32.dll");
    if (module == NULL) return 1;
    FreeLibrary(module);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(5,),
        )
        yield entry(
            "window_message",
            "Windowsメッセージ操作",
            ("SendMessageA", "SendMessageW", "PostMessageA",
             "PostMessageW", "PostThreadMessageA", "PostThreadMessageW"),
            "ウィンドウやスレッドへのメッセージ送信を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    HWND window = GetConsoleWindow();
    if (window != NULL) {
        SendMessageW(window, WM_GETTEXTLENGTH, 0, 0);
    }
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(7,),
        )
        yield entry(
            "screen_capture",
            "画面取得",
            ("BitBlt", "StretchBlt", "PrintWindow", "GetDC"),
            "画面やウィンドウの取得につながる操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    HDC screen = GetDC(NULL);
    if (screen == NULL) return 1;
    ReleaseDC(NULL, screen);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(5,),
        )
        yield entry(
            "shared_memory",
            "共有メモリ",
            ("CreateFileMappingA", "CreateFileMappingW",
             "OpenFileMappingA", "OpenFileMappingW", "MapViewOfFile"),
            "プロセス間で共有可能なメモリ操作を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

int main(void) {
    HANDLE mapping = CreateFileMappingW(INVALID_HANDLE_VALUE, NULL,
                                        PAGE_READWRITE, 0, 4096,
                                        L"Local\\AutoProgenDemo");
    if (mapping == NULL) return 1;
    CloseHandle(mapping);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(5,),
        )
        yield {"group_id": 'system', "name": 'システム操作'}

        # 危険な文字列
        yield entry(
            "command_interpreter",
            "コマンドインタプリタ",
            ("cmd.exe", "powershell.exe", "pwsh.exe", "command.com"),
            "コマンドインタプリタを指す文字列を検出します。",
            SourceCodeCheckMatchType.STRING_LITERAL,
            example_source_code=r"""#include <stdio.h>

int main(void) {
    /* 文字列を表示するだけで、コマンドは実行しない。 */
    const char *command = "cmd.exe /c echo demo";
    puts(command);
    return 0;
}
""",
            example_highlighted_line_numbers=(5,),
        )
        yield entry(
            "script",
            "スクリプト実行",
            ("wscript.exe", "cscript.exe", "mshta.exe",
             ".bat", ".cmd", ".ps1", ".vbs", ".js"),
            "スクリプト実行に使われる文字列を検出します。",
            SourceCodeCheckMatchType.STRING_LITERAL,
            example_source_code=r"""#include <stdio.h>

int main(void) {
    const char *script_name = "sample.ps1";
    printf("script: %s\n", script_name);
    return 0;
}
""",
            example_highlighted_line_numbers=(4,),
        )
        yield entry(
            "destructive_command",
            "破壊的なシステムコマンド",
            ("format ", "diskpart", "del ", "erase ", "rmdir ", "rd ",
             "taskkill", "net user", "shutdown ", "reg add", "reg delete"),
            "システムへ影響するコマンド文字列を検出します。",
            SourceCodeCheckMatchType.STRING_LITERAL,
            example_source_code=r"""#include <stdio.h>

int main(void) {
    /* 危険なコマンド文字列の例。コマンドは実行しない。 */
    const char *command = "shutdown /s";
    puts(command);
    return 0;
}
""",
            example_highlighted_line_numbers=(5,),
        )
        yield entry(
            "sensitive_path",
            "機密・外部パス",
            ("C:\\Windows", "C:\\Program Files", "C:\\Users",
             "..\\", "../", "\\\\.\\", "\\\\?\\"),
            "プロジェクト外部やデバイスを指すパスを検出します。",
            SourceCodeCheckMatchType.STRING_LITERAL,
            example_source_code=r"""#include <stdio.h>

int main(void) {
    const char *path = "C:\\Windows\\System32";
    puts(path);
    return 0;
}
""",
            example_highlighted_line_numbers=(4,),
        )
        yield entry(
            "autorun",
            "自動起動設定",
            ("\\CurrentVersion\\Run",
             "\\CurrentVersion\\RunOnce", "Startup"),
            "Windowsの自動起動設定を指す文字列を検出します。",
            SourceCodeCheckMatchType.STRING_LITERAL,
            example_source_code=r"""#include <stdio.h>

int main(void) {
    /* 自動起動に使われるレジストリパスを表示するだけ。 */
    const char *key = "Software\\Microsoft\\Windows\\CurrentVersion\\Run";
    puts(key);
    return 0;
}
""",
            example_highlighted_line_numbers=(5,),
        )
        yield {"group_id": 'dangerous_string', "name": '危険な文字列'}

        # プリプロセッサ
        yield entry(
            "external_include",
            "外部パスのinclude",
            ("#include", "../", "..\\", ":\\"),
            "親ディレクトリや絶対パスを指すincludeを検出します。",
            SourceCodeCheckMatchType.PREPROCESSOR_EXTERNAL_INCLUDE,
            example_source_code=r"""/* プロジェクト外のヘッダーを直接参照する例。 */
#if 0
#include "../shared.h"
#endif

int main(void) {
    return 0;
}
""",
            example_highlighted_line_numbers=(3,),
        )
        yield entry(
            "macro_include",
            "マクロによるinclude",
            ("#include",),
            "マクロを介して指定されたincludeを検出します。",
            SourceCodeCheckMatchType.PREPROCESSOR_MACRO_INCLUDE,
            example_source_code=r"""#define HEADER <stdio.h>
#include HEADER

int main(void) {
    puts("AutoProgen demo");
    return 0;
}
""",
            example_highlighted_line_numbers=(2,),
        )
        yield entry(
            "pragma_comment",
            "pragmaによる設定変更",
            ("#pragma comment", "__pragma", "_Pragma"),
            "リンク設定などを変更できるpragmaを検出します。",
            SourceCodeCheckMatchType.PREPROCESSOR_PRAGMA,
            example_source_code=r"""#include <stdio.h>
#pragma comment(lib, "user32.lib")

int main(void) {
    puts("AutoProgen demo");
    return 0;
}
""",
            example_highlighted_line_numbers=(2,),
        )
        yield {"group_id": 'preprocessor', "name": 'プリプロセッサ'}

        # 通常のC操作
        yield entry(
            "malloc",
            "malloc",
            ("malloc",),
            "mallocによる動的メモリ確保を検出します。",
            example_source_code=r"""#include <stdlib.h>

int main(void) {
    int *buffer = malloc(10 * sizeof(*buffer));
    if (buffer == NULL) return 1;
    free(buffer);
    return 0;
}
""",
            example_highlighted_line_numbers=(4,),
        )
        yield entry(
            "calloc",
            "calloc",
            ("calloc",),
            "callocによる動的メモリ確保を検出します。",
            example_source_code=r"""#include <stdlib.h>

int main(void) {
    int *buffer = calloc(10, sizeof(*buffer));
    if (buffer == NULL) return 1;
    free(buffer);
    return 0;
}
""",
            example_highlighted_line_numbers=(4,),
        )
        yield entry(
            "realloc",
            "realloc",
            ("realloc",),
            "reallocによるメモリ領域変更を検出します。",
            example_source_code=r"""#include <stdlib.h>

int main(void) {
    int *buffer = malloc(sizeof(*buffer));
    if (buffer == NULL) return 1;
    int *larger = realloc(buffer, 20 * sizeof(*larger));
    if (larger == NULL) { free(buffer); return 1; }
    free(larger);
    return 0;
}
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "free",
            "free",
            ("free",),
            "freeによる動的メモリ解放を検出します。",
            example_source_code=r"""#include <stdlib.h>

int main(void) {
    void *buffer = malloc(16);
    if (buffer == NULL) return 1;
    free(buffer);
    return 0;
}
""",
            example_highlighted_line_numbers=(6,),
        )
        yield entry(
            "thread",
            "通常のスレッド生成",
            ("CreateThread", "_beginthread", "_beginthreadex"),
            "現在のプロセス内でのスレッド生成を検出します。",
            example_source_code=r"""#ifdef _WIN32
#include <windows.h>

static DWORD WINAPI worker(LPVOID data) {
    (void)data;
    return 0;
}

int main(void) {
    HANDLE thread = CreateThread(NULL, 0, worker, NULL, 0, NULL);
    if (thread == NULL) return 1;
    WaitForSingleObject(thread, INFINITE);
    CloseHandle(thread);
    return 0;
}
#else
int main(void) { return 0; }
#endif
""",
            example_highlighted_line_numbers=(10,),
        )
        yield entry(
            "terminate",
            "プログラム終了",
            ("exit", "_exit", "_Exit", "abort", "ExitProcess"),
            "プログラムを明示的に終了させる操作を検出します。",
            example_source_code=r"""#include <stdlib.h>

int main(void) {
    exit(EXIT_SUCCESS);
    return 0;
}
""",
            example_highlighted_line_numbers=(4,),
        )
        yield entry(
            "environment",
            "環境情報取得",
            ("getenv", "_wgetenv", "GetEnvironmentVariableA", "GetEnvironmentVariableW",
             "GetCurrentDirectoryA", "GetCurrentDirectoryW", "getcwd", "_getcwd"),
            "環境変数やカレントディレクトリの取得を検出します。",
            example_source_code=r"""#include <stdlib.h>
#include <stdio.h>

int main(void) {
    const char *path = getenv("PATH");
    if (path != NULL) puts(path);
    return 0;
}
""",
            example_highlighted_line_numbers=(5,),
        )
        yield {"group_id": 'common_c', "name": '通常のC操作'}

    def create(self) -> SourceCodeCheckCatalog:
        """カテゴリ別に整理された標準チェックカタログを返す。"""
        groups: list[SourceCodeCheckGroup] = []
        entries: list[SourceCodeCheckEntry] = []

        for item in self._iter_items():
            if isinstance(item, SourceCodeCheckEntry):
                entries.append(item)
                continue

            # グループ終端のdictを受け取った時点で、直前の規則群を確定する。
            groups.append(SourceCodeCheckGroup(
                group_id=item["group_id"],
                name=item["name"],
                entries=tuple(entries),
            ))
            entries.clear()

        # グループ情報をyieldし忘れた場合に、規則が黙って失われるのを防ぐ。
        if entries:
            raise ValueError("最後のグループ情報がありません")

        return SourceCodeCheckCatalog(groups=tuple(groups))
