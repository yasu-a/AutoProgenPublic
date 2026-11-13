import hashlib
import re
from dataclasses import dataclass

from autoprogen.domain.model.source_code_check import (
    SourceCodeCheckCatalog,
    SourceCodeCheckEntry,
    SourceCodeCheckFinding,
    SourceCodeCheckGroup,
    SourceCodeCheckMatchType,
    SourceCodeCheckResult,
)
from autoprogen.util.app_logging import create_logger


class SourceCodeCheckCatalogFactory:
    """AutoProgenが提供する固定のソースコードチェック規則を構成する。"""

    @staticmethod
    def _entry(
            check_id: str,
            name: str,
            target_strings: tuple[str, ...],
            description: str,
            match_type: SourceCodeCheckMatchType = SourceCodeCheckMatchType.FUNCTION_CALL,
    ) -> SourceCodeCheckEntry:
        """固定カタログへ登録するチェック規則を生成する。"""
        return SourceCodeCheckEntry(
            check_id=check_id,
            name=name,
            target_strings=target_strings,
            description=description,
            match_type=match_type,
        )

    def create(self) -> SourceCodeCheckCatalog:
        """カテゴリ別に整理された標準チェックカタログを返す。"""
        item = self._entry
        return SourceCodeCheckCatalog(groups=(
            SourceCodeCheckGroup(
                group_id="process",
                name="外部コマンド・プロセス生成",
                entries=(
                    item(
                        "system",
                        "外部コマンドの実行",
                        ("system", "_wsystem"),
                        "コマンドインタプリタを通じた外部コマンドの実行を検出します。",
                    ),
                    item(
                        "popen",
                        "パイプを使用したプロセス生成",
                        ("popen", "_popen", "_wpopen"),
                        "外部プロセスを起動してパイプを開く操作を検出します。",
                    ),
                    item(
                        "spawn",
                        "spawn系プロセス生成",
                        ("_spawnl", "_spawnle", "_spawnlp", "_spawnlpe", "_spawnv", "_spawnve", "_spawnvp", "_spawnvpe"),
                        "Cランタイムのspawn系関数を検出します。",
                    ),
                    item(
                        "exec",
                        "exec系プロセス置換",
                        ("_execl", "_execle", "_execlp", "_execlpe", "_execv", "_execve", "_execvp", "_execvpe"),
                        "Cランタイムのexec系関数を検出します。",
                    ),
                    item(
                        "create_process",
                        "Windowsプロセス生成",
                        ("CreateProcessA", "CreateProcessW", "CreateProcessAsUserA", "CreateProcessAsUserW", "CreateProcessWithLogonW", "CreateProcessWithTokenW"),
                        "Windows APIによるプロセス生成を検出します。",
                    ),
                    item(
                        "shell_execute",
                        "Windowsシェル実行",
                        ("ShellExecuteA", "ShellExecuteW", "ShellExecuteExA", "ShellExecuteExW", "WinExec"),
                        "Windowsシェルを通じた実行を検出します。",
                    ),
                    item(
                        "native_create_process",
                        "低レベルプロセス生成",
                        ("NtCreateProcess", "NtCreateProcessEx", "NtCreateUserProcess", "RtlCreateUserProcess"),
                        "Native APIによる低レベルなプロセス生成を検出します。",
                    ),
                ),
            ),
            SourceCodeCheckGroup(
                group_id="file",
                name="ファイル操作",
                entries=(
                    item(
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
                    ),
                    item(
                        "read",
                        "ファイル読み込み",
                        (
                            "fread", "fscanf", "fwscanf", "fscanf_s", "fwscanf_s",
                            "vfscanf", "vfwscanf", "vfscanf_s", "vfwscanf_s",
                            "fgetc", "fgetwc", "fgets", "fgetws",
                            "getc", "getwc", "ungetc", "ungetwc", "_getw",
                            "_read", "ReadFile",
                        ),
                        "ファイルからの読み込みを検出します。",
                    ),
                    item(
                        "write",
                        "ファイル書き込み",
                        (
                            "fwrite", "fprintf", "fwprintf", "fprintf_s", "fwprintf_s",
                            "vfprintf", "vfwprintf", "vfprintf_s", "vfwprintf_s",
                            "fputc", "fputwc", "fputs", "fputws",
                            "putc", "putwc", "_putw", "_write",
                            "WriteFile", "WriteFileEx",
                        ),
                        "ファイルへの書き込みを検出します。",
                    ),
                    item(
                        "position",
                        "ファイル位置操作",
                        (
                            "fseek", "_fseeki64", "fsetpos", "rewind",
                            "ftell", "_ftelli64", "fgetpos",
                            "_lseek", "_lseeki64", "_tell", "_telli64",
                        ),
                        "ファイルの読み書き位置を取得または変更する操作を検出します。",
                    ),
                    item(
                        "stream_control",
                        "ストリーム制御",
                        (
                            "fflush", "_flushall", "setbuf", "setvbuf",
                            "clearerr", "clearerr_s", "feof", "ferror",
                            "_commit", "_eof", "_fileno",
                        ),
                        "ストリームのバッファ、状態、ディスク反映を制御する操作を検出します。",
                    ),
                    item(
                        "close",
                        "ファイルを閉じる操作",
                        ("fclose", "_fcloseall", "_close"),
                        "ストリームまたはファイル記述子を閉じる操作を検出します。",
                    ),
                    item(
                        "temporary",
                        "一時ファイル操作",
                        (
                            "tmpfile", "tmpfile_s", "tmpnam", "tmpnam_s",
                            "_wtmpnam", "_wtmpnam_s", "_tempnam", "_wtempnam",
                            "_rmtmp",
                        ),
                        "一時ファイルの作成、命名、削除を行う操作を検出します。",
                    ),
                    item(
                        "descriptor",
                        "ファイル記述子操作",
                        ("_dup", "_dup2", "_getmaxstdio", "_setmaxstdio"),
                        "ファイル記述子や同時に開けるストリーム数を操作する処理を検出します。",
                    ),
                    item(
                        "delete",
                        "ファイル削除",
                        ("remove", "_wremove", "DeleteFileA", "DeleteFileW"),
                        "ファイルを削除する操作を検出します。",
                    ),
                    item(
                        "move",
                        "ファイル移動・置換",
                        ("rename", "_wrename", "MoveFileA", "MoveFileW", "MoveFileExA", "MoveFileExW", "ReplaceFileA", "ReplaceFileW"),
                        "ファイルの移動、改名、置換を検出します。",
                    ),
                    item(
                        "remove_directory",
                        "ディレクトリ削除",
                        ("rmdir", "_rmdir", "_wrmdir", "RemoveDirectoryA", "RemoveDirectoryW"),
                        "ディレクトリの削除を検出します。",
                    ),
                    item(
                        "truncate",
                        "ファイル切り詰め",
                        ("_chsize", "_chsize_s", "SetEndOfFile"),
                        "ファイル長の変更を検出します。",
                    ),
                    item(
                        "link",
                        "リンク作成",
                        ("CreateHardLinkA", "CreateHardLinkW", "CreateSymbolicLinkA", "CreateSymbolicLinkW"),
                        "ファイルシステム上のリンク作成を検出します。",
                    ),
                    item(
                        "permission",
                        "アクセス権変更",
                        ("chmod", "_chmod", "_wchmod", "SetFileSecurityA", "SetFileSecurityW"),
                        "ファイルのアクセス権変更を検出します。",
                    ),
                ),
            ),
            SourceCodeCheckGroup(
                group_id="windows_configuration",
                name="Windows設定",
                entries=(
                    item(
                        "registry",
                        "レジストリ操作",
                        ("RegCreateKey", "RegOpenKey", "RegSetValue", "RegDeleteKey", "RegDeleteValue", "RegSaveKey", "RegRestoreKey"),
                        "Windowsレジストリの参照や変更を検出します。",
                    ),
                    item(
                        "service",
                        "サービス操作",
                        ("OpenSCManager", "CreateService", "ChangeServiceConfig", "ControlService", "DeleteService", "StartService"),
                        "Windowsサービスの操作を検出します。",
                    ),
                    item(
                        "shutdown",
                        "シャットダウン操作",
                        ("ExitWindowsEx", "InitiateSystemShutdown", "InitiateSystemShutdownEx", "AbortSystemShutdown"),
                        "Windowsのシャットダウンや再起動を検出します。",
                    ),
                    item(
                        "power",
                        "電源制御",
                        ("SetSuspendState", "SetSystemPowerState"),
                        "システムの電源状態変更を検出します。",
                    ),
                    item(
                        "firmware",
                        "ファームウェア変数変更",
                        ("SetFirmwareEnvironmentVariableA", "SetFirmwareEnvironmentVariableW", "SetFirmwareEnvironmentVariableExA", "SetFirmwareEnvironmentVariableExW"),
                        "ファームウェア環境変数の変更を検出します。",
                    ),
                ),
            ),
            SourceCodeCheckGroup(
                group_id="process_interference",
                name="他プロセスへの干渉",
                entries=(
                    item(
                        "process_memory",
                        "他プロセスのメモリ操作",
                        ("ReadProcessMemory", "WriteProcessMemory", "VirtualAllocEx", "VirtualProtectEx"),
                        "別プロセスのメモリ操作を検出します。",
                    ),
                    item(
                        "thread_injection",
                        "スレッド注入",
                        ("CreateRemoteThread", "CreateRemoteThreadEx", "QueueUserAPC", "NtCreateThreadEx"),
                        "別プロセスでのコード実行につながる操作を検出します。",
                    ),
                    item(
                        "terminate",
                        "他プロセスの強制終了",
                        ("TerminateProcess", "NtTerminateProcess"),
                        "別プロセスの強制終了を検出します。",
                    ),
                    item(
                        "token",
                        "プロセストークン操作",
                        ("OpenProcessToken", "AdjustTokenPrivileges", "DuplicateToken", "DuplicateTokenEx", "SetTokenInformation"),
                        "アクセストークンや権限の操作を検出します。",
                    ),
                    item(
                        "impersonation",
                        "ユーザー偽装",
                        ("ImpersonateLoggedOnUser", "ImpersonateNamedPipeClient", "ImpersonateSelf", "SetThreadToken"),
                        "別ユーザーを偽装する操作を検出します。",
                    ),
                    item(
                        "hook",
                        "Windowsフック",
                        ("SetWindowsHookExA", "SetWindowsHookExW", "UnhookWindowsHookEx"),
                        "Windowsフックの操作を検出します。",
                    ),
                    item(
                        "input_capture",
                        "キーボード・クリップボード取得",
                        ("GetAsyncKeyState", "GetKeyState", "OpenClipboard", "GetClipboardData"),
                        "ユーザー入力やクリップボードの取得を検出します。",
                    ),
                ),
            ),
            SourceCodeCheckGroup(
                group_id="network",
                name="ネットワーク",
                entries=(
                    item(
                        "winsock",
                        "Winsock通信",
                        ("WSAStartup", "socket", "connect", "bind", "listen", "accept", "send", "sendto", "recv", "recvfrom"),
                        "Winsockを使用した通信を検出します。",
                    ),
                    item(
                        "winhttp",
                        "WinHTTP通信",
                        ("WinHttpOpen", "WinHttpConnect", "WinHttpOpenRequest", "WinHttpSendRequest", "WinHttpReceiveResponse"),
                        "WinHTTPを使用した通信を検出します。",
                    ),
                    item(
                        "wininet",
                        "WinINet通信",
                        ("InternetOpen", "InternetConnect", "HttpOpenRequest", "HttpSendRequest", "InternetOpenUrl"),
                        "WinINetを使用した通信を検出します。",
                    ),
                    item(
                        "download",
                        "URLからのダウンロード",
                        ("URLDownloadToFileA", "URLDownloadToFileW", "URLDownloadToCacheFileA", "URLDownloadToCacheFileW"),
                        "URLからファイルを取得する操作を検出します。",
                    ),
                    item(
                        "dns",
                        "DNS問い合わせ",
                        ("DnsQuery_A", "DnsQuery_W", "DnsQuery_UTF8", "getaddrinfo", "GetAddrInfoW"),
                        "DNSや名前解決の問い合わせを検出します。",
                    ),
                    item(
                        "configuration",
                        "ネットワーク設定変更",
                        ("SetIpForwardEntry", "SetIpInterfaceEntry", "AddIPAddress", "DeleteIPAddress"),
                        "Windowsのネットワーク設定変更を検出します。",
                    ),
                ),
            ),
            SourceCodeCheckGroup(
                group_id="system",
                name="システム操作",
                entries=(
                    item(
                        "device",
                        "デバイス制御",
                        ("DeviceIoControl",),
                        "デバイスへの制御要求を検出します。",
                    ),
                    item(
                        "volume",
                        "ボリューム操作",
                        ("SetVolumeMountPoint", "DeleteVolumeMountPoint", "DefineDosDevice", "SetVolumeLabel"),
                        "ドライブやボリュームの構成変更を検出します。",
                    ),
                    item(
                        "block_input",
                        "入力ブロック",
                        ("BlockInput",),
                        "キーボードやマウス入力の遮断を検出します。",
                    ),
                    item(
                        "dynamic_library",
                        "DLLの動的読み込み",
                        ("LoadLibraryA", "LoadLibraryW", "LoadLibraryExA", "LoadLibraryExW", "GetProcAddress"),
                        "DLLや関数の動的読み込みを検出します。",
                    ),
                    item(
                        "window_message",
                        "Windowsメッセージ操作",
                        ("SendMessageA", "SendMessageW", "PostMessageA", "PostMessageW", "PostThreadMessageA", "PostThreadMessageW"),
                        "ウィンドウやスレッドへのメッセージ送信を検出します。",
                    ),
                    item(
                        "screen_capture",
                        "画面取得",
                        ("BitBlt", "StretchBlt", "PrintWindow", "GetDC"),
                        "画面やウィンドウの取得につながる操作を検出します。",
                    ),
                    item(
                        "shared_memory",
                        "共有メモリ",
                        ("CreateFileMappingA", "CreateFileMappingW", "OpenFileMappingA", "OpenFileMappingW", "MapViewOfFile"),
                        "プロセス間で共有可能なメモリ操作を検出します。",
                    ),
                ),
            ),
            SourceCodeCheckGroup(
                group_id="dangerous_string",
                name="危険な文字列",
                entries=(
                    item(
                        "command_interpreter",
                        "コマンドインタプリタ",
                        ("cmd.exe", "powershell.exe", "pwsh.exe", "command.com"),
                        "コマンドインタプリタを指す文字列を検出します。",
                        SourceCodeCheckMatchType.STRING_LITERAL,
                    ),
                    item(
                        "script",
                        "スクリプト実行",
                        ("wscript.exe", "cscript.exe", "mshta.exe", ".bat", ".cmd", ".ps1", ".vbs", ".js"),
                        "スクリプト実行に使われる文字列を検出します。",
                        SourceCodeCheckMatchType.STRING_LITERAL,
                    ),
                    item(
                        "destructive_command",
                        "破壊的なシステムコマンド",
                        ("format ", "diskpart", "del ", "erase ", "rmdir ", "rd ", "taskkill", "net user", "shutdown ", "reg add", "reg delete"),
                        "システムへ影響するコマンド文字列を検出します。",
                        SourceCodeCheckMatchType.STRING_LITERAL,
                    ),
                    item(
                        "sensitive_path",
                        "機密・外部パス",
                        ("C:\\Windows", "C:\\Program Files", "C:\\Users", "..\\", "../", "\\\\.\\", "\\\\?\\"),
                        "プロジェクト外部やデバイスを指すパスを検出します。",
                        SourceCodeCheckMatchType.STRING_LITERAL,
                    ),
                    item(
                        "autorun",
                        "自動起動設定",
                        ("\\CurrentVersion\\Run", "\\CurrentVersion\\RunOnce", "Startup"),
                        "Windowsの自動起動設定を指す文字列を検出します。",
                        SourceCodeCheckMatchType.STRING_LITERAL,
                    ),
                ),
            ),
            SourceCodeCheckGroup(
                group_id="preprocessor",
                name="プリプロセッサ",
                entries=(
                    item(
                        "external_include",
                        "外部パスのinclude",
                        ("#include", "../", "..\\", ":\\"),
                        "親ディレクトリや絶対パスを指すincludeを検出します。",
                        SourceCodeCheckMatchType.PREPROCESSOR_EXTERNAL_INCLUDE,
                    ),
                    item(
                        "macro_include",
                        "マクロによるinclude",
                        ("#include",),
                        "マクロを介して指定されたincludeを検出します。",
                        SourceCodeCheckMatchType.PREPROCESSOR_MACRO_INCLUDE,
                    ),
                    item(
                        "pragma_comment",
                        "pragmaによる設定変更",
                        ("#pragma comment", "__pragma", "_Pragma"),
                        "リンク設定などを変更できるpragmaを検出します。",
                        SourceCodeCheckMatchType.PREPROCESSOR_PRAGMA,
                    ),
                ),
            ),
            SourceCodeCheckGroup(
                group_id="common_c",
                name="通常のC操作",
                entries=(
                    item(
                        "malloc",
                        "malloc",
                        ("malloc",),
                        "mallocによる動的メモリ確保を検出します。",
                    ),
                    item(
                        "calloc",
                        "calloc",
                        ("calloc",),
                        "callocによる動的メモリ確保を検出します。",
                    ),
                    item(
                        "realloc",
                        "realloc",
                        ("realloc",),
                        "reallocによるメモリ領域変更を検出します。",
                    ),
                    item(
                        "free",
                        "free",
                        ("free",),
                        "freeによる動的メモリ解放を検出します。",
                    ),
                    item(
                        "thread",
                        "通常のスレッド生成",
                        ("CreateThread", "_beginthread", "_beginthreadex"),
                        "現在のプロセス内でのスレッド生成を検出します。",
                    ),
                    item(
                        "terminate",
                        "プログラム終了",
                        ("exit", "_exit", "_Exit", "abort", "ExitProcess"),
                        "プログラムを明示的に終了させる操作を検出します。",
                    ),
                    item(
                        "buffer",
                        "バッファ操作",
                        ("strcpy", "strcat", "sprintf", "gets", "memcpy", "memmove", "memset"),
                        "文字列やメモリのバッファ操作を検出します。",
                    ),
                    item(
                        "environment",
                        "環境情報取得",
                        ("getenv", "_wgetenv", "GetEnvironmentVariableA", "GetEnvironmentVariableW", "GetCurrentDirectoryA", "GetCurrentDirectoryW", "getcwd", "_getcwd"),
                        "環境変数やカレントディレクトリの取得を検出します。",
                    ),
                    item(
                        "suspicious_loop",
                        "疑わしい無限ループ",
                        ("while(1)", "while (1)", "for(;;)", "for (;;)"),
                        "終了条件を持たない可能性があるループ構文を検出します。",
                        SourceCodeCheckMatchType.SOURCE_PATTERN,
                    ),
                ),
            ),
        ))


