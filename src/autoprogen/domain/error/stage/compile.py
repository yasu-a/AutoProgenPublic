from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from autoprogen.domain.error.stage.base import StageError
from autoprogen.domain.model.source_code_check import SourceCodeCheckFinding


class CompileStageError(StageError):
    """COMPILEステージで発生するエラーの基底クラス。"""

    error_group_id: ClassVar[str] = "compile"


class SourceSafetyViolationError(CompileStageError):
    """ソースコードの安全性チェックで問題が検出された。"""

    error_type_id: ClassVar[str] = "safety_violation"

    # 検査対象ソースコードのSHA-256ハッシュ値（小文字16進文字列）。
    source_sha256: str

    # 検出された問題の一覧。既存のSourceCodeCheckFindingを利用する。
    findings: tuple[SourceCodeCheckFinding, ...]

    def __init__(
            self,
            *,
            source_sha256: str,
            findings: Sequence[SourceCodeCheckFinding],
    ) -> None:
        """検査対象のハッシュ値と検出された問題を保持する。"""
        if type(source_sha256) is not str:
            raise TypeError("source_sha256はstrである必要があります")
        if any(
                not isinstance(finding, SourceCodeCheckFinding) for finding in findings
        ):
            raise TypeError("findingsの要素はSourceCodeCheckFindingである必要があります")
        super().__init__()
        self.source_sha256 = source_sha256
        self.findings = tuple(findings)

    def to_params_dict(self) -> dict[str, Any]:
        """ハッシュ値と検出結果をJSON互換の辞書へ変換する。"""
        return {
            "source_sha256": self.source_sha256,
            "findings": [
                {
                    "line_number": finding.line_number,
                    "group_id": finding.group_id,
                    "check_id": finding.check_id,
                }
                for finding in self.findings
            ],
        }

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "SourceSafetyViolationError":
        """保存用辞書からハッシュ値と検出結果を復元する。"""
        source_sha256 = params["source_sha256"]
        findings = params["findings"]
        if type(source_sha256) is not str:
            raise TypeError("source_sha256はstrである必要があります")
        if type(findings) is not list:
            raise TypeError("findingsはlistである必要があります")

        restored_findings: list[SourceCodeCheckFinding] = []
        for finding in findings:
            if type(finding) is not dict:
                raise TypeError("findingsの要素はdictである必要があります")
            line_number = finding["line_number"]
            group_id = finding["group_id"]
            check_id = finding["check_id"]
            if type(line_number) is not int:
                raise TypeError("line_numberはintである必要があります")
            if type(group_id) is not str:
                raise TypeError("group_idはstrである必要があります")
            if type(check_id) is not str:
                raise TypeError("check_idはstrである必要があります")
            restored_findings.append(SourceCodeCheckFinding(
                line_number=line_number,
                group_id=group_id,
                check_id=check_id,
            ))
        return cls(
            source_sha256=source_sha256,
            findings=tuple(restored_findings),
        )


class SourceSafetyDecodeError(CompileStageError):
    """安全性チェックのためにソースコードをUTF-8で復号できなかった。"""

    error_type_id: ClassVar[str] = "safety_decode_error"


class CompilerNotConfiguredError(CompileStageError):
    """使用するコンパイラが設定されていない。"""

    error_type_id: ClassVar[str] = "compiler_not_configured"


class CompileSourceNotFoundError(CompileStageError):
    """一時ストレージにコンパイル対象が存在しない。"""

    error_type_id: ClassVar[str] = "source_not_found"


class VsDevToolNotFoundError(CompileStageError):
    """Visual Studioの開発者ツールが存在しない。"""

    error_type_id: ClassVar[str] = "vs_dev_tool_not_found"

    # 見つからなかったVisual Studio開発者ツールのパス。
    path: Path

    def __init__(self, *, path: Path) -> None:
        """見つからなかった開発者ツールのパスを保持する。"""
        if not isinstance(path, Path):
            raise TypeError("pathはPathである必要があります")
        super().__init__()
        self.path = path

    def to_params_dict(self) -> dict[str, Any]:
        """パスをJSON互換の辞書へ変換する。"""
        return {"path": str(self.path)}

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "VsDevToolNotFoundError":
        """保存用辞書からパスを復元する。"""
        path = params["path"]
        if type(path) is not str:
            raise TypeError("pathはstrである必要があります")
        return cls(path=Path(path))


class CompilerWorkingDirectoryNotFoundError(CompileStageError):
    """コンパイラの作業ディレクトリが存在しない。"""

    error_type_id: ClassVar[str] = "working_directory_not_found"

    # 存在しないコンパイラ作業ディレクトリのパス。
    path: Path

    def __init__(self, *, path: Path) -> None:
        """存在しない作業ディレクトリのパスを保持する。"""
        if not isinstance(path, Path):
            raise TypeError("pathはPathである必要があります")
        super().__init__()
        self.path = path

    def to_params_dict(self) -> dict[str, Any]:
        """パスをJSON互換の辞書へ変換する。"""
        return {"path": str(self.path)}

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "CompilerWorkingDirectoryNotFoundError":
        """保存用辞書からパスを復元する。"""
        path = params["path"]
        if type(path) is not str:
            raise TypeError("pathはstrである必要があります")
        return cls(path=Path(path))


class CompilerInputFileNotFoundError(CompileStageError):
    """コンパイラへ渡すソースファイルが存在しない。"""

    error_type_id: ClassVar[str] = "input_file_not_found"

    # 見つからなかったコンパイラ入力ファイルのパス。
    path: Path

    def __init__(self, *, path: Path) -> None:
        """見つからなかった入力ファイルのパスを保持する。"""
        if not isinstance(path, Path):
            raise TypeError("pathはPathである必要があります")
        super().__init__()
        self.path = path

    def to_params_dict(self) -> dict[str, Any]:
        """パスをJSON互換の辞書へ変換する。"""
        return {"path": str(self.path)}

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "CompilerInputFileNotFoundError":
        """保存用辞書からパスを復元する。"""
        path = params["path"]
        if type(path) is not str:
            raise TypeError("pathはstrである必要があります")
        return cls(path=Path(path))


class CompilerDiagnosticError(CompileStageError):
    """コンパイラがソースコードのエラーを報告した。"""

    error_type_id: ClassVar[str] = "compiler_diagnostic"


class CompilerExecutionFailedError(CompileStageError):
    """コンパイラを正常に起動・実行できなかった。"""

    error_type_id: ClassVar[str] = "compiler_execution_failed"


class CompilerTimeoutError(CompileStageError):
    """コンパイラからの応答が制限時間内に返らなかった。"""

    error_type_id: ClassVar[str] = "timeout"
