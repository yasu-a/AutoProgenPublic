from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from feature.setting.usecase.interface import TestCompileStageResultDto
from shared.domain.value.setting import Setting


# ===== CompilerSearch Interfaces =====

class ICompilerSearchHandler(ABC):
    """コンパイラ検索Viewから見たHandlerのインターフェース"""

    @abstractmethod
    def set_view(self, view: "ICompilerSearchView") -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        raise NotImplementedError()

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる（検索開始）"""
        raise NotImplementedError()

    @abstractmethod
    def on_search_finished(self, paths: list[Path]) -> None:
        """検索が完了したとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_search_progress_updated(self, current_path: Path) -> None:
        """検索の進捗が更新されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_close_requested(self) -> None:
        """ダイアログが閉じられようとしたとき（検索の停止）"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class ICompilerSearchView:
    """Handlerから見たコンパイラ検索のインターフェース"""

    @abstractmethod
    def set_progress_text(self, text: str) -> None:
        """進捗テキストを設定"""
        raise NotImplementedError()

    @abstractmethod
    def show_path_selection(self, paths: list[Path]) -> Path | None:
        """パス選択を表示（戻り値: 選択されたパス、キャンセル時はNone）"""
        raise NotImplementedError()

    @abstractmethod
    def show_not_found_message(self) -> None:
        """パスが見つからなかったメッセージを表示"""
        raise NotImplementedError()

    @abstractmethod
    def accept_dialog(self) -> None:
        """ダイアログをAcceptして閉じる"""
        raise NotImplementedError()

    @abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得（QObjectのparent用）"""
        raise NotImplementedError()


# ===== SettingEditDialog Interfaces =====

@dataclass
class SettingEditDTO:
    """View↔Handler間の設定値受け渡し用DTO（入力された生の値を格納）"""
    compiler_tool_fullpath: str | None  # Pathではなくstr
    compile_timeout: float
    max_workers: int
    backup_before_export: bool
    show_editing_symbols_in_stream_content: bool
    show_editing_symbols_in_source_code: bool
    enable_line_wrap_in_stream_content: bool
    enable_line_wrap_in_source_code: bool


# ===== SettingEditHandler Exceptions =====

class SettingEditValidationError(Exception):
    """SettingEditHandlerのバリデーションエラーの基底クラス"""
    pass


class PathNotAbsoluteError(SettingEditValidationError):
    """パスが絶対パスでない場合に投げられる例外"""
    pass


class PathNotExistsError(SettingEditValidationError):
    """指定されたパスが存在しない場合に投げられる例外"""
    pass


class ISettingEditHandler(ABC):
    """Viewから見たHandlerのインターフェース"""

    @abstractmethod
    def set_view(self, view: "ISettingEditView") -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        raise NotImplementedError()

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()

    @abstractmethod
    def on_compiler_test_requested(self, compiler_tool_fullpath: Path) -> None:
        """コンパイルテストが要求されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_compiler_search_requested(self) -> None:
        """コンパイラ自動検索が要求されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_save_requested(self, setting: Setting) -> None:
        """
        保存が要求されたとき（内部用）
        """
        raise NotImplementedError()

    @abstractmethod
    def on_save_button_clicked(self) -> bool:
        """
        保存ボタンがクリックされたとき
        戻り値: 閉じることを許可するか（True=許可、False=拒否）
        """
        raise NotImplementedError()

    @abstractmethod
    def on_cancel_requested(self) -> bool:
        """
        キャンセルボタンがクリックされたとき
        戻り値: 閉じることを許可するか（True=許可、False=拒否）
        """
        raise NotImplementedError()

    @abstractmethod
    def on_close_requested(self) -> bool:
        """
        ダイアログが閉じられようとしたとき（×ボタン）
        戻り値: 閉じることを許可するか（True=許可、False=拒否）
        """
        raise NotImplementedError()

    @abstractmethod
    def validate_dto(self, dto: SettingEditDTO) -> None:
        """
        DTOのバリデーション
        バリデーションに失敗した場合はSettingEditValidationErrorのサブクラスを投げる
        """
        raise NotImplementedError()


# QtのmetaclassとABCのmetaclassが競合するため、ABCを継承しない
# noinspection PyAbstractClass
class ISettingEditView:
    """Handlerから見たViewのインターフェース"""

    @abstractmethod
    def set_settings(self, dto: SettingEditDTO) -> None:
        """設定をViewに設定"""
        raise NotImplementedError()

    @abstractmethod
    def set_compiler_tool_fullpath(self, path: Path | None) -> None:
        """コンパイラツールのパスを設定"""
        raise NotImplementedError()

    @abstractmethod
    def get_settings_dto(self) -> SettingEditDTO:
        """Viewから設定を取得（DTO形式）"""
        raise NotImplementedError()

    @abstractmethod
    def show_test_result(self, result: TestCompileStageResultDto) -> None:
        """コンパイルテスト結果を表示"""
        raise NotImplementedError()

    @abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得（QMessageBoxのparent用）"""
        raise NotImplementedError()

    @abstractmethod
    def show_validation_error(self, error_message: str) -> None:
        """バリデーションエラーを表示"""
        raise NotImplementedError()

    @abstractmethod
    def confirm_discard_changes(self) -> bool:
        """
        変更内容を破棄するか確認
        戻り値: 破棄するか（True=破棄、False=キャンセル）
        """
        raise NotImplementedError()
