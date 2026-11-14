from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from autoprogen.domain.error.stage.base import StageError


class BuildStageError(StageError):
    """BUILDステージで発生するエラーの基底クラス。"""

    error_group_id: ClassVar[str] = "build"


class SubmissionNotFoundError(BuildStageError):
    """学生の提出物が存在しない。"""

    error_type_id: ClassVar[str] = "not_submitted"


class SourceFilenameMultipleNumbersError(BuildStageError):
    """ソースファイル名に数字が複数含まれている。"""

    error_type_id: ClassVar[str] = "filename_multiple_numbers"

    # 問題のあるソースファイルの提出フォルダからの相対パス。
    file_relative_path: Path

    # ファイル名から抽出された数字の文字列。
    numbers: tuple[str, ...]

    def __init__(
            self,
            *,
            file_relative_path: Path,
            numbers: Sequence[str],
    ) -> None:
        """問題のあるファイルパスと抽出された数字を保持する。"""
        if not isinstance(file_relative_path, Path):
            raise TypeError("file_relative_pathはPathである必要があります")
        if any(type(number) is not str for number in numbers):
            raise TypeError("numbersの要素はstrである必要があります")
        super().__init__()
        self.file_relative_path = file_relative_path
        self.numbers = tuple(numbers)

    def to_params_dict(self) -> dict[str, Any]:
        """ファイルパスと数字をJSON互換の辞書へ変換する。"""
        return {
            "file_relative_path": str(self.file_relative_path),
            "numbers": list(self.numbers),
        }

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "SourceFilenameMultipleNumbersError":
        """保存用辞書からファイルパスと数字を復元する。"""
        file_relative_path = params["file_relative_path"]
        numbers = params["numbers"]
        if type(file_relative_path) is not str:
            raise TypeError("file_relative_pathはstrである必要があります")
        if type(numbers) is not list or any(type(number) is not str for number in numbers):
            raise TypeError("numbersはstrのlistである必要があります")
        return cls(
            file_relative_path=Path(file_relative_path),
            numbers=tuple(numbers),
        )


class SourceFilenameNoNumberError(BuildStageError):
    """ソースファイル名に数字が含まれていない。"""

    error_type_id: ClassVar[str] = "filename_no_number"

    # 問題のあるソースファイルの提出フォルダからの相対パス。
    file_relative_path: Path

    def __init__(self, *, file_relative_path: Path) -> None:
        """問題のあるファイルパスを保持する。"""
        if not isinstance(file_relative_path, Path):
            raise TypeError("file_relative_pathはPathである必要があります")
        super().__init__()
        self.file_relative_path = file_relative_path

    def to_params_dict(self) -> dict[str, Any]:
        """ファイルパスをJSON互換の辞書へ変換する。"""
        return {"file_relative_path": str(self.file_relative_path)}

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "SourceFilenameNoNumberError":
        """保存用辞書からファイルパスを復元する。"""
        file_relative_path = params["file_relative_path"]
        if type(file_relative_path) is not str:
            raise TypeError("file_relative_pathはstrである必要があります")
        return cls(file_relative_path=Path(file_relative_path))


class MultipleSourceFilesError(BuildStageError):
    """対象となるソースファイルが複数見つかった。"""

    error_type_id: ClassVar[str] = "multiple_sources"

    # 見つかったソースファイルの提出フォルダからの相対パス。
    file_relative_paths: tuple[Path, ...]

    def __init__(self, *, file_relative_paths: Sequence[Path]) -> None:
        """複数見つかったソースファイルのパスを保持する。"""
        if any(not isinstance(path, Path) for path in file_relative_paths):
            raise TypeError("file_relative_pathsの要素はPathである必要があります")
        super().__init__()
        self.file_relative_paths = tuple(file_relative_paths)

    def to_params_dict(self) -> dict[str, Any]:
        """複数のファイルパスをJSON互換の辞書へ変換する。"""
        return {
            "file_relative_paths": [str(path) for path in self.file_relative_paths],
        }

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "MultipleSourceFilesError":
        """保存用辞書から複数のファイルパスを復元する。"""
        file_relative_paths = params["file_relative_paths"]
        if type(file_relative_paths) is not list or any(
                type(path) is not str for path in file_relative_paths
        ):
            raise TypeError("file_relative_pathsはstrのlistである必要があります")
        return cls(
            file_relative_paths=tuple(Path(path) for path in file_relative_paths),
        )


class SubmissionSourceNotFoundError(BuildStageError):
    """対象となるソースファイルが見つからなかった。"""

    error_type_id: ClassVar[str] = "source_not_found"


class SourceEncodingUnknownError(BuildStageError):
    """ソースファイルの文字コードを判定できなかった。"""

    error_type_id: ClassVar[str] = "encoding_unknown"

    # 文字コードを判定できなかったファイルの提出フォルダからの相対パス。
    file_relative_path: Path

    def __init__(self, *, file_relative_path: Path) -> None:
        """文字コードを判定できなかったファイルパスを保持する。"""
        if not isinstance(file_relative_path, Path):
            raise TypeError("file_relative_pathはPathである必要があります")
        super().__init__()
        self.file_relative_path = file_relative_path

    def to_params_dict(self) -> dict[str, Any]:
        """ファイルパスをJSON互換の辞書へ変換する。"""
        return {"file_relative_path": str(self.file_relative_path)}

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "SourceEncodingUnknownError":
        """保存用辞書からファイルパスを復元する。"""
        file_relative_path = params["file_relative_path"]
        if type(file_relative_path) is not str:
            raise TypeError("file_relative_pathはstrである必要があります")
        return cls(file_relative_path=Path(file_relative_path))
