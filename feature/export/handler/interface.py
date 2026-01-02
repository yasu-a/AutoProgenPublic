from abc import ABC, abstractmethod
from abc import abstractmethod as view_abstractmethod
from pathlib import Path


# ===== Handler Interfaces (Viewから見たHandlerのインターフェース) =====

class IScoreExportDialogHandler(ABC):
    """点数エクスポートダイアログViewから見たHandlerのインターフェース"""

    @abstractmethod
    def set_view(self, view: "IScoreExportDialogView") -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        raise NotImplementedError()

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()

    @abstractmethod
    def on_excel_path_changed(self, excel_path: str) -> None:
        """Excelファイルパスが変更されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_excel_path_select_requested(self) -> None:
        """Excelファイル選択要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_export_requested(self) -> None:
        """エクスポート要求"""
        raise NotImplementedError()


# ===== View Interfaces (Handlerから見たViewのインターフェース) =====

# Not inheriting from ABC to avoid metaclass conflict with Qt classes
class IScoreExportDialogView:
    """Handlerから見た点数エクスポートダイアログのインターフェース"""

    @view_abstractmethod
    def set_excel_path(self, path: str) -> None:
        """Excelファイルパスを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_excel_path(self) -> str:
        """Excelファイルパスを取得"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_worksheet_names(self, names: list[str]) -> None:
        """ワークシート名リストを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_selected_worksheet_name(self) -> str:
        """選択中のワークシート名を取得"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_message(self, message: str) -> None:
        """メッセージを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_export_enabled(self, enabled: bool) -> None:
        """エクスポートボタンの有効/無効を設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_excel_path_valid(self, valid: bool) -> None:
        """Excelファイルパスの有効性を設定（スタイル変更用）"""
        raise NotImplementedError()

    @view_abstractmethod
    def show_export_confirmation(self, message: str) -> bool:
        """エクスポート確認ダイアログを表示（戻り値: True=実行, False=キャンセル）"""
        raise NotImplementedError()

    @view_abstractmethod
    def show_export_success(self, backup_path: Path | None, message: str) -> bool:
        """エクスポート成功ダイアログを表示（戻り値: True=ファイルを開く, False=閉じる）"""
        raise NotImplementedError()

    @view_abstractmethod
    def show_export_error(self, error_message: str) -> None:
        """エクスポートエラーダイアログを表示"""
        raise NotImplementedError()

    @view_abstractmethod
    def show_file_dialog(self, default_path: Path) -> Path | None:
        """ファイル選択ダイアログを表示（戻り値: 選択されたパス、キャンセル時はNone）"""
        raise NotImplementedError()
