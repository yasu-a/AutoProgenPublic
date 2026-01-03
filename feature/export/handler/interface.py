from abc import ABC, abstractmethod
from pathlib import Path

from feature.export.view.component.tab_excel import ExcelScoreExportTab
from feature.export.view.component.tab_simple import SimpleScoreExportTab


# ===== Handler Interfaces (Viewから見たHandlerのインターフェース) =====

class ISimpleScoreExportTabHandler(ABC):
    """SimpleScoreExportTabから見たHandlerのインターフェース"""

    @abstractmethod
    def set_view(self, view: "ISimpleScoreExportTabView") -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        raise NotImplementedError()

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()

    @abstractmethod
    def on_export_requested(self) -> None:
        """エクスポート要求"""
        raise NotImplementedError()


class IExcelScoreExportTabHandler(ABC):
    """ExcelScoreExportTabから見たHandlerのインターフェース"""

    @abstractmethod
    def set_view(self, view: "IExcelScoreExportTabView") -> None:
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
    def on_excel_sheet_selection_changed(self) -> None:
        """Excelシート選択が変更されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_excel_mapping_changed(self) -> None:
        """マッピング設定が変更されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_export_requested(self) -> None:
        """エクスポート要求"""
        raise NotImplementedError()


# ===== View Interfaces (Handlerから見たViewのインターフェース) =====

# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class ISimpleScoreExportTabView:
    """Handlerから見たSimpleScoreExportTabのインターフェース"""

    @property
    @abstractmethod
    def simple_tab(self) -> SimpleScoreExportTab:
        """SimpleScoreExportTabへのアクセサ"""
        raise NotImplementedError()

    @abstractmethod
    def show_export_error(self, error_message: str) -> None:
        """エクスポートエラーダイアログを表示"""
        raise NotImplementedError()

    @abstractmethod
    def show_export_success(self, backup_path: Path | None, message: str) -> bool:
        """エクスポート成功ダイアログを表示（戻り値: True=ファイルを開く, False=閉じる）"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class IExcelScoreExportTabView:
    """Handlerから見たExcelScoreExportTabのインターフェース"""

    @property
    @abstractmethod
    def excel_tab(self) -> ExcelScoreExportTab:
        """ExcelScoreExportTabへのアクセサ"""
        raise NotImplementedError()

    @abstractmethod
    def show_export_error(self, error_message: str) -> None:
        """エクスポートエラーダイアログを表示"""
        raise NotImplementedError()

    @abstractmethod
    def show_export_success(self, backup_path: Path | None, message: str) -> bool:
        """エクスポート成功ダイアログを表示（戻り値: True=ファイルを開く, False=閉じる）"""
        raise NotImplementedError()

    @abstractmethod
    def show_file_dialog(self, default_path: Path) -> Path | None:
        """ファイル選択ダイアログを表示（戻り値: 選択されたパス、キャンセル時はNone）"""
        raise NotImplementedError()