@dataclass(frozen=True)
class _StringLiteral:
    """字句解析中に抽出した一つの文字列リテラルを保持する。"""

    # 引用符を除いた、エスケープ表現を維持した文字列内容。
    content: str
    # 文字列内容のソースコード全体における開始位置。
    content_start: int


@dataclass(frozen=True)
class _LexicalView:
    """検出対象ごとに不要な字句を隠したソースコード表現を保持する。"""

    # コメント、文字列、文字リテラルを空白化し、位置を維持したソースコード。
    code_only: str
    # コメントだけを空白化し、プリプロセッサ解析に使用するソースコード。
    without_comments: str
    # ソースコードから抽出した文字列リテラル。
    string_literals: tuple[_StringLiteral, ...]


class SourceCodeCheckDecodeError(UnicodeError):
    """コンパイル対象をUTF-8ソースコードとして解釈できない場合のエラー。"""


class SourceCodeCheckService:
    """コンパイル対象ソースへ静的安全性チェックを適用する。"""

    _logger = create_logger()
    _IDENTIFIER_CHARACTER_PATTERN = r"A-Za-z0-9_"

    def __init__(
            self,
            *,
            catalog_factory: SourceCodeCheckCatalogFactory,
    ) -> None:
        """チェック規則カタログを構成するファクトリを受け取る。"""
        self._catalog_factory = catalog_factory

    @staticmethod
    def _mask_character(characters: list[str], index: int) -> None:
        """行位置を維持したまま、指定位置の字句を空白化する。"""
        if characters[index] not in "\r\n":
            characters[index] = " "

    @classmethod
    def _create_lexical_view(cls, source_code_text: str) -> _LexicalView:
        """コメントやリテラルを区別した検査用ソースコードを生成する。"""
        code_only = list(source_code_text)
        without_comments = list(source_code_text)
        string_literals: list[_StringLiteral] = []
        index = 0

        while index < len(source_code_text):
            current = source_code_text[index]
            following = source_code_text[index + 1] if index + 1 < len(source_code_text) else ""

            # 行コメントは改行を残して両方の検査用表現から除外する。
            if current == "/" and following == "/":
                while index < len(source_code_text) and source_code_text[index] not in "\r\n":
                    cls._mask_character(code_only, index)
                    cls._mask_character(without_comments, index)
                    index += 1
                continue

            # ブロックコメントは内部の改行位置を維持して除外する。
            if current == "/" and following == "*":
                cls._mask_character(code_only, index)
                cls._mask_character(without_comments, index)
                index += 1
                cls._mask_character(code_only, index)
                cls._mask_character(without_comments, index)
                index += 1
                while index < len(source_code_text):
                    if (
                            source_code_text[index] == "*"
                            and index + 1 < len(source_code_text)
                            and source_code_text[index + 1] == "/"
                    ):
                        cls._mask_character(code_only, index)
                        cls._mask_character(without_comments, index)
                        index += 1
                        cls._mask_character(code_only, index)
                        cls._mask_character(without_comments, index)
                        index += 1
                        break
                    cls._mask_character(code_only, index)
                    cls._mask_character(without_comments, index)
                    index += 1
                continue

            # 文字列リテラルは内容を記録し、関数呼び出し用の表現だけから除外する。
            if current == '"':
                cls._mask_character(code_only, index)
                index += 1
                content_start = index
                while index < len(source_code_text):
                    if source_code_text[index] == "\\":
                        cls._mask_character(code_only, index)
                        index += 1
                        if index < len(source_code_text):
                            cls._mask_character(code_only, index)
                            index += 1
                        continue
                    if source_code_text[index] == '"':
                        content = source_code_text[content_start:index]
                        string_literals.append(_StringLiteral(content, content_start))
                        cls._mask_character(code_only, index)
                        index += 1
                        break
                    cls._mask_character(code_only, index)
                    index += 1
                continue

            # 文字リテラルは関数名検出の対象外とし、内容は危険文字列として扱わない。
            if current == "'":
                cls._mask_character(code_only, index)
                index += 1
                while index < len(source_code_text):
                    if source_code_text[index] == "\\":
                        cls._mask_character(code_only, index)
                        index += 1
                        if index < len(source_code_text):
                            cls._mask_character(code_only, index)
                            index += 1
                        continue
                    is_end = source_code_text[index] == "'"
                    cls._mask_character(code_only, index)
                    index += 1
                    if is_end:
                        break
                continue

            index += 1

        return _LexicalView(
            code_only="".join(code_only),
            without_comments="".join(without_comments),
            string_literals=tuple(string_literals),
        )

    @staticmethod
    def _line_number(source_code_text: str, position: int) -> int:
        """文字位置を1から始まる行番号へ変換する。"""
        return source_code_text.count("\n", 0, position) + 1

    @staticmethod
    def _create_finding(
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            line_number: int,
    ) -> SourceCodeCheckFinding:
        """チェック規則と一致箇所から構造化された検出結果を生成する。"""
        return SourceCodeCheckFinding(
            line_number=line_number,
            group_id=group_id,
            check_id=entry.check_id,
        )

    @classmethod
    def _find_function_calls(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            source_code_text: str,
            code_only: str,
    ) -> list[SourceCodeCheckFinding]:
        """コメントやリテラル以外にある対象関数の呼び出しを検出する。"""
        findings: list[SourceCodeCheckFinding] = []
        for target in entry.target_strings:
            optional_windows_suffix = "(?:A|W)?" if target[0].isupper() else ""
            pattern = re.compile(
                rf"(?<![{cls._IDENTIFIER_CHARACTER_PATTERN}])"
                rf"(?P<name>{re.escape(target)}{optional_windows_suffix})"
                rf"(?=\s*\()"
            )
            for match in pattern.finditer(code_only):
                findings.append(cls._create_finding(
                    group_id=group_id,
                    entry=entry,
                    line_number=cls._line_number(source_code_text, match.start("name")),
                ))
        return findings

    @classmethod
    def _find_dangerous_strings(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            source_code_text: str,
            string_literals: tuple[_StringLiteral, ...],
    ) -> list[SourceCodeCheckFinding]:
        """文字列リテラル内にある危険なコマンドやパスを検出する。"""
        findings: list[SourceCodeCheckFinding] = []
        for literal in string_literals:
            lowered_content = literal.content.casefold()
            for target in entry.target_strings:
                # C文字列内のバックスラッシュはエスケープされる場合も同一対象として扱う。
                candidates = {target, target.replace("\\", "\\\\")}
                for candidate in candidates:
                    start = 0
                    while True:
                        position = lowered_content.find(candidate.casefold(), start)
                        if position < 0:
                            break
                        absolute_position = literal.content_start + position
                        findings.append(cls._create_finding(
                            group_id=group_id,
                            entry=entry,
                            line_number=cls._line_number(source_code_text, absolute_position),
                        ))
                        start = position + max(len(candidate), 1)
        return findings

    @staticmethod
    def _iter_logical_lines(source_code_text: str) -> list[tuple[int, str]]:
        """行継続を結合したプリプロセッサ用の論理行を列挙する。"""
        logical_lines: list[tuple[int, str]] = []
        buffer = ""
        start_line = 1
        for line_number, physical_line in enumerate(source_code_text.splitlines(), start=1):
            stripped_line = physical_line.rstrip()
            if not buffer:
                start_line = line_number
            if stripped_line.endswith("\\"):
                buffer += stripped_line[:-1] + " "
                continue
            logical_lines.append((start_line, buffer + physical_line))
            buffer = ""
        if buffer:
            logical_lines.append((start_line, buffer))
        return logical_lines

    @classmethod
    def _find_preprocessor(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            lexical_view: _LexicalView,
    ) -> list[SourceCodeCheckFinding]:
        """includeとpragmaに固有のプリプロセッサ規則を検査する。"""
        findings: list[SourceCodeCheckFinding] = []
        logical_lines = cls._iter_logical_lines(lexical_view.without_comments)
        for line_number, logical_line in logical_lines:
            include_match = re.match(r"^\s*#\s*include\s+(.+?)\s*$", logical_line)
            if entry.match_type == SourceCodeCheckMatchType.PREPROCESSOR_EXTERNAL_INCLUDE:
                if include_match is None:
                    continue
                argument = include_match.group(1)
                if not (
                        (argument.startswith('"') and argument.endswith('"'))
                        or (argument.startswith("<") and argument.endswith(">"))
                ):
                    continue
                path_text = argument[1:-1]
                is_external = bool(re.search(
                    r"(?:^|[\\/])\.\.(?:[\\/]|$)|^[A-Za-z]:[\\/]|^[\\/]",
                    path_text,
                ))
                if is_external:
                    findings.append(cls._create_finding(
                        group_id=group_id,
                        entry=entry,
                        line_number=line_number,
                    ))
            elif entry.match_type == SourceCodeCheckMatchType.PREPROCESSOR_MACRO_INCLUDE:
                if include_match is None:
                    continue
                argument = include_match.group(1)
                if not argument.startswith(('"', "<")):
                    findings.append(cls._create_finding(
                        group_id=group_id,
                        entry=entry,
                        line_number=line_number,
                    ))
            elif entry.match_type == SourceCodeCheckMatchType.PREPROCESSOR_PRAGMA:
                pragma_match = re.search(r"#\s*pragma\s+comment\b", logical_line)
                if pragma_match is not None:
                    findings.append(cls._create_finding(
                        group_id=group_id,
                        entry=entry,
                        line_number=line_number,
                    ))

        if entry.match_type == SourceCodeCheckMatchType.PREPROCESSOR_PRAGMA:
            pragma_pattern = re.compile(r"\b(?:__pragma\s*\(\s*comment|_Pragma\s*\()")
            for match in pragma_pattern.finditer(lexical_view.code_only):
                findings.append(cls._create_finding(
                    group_id=group_id,
                    entry=entry,
                    line_number=cls._line_number(lexical_view.code_only, match.start()),
                ))
        return findings

    @classmethod
    def _find_source_patterns(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            source_code_text: str,
            code_only: str,
    ) -> list[SourceCodeCheckFinding]:
        """空白表記の差を許容して疑わしい構文を検出する。"""
        findings: list[SourceCodeCheckFinding] = []
        pattern = re.compile(
            r"\bwhile\s*\(\s*(?:1|true)\s*\)"
            r"|\bfor\s*\(\s*;\s*;\s*\)"
        )
        for match in pattern.finditer(code_only):
            findings.append(cls._create_finding(
                group_id=group_id,
                entry=entry,
                line_number=cls._line_number(source_code_text, match.start()),
            ))
        return findings

    @classmethod
    def _find_entry(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            source_code_text: str,
            lexical_view: _LexicalView,
    ) -> list[SourceCodeCheckFinding]:
        """規則に指定された検出方式で一致箇所を探す。"""
        if entry.match_type == SourceCodeCheckMatchType.FUNCTION_CALL:
            return cls._find_function_calls(
                group_id=group_id,
                entry=entry,
                source_code_text=source_code_text,
                code_only=lexical_view.code_only,
            )
        if entry.match_type == SourceCodeCheckMatchType.STRING_LITERAL:
            return cls._find_dangerous_strings(
                group_id=group_id,
                entry=entry,
                source_code_text=source_code_text,
                string_literals=lexical_view.string_literals,
            )
        if entry.match_type in {
            SourceCodeCheckMatchType.PREPROCESSOR_EXTERNAL_INCLUDE,
            SourceCodeCheckMatchType.PREPROCESSOR_MACRO_INCLUDE,
            SourceCodeCheckMatchType.PREPROCESSOR_PRAGMA,
        }:
            return cls._find_preprocessor(
                group_id=group_id,
                entry=entry,
                lexical_view=lexical_view,
            )
        if entry.match_type == SourceCodeCheckMatchType.SOURCE_PATTERN:
            return cls._find_source_patterns(
                group_id=group_id,
                entry=entry,
                source_code_text=source_code_text,
                code_only=lexical_view.code_only,
            )
        raise ValueError(f"Unsupported match type: {entry.match_type}")

    def execute(self, *, source_code_bytes: bytes) -> SourceCodeCheckResult:
        """UTF-8ソースコードを検査し、SHA-256と検出結果を返す。"""
        catalog = self._catalog_factory.create()
        source_sha256 = hashlib.sha256(source_code_bytes).hexdigest()
        try:
            source_code_text = source_code_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise SourceCodeCheckDecodeError(
                "source code must be valid UTF-8"
            ) from error

        self._logger.info(
            "SOURCE CODE SAFETY CHECK STARTED "
            f"(source_size={len(source_code_bytes)}, "
            f"group_count={len(catalog.groups)}, "
            f"check_count={catalog.entry_count})"
        )

        lexical_view = self._create_lexical_view(source_code_text)
        findings = [
            finding
            for group in catalog.groups
            for entry in group.entries
            for finding in self._find_entry(
                group_id=group.group_id,
                entry=entry,
                source_code_text=source_code_text,
                lexical_view=lexical_view,
            )
        ]

        # 同一グループの同一規則が同じ行で複数回検出された場合は一件にまとめる。
        unique_findings = {
            (
                finding.group_id,
                finding.check_id,
                finding.line_number,
            ): finding
            for finding in findings
        }
        ordered_findings = tuple(sorted(
            unique_findings.values(),
            key=lambda finding: (
                finding.line_number,
                finding.group_id,
                finding.check_id,
            ),
        ))
        self._logger.info(
            "SOURCE CODE SAFETY CHECK FINISHED "
            f"(finding_count={len(ordered_findings)}, sha256={source_sha256})"
        )
        return SourceCodeCheckResult(
            source_sha256=source_sha256,
            findings=ordered_findings,
        )
