"""ステージエラーを保存可能なデータへ変換し、元の具象エラーへ復元する。"""

from dataclasses import dataclass
from typing import Any

from autoprogen.domain.error.stage import build as build_errors
from autoprogen.domain.error.stage import compile as compile_errors
from autoprogen.domain.error.stage import execute as execute_errors
from autoprogen.domain.error.stage import test as test_errors
from autoprogen.domain.error.stage.base import StageError


@dataclass(frozen=True, slots=True)
class StageErrorRecord:
    """ステージエラーを識別し、保存・復元に必要な情報を保持する。

    paramsはJSONで表現できる値を持つ辞書とする。SQLiteへの書き込みは
    Repositoryが担当し、このクラスでは行わない。
    """

    # エラーが発生したステージの識別子（build、compile、execute、test）。
    error_group_id: str

    # ステージ内でエラーの種類を識別する固定文字列。
    error_type_id: str

    # エラー固有の情報。Pathやtuple等は具象エラー側でJSON用に変換する。
    params: dict[str, Any]

    def __post_init__(self) -> None:
        """各フィールドが宣言された型に一致することを確認する。"""
        if type(self.error_group_id) is not str:
            raise TypeError("error_group_idはstrである必要があります")
        if type(self.error_type_id) is not str:
            raise TypeError("error_type_idはstrである必要があります")
        if type(self.params) is not dict:
            raise TypeError("paramsはdictである必要があります")
        if any(type(key) is not str for key in self.params):
            raise TypeError("paramsのキーはstrである必要があります")


# 保存対象のStageErrorの具象型。ステージ別の基底クラスは含めない。
_ERROR_TYPES: tuple[type[StageError], ...] = (
    build_errors.SubmissionNotFoundError,
    build_errors.SourceFilenameMultipleNumbersError,
    build_errors.SourceFilenameNoNumberError,
    build_errors.MultipleSourceFilesError,
    build_errors.SubmissionSourceNotFoundError,
    build_errors.SourceEncodingUnknownError,
    compile_errors.SourceSafetyViolationError,
    compile_errors.SourceSafetyDecodeError,
    compile_errors.CompilerNotConfiguredError,
    compile_errors.CompileSourceNotFoundError,
    compile_errors.VsDevToolNotFoundError,
    compile_errors.CompilerWorkingDirectoryNotFoundError,
    compile_errors.CompilerInputFileNotFoundError,
    compile_errors.CompilerDiagnosticError,
    compile_errors.CompilerExecutionFailedError,
    compile_errors.CompilerTimeoutError,
    execute_errors.ExecutableNotFoundError,
    execute_errors.ExecutionTimeoutError,
    test_errors.ExecuteResultNotFoundError,
    test_errors.ExecuteResultFailedError,
    test_errors.OutputMatchingError,
)


_ID_TO_ERROR_TYPE: dict[tuple[str, str], type[StageError]] = {
    (error_type.error_group_id, error_type.error_type_id): error_type
    for error_type in _ERROR_TYPES
}


def _find_error_type_by_id(
        error_group_id: str,
        error_type_id: str,
) -> type[StageError] | None:
    """グループIDと種別IDに対応する具象エラー型を返す。"""
    key = error_group_id, error_type_id
    return _ID_TO_ERROR_TYPE.get(key)


class StageErrorCodec:
    """具象StageErrorとStageErrorRecordを相互変換する。

    具体型とIDの対応は明示的に登録する。個々のパラメータの必須項目や
    型の検証は、各具象エラーのfrom_params_dict()に委ねる。
    """

    def encode(self, error: StageError) -> StageErrorRecord:
        """具象エラーが持つ固定IDとパラメータを保存用レコードへ変換する。"""
        if not isinstance(error, StageError):
            raise TypeError("errorにはStageErrorを指定してください")
        return StageErrorRecord(
            error_group_id=error.error_group_id,
            error_type_id=error.error_type_id,
            params=error.to_params_dict(),
        )

    def decode(self, record: StageErrorRecord) -> StageError:
        """レコードの固定IDを使い、元の具象エラーへ復元する。"""
        if not isinstance(record, StageErrorRecord):
            raise TypeError("recordにはStageErrorRecordを指定してください")
        ids = record.error_group_id, record.error_type_id
        error_type = _find_error_type_by_id(*ids)
        if error_type is None:
            raise ValueError(f"未知のStageError IDです: {ids!r}")
        try:
            error = error_type.from_params_dict(record.params)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"StageErrorのパラメータが不正です: {ids!r}") from exc
        if type(error) is not error_type:
            raise TypeError(f"復元されたエラーの型が不正です: {ids!r}")
        return error
