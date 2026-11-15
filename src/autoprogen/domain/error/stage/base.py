from typing import Any, ClassVar, Self


class StageError(Exception):
    """ステージ処理で発生した構造化可能なエラーを表す。"""

    error_group_id: ClassVar[str]
    error_type_id: ClassVar[str]

    def to_params_dict(self) -> dict[str, Any]:
        """固有パラメータを持たないエラーを空辞書へ変換する。"""
        return {}

    @classmethod
    def from_params_dict(cls, params: dict[str, Any]) -> Self:
        """空のパラメータから固有パラメータを持たないエラーを復元する。"""
        if type(params) is not dict:
            raise TypeError("paramsはdictである必要があります")
        if params:
            raise ValueError("このエラーにパラメータは指定できません")
        return cls()
