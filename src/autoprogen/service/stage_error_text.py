"""構造化されたステージエラーを画面表示用の日本語へ変換する。"""

from autoprogen.domain.error.stage.base import StageError
from autoprogen.domain.error.stage.build import (
    MultipleSourceFilesError,
    SourceEncodingUnknownError,
    SourceFilenameMultipleNumbersError,
    SourceFilenameNoNumberError,
    SubmissionNotFoundError,
    SubmissionSourceNotFoundError,
)
from autoprogen.domain.error.stage.compile import (
    CompileSourceNotFoundError,
    CompilerDiagnosticError,
    CompilerExecutionFailedError,
    CompilerInputFileNotFoundError,
    CompilerNotConfiguredError,
    CompilerTimeoutError,
    CompilerWorkingDirectoryNotFoundError,
    SourceSafetyViolationError,
    VsDevToolNotFoundError,
)
from autoprogen.domain.error.stage.execute import ExecutableNotFoundError, ExecutionTimeoutError
from autoprogen.domain.error.stage.test import (
    ExecuteResultFailedError,
    ExecuteResultNotFoundError,
    OutputMatchingError,
)
from autoprogen.domain.model.student_stage_result import (
    AbstractFailureStudentStageResult,
    CompileFailureStudentStageResult,
)
from autoprogen.domain.service.source_code_check_factory import SourceCodeCheckCatalogFactory


class StageErrorTextFormatter:
    """ステージエラーから従来と同じ概要・詳細文字列を生成する。"""

    def __init__(
            self,
            *,
            source_code_check_catalog_factory: SourceCodeCheckCatalogFactory,
    ) -> None:
        """安全性チェック規則の現在の表示名を取得するFactoryを受け取る。"""
        self._source_code_check_catalog_factory = source_code_check_catalog_factory

    def format_summary(self, error: StageError) -> str:
        """構造化エラーを学生テーブル用の概要文字列へ変換する。"""
        if isinstance(error, SubmissionNotFoundError):
            return "未提出の学生です。"
        if isinstance(error, SourceFilenameMultipleNumbersError):
            return (
                "提出フォルダからソースファイルを抽出中にエラーが発生しました。\n"
                f"ファイル名{error.file_relative_path!s}から設問番号を判別できません。\n"
                f"ファイル名に数字が複数含まれています: {', '.join(error.numbers)}"
            )
        if isinstance(error, SourceFilenameNoNumberError):
            return (
                "提出フォルダからソースファイルを抽出中にエラーが発生しました。\n"
                f"ファイル名{error.file_relative_path!s}から設問番号を判別できません。\n"
                "ファイル名に数字が含まれていません。"
            )
        if isinstance(error, MultipleSourceFilesError):
            paths = "\n".join(map(str, error.file_relative_paths))
            return f"提出物に複数のソースファイルが見つかりました。\n{paths}"
        if isinstance(error, SubmissionSourceNotFoundError):
            return "提出物にソースファイルが見つかりませんでした。"
        if isinstance(error, SourceEncodingUnknownError):
            return (
                "ソースファイルの文字コードが判定できません。\n"
                f"ファイル名: {error.file_relative_path!s}\n"
            )
        if isinstance(error, SourceSafetyViolationError):
            return self._format_safety_violation(error)
        if isinstance(error, CompilerNotConfiguredError):
            return "コンパイルに失敗しました。\nコンパイラが設定されていません"
        if isinstance(error, CompileSourceNotFoundError):
            return "コンパイルに失敗しました。\nコンパイル対象が存在しません"
        if isinstance(error, VsDevToolNotFoundError):
            detail = f"Visual Studio 開発者ツールが存在しません: {error.path!s}"
            return self._format_compiler_failure(detail)
        if isinstance(error, CompilerWorkingDirectoryNotFoundError):
            detail = f"コンパイル先のディレクトリが存在しません: {error.path!s}"
            return self._format_compiler_failure(detail)
        if isinstance(error, CompilerInputFileNotFoundError):
            detail = f"コンパイル対象のファイルが存在しません: {error.path!s}"
            return self._format_compiler_failure(detail)
        if isinstance(error, CompilerDiagnosticError):
            return self._format_compiler_failure("コンパイルエラーが発生しました")
        if isinstance(error, CompilerExecutionFailedError):
            return self._format_compiler_failure("コンパイラを実行できません")
        if isinstance(error, CompilerTimeoutError):
            return self._format_compiler_failure("コンパイラからの応答がタイムアウトしました")
        if isinstance(error, ExecutableNotFoundError):
            return "実行対象が存在しません"
        if isinstance(error, ExecutionTimeoutError):
            return (
                "実行がタイムアウトしました\n"
                "この環境のスペックに対して並列タスク数が多すぎる・"
                "プログラムが入力を待っている・無限ループしているなどの可能性があります"
            )
        if isinstance(error, ExecuteResultNotFoundError):
            return "実行結果が見つかりません"
        if isinstance(error, ExecuteResultFailedError):
            return "失敗した実行のテストはできません"
        if isinstance(error, OutputMatchingError):
            return error.detail
        raise TypeError(f"未対応のステージエラーです: {type(error).__name__}")

    def format_detail(self, result: AbstractFailureStudentStageResult) -> str:
        """失敗結果をエラー詳細画面用の文字列へ変換する。"""
        summary = self.format_summary(result.error)
        if isinstance(result, CompileFailureStudentStageResult):
            return summary + "\n" + result.output
        return summary

    def _format_compiler_failure(self, detail: str) -> str:
        """コンパイラ実行失敗を従来の案内文と結合する。"""
        return (
            "コンパイルに失敗しました。\n"
            "コンパイルに失敗しました。ソースコードを直接Visual Studioで開いて"
            "実行してください．\n"
            "文字コードが原因の場合、Visual Studioで実行すると正常に動作することが"
            f"あります。\n{detail}"
        )

    def _format_safety_violation(self, error: SourceSafetyViolationError) -> str:
        """安全性チェックの検出結果を現在の規則名で整形する。"""
        catalog = self._source_code_check_catalog_factory.create()
        rule_names = {
            (group.group_id, entry.check_id): entry.name
            for group in catalog.groups
            for entry in group.entries
        }
        detail_lines = [
            f"{finding.line_number}行目: "
            f"[{finding.group_id}.{finding.check_id}] "
            f"{rule_names.get((finding.group_id, finding.check_id), '検出した規則')}"
            for finding in error.findings[:50]
        ]
        if len(error.findings) > 50:
            detail_lines.append(f"ほか{len(error.findings) - 50}件の検出があります。")
        return (
            "ソースコードの安全性チェックで問題が検出されたため、"
            "コンパイルを停止しました。\n"
            f"検査対象SHA-256: {error.source_sha256}\n"
            + "\n".join(detail_lines)
        )
