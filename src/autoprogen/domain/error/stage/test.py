from typing import Any, ClassVar

from autoprogen.domain.error.stage.base import StageError


class TestStageError(StageError):
    """TESTステージで発生するエラーの基底クラス。"""

    error_group_id: ClassVar[str] = "test"


class ExecuteResultNotFoundError(TestStageError):
    """テスト対象となるEXECUTEステージの結果が存在しない。"""

    error_type_id: ClassVar[str] = "execute_result_not_found"


class ExecuteResultFailedError(TestStageError):
    """EXECUTEステージが失敗しているためテストできない。"""

    error_type_id: ClassVar[str] = "execute_result_failed"


class OutputMatchingError(TestStageError):
    """出力内容のマッチング処理に失敗した。"""

    error_type_id: ClassVar[str] = "output_matching_error"

    # マッチング処理が返した失敗理由。既存の表示内容を保持する。
    detail: str

    def __init__(self, *, detail: str) -> None:
        """マッチング処理が返した失敗理由を保持する。"""
        if type(detail) is not str:
            raise TypeError("detailはstrである必要があります")
        super().__init__()
        self.detail = detail

    def to_params_dict(self) -> dict[str, Any]:
        """失敗理由を保存用辞書へ変換する。"""
        return {"detail": self.detail}

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> "OutputMatchingError":
        """保存用辞書から失敗理由を復元する。"""
        detail = params["detail"]
        if type(detail) is not str:
            raise TypeError("detailはstrである必要があります")
        return cls(detail=detail)
