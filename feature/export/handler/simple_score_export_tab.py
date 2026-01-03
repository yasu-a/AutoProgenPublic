import os
from pathlib import Path

from PyQt5.QtCore import QStandardPaths

from feature.export.handler.interface import (
    ISimpleScoreExportTabHandler,
    ISimpleScoreExportTabView,
)
from feature.export.usecase.interface import (
    IGetSimpleScoreExportDataUseCase,
    IExecuteSimpleScoreExportUseCase,
)
from feature.projman.usecase.interface import ICurrentProjectSummaryGetUseCase


class SimpleScoreExportTabHandler(ISimpleScoreExportTabHandler):
    """SimpleScoreExportTab専任のHandler"""

    def __init__(
        self,
        *,
        view: ISimpleScoreExportTabView | None,
        get_simple_export_data_usecase: IGetSimpleScoreExportDataUseCase,
        execute_simple_export_usecase: IExecuteSimpleScoreExportUseCase,
        current_project_summary_get_usecase: ICurrentProjectSummaryGetUseCase,
    ):
        self._view: ISimpleScoreExportTabView | None = view
        self._get_simple_export_data_usecase = get_simple_export_data_usecase
        self._execute_simple_export_usecase = execute_simple_export_usecase
        self._current_project_summary_get_usecase = current_project_summary_get_usecase

    def set_view(self, view: ISimpleScoreExportTabView) -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        self._view = view

    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        # 単純エクスポート用データの取得
        data = self._get_simple_export_data_usecase.execute()
        self._view.simple_tab.set_preview_data(data)
        
        # デフォルトフォルダ（ダウンロードフォルダ）
        default_folder = Path(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        self._view.simple_tab.set_folder_path(str(default_folder))
        
        # デフォルトファイル名（プロジェクト名）
        try:
            project_summary = self._current_project_summary_get_usecase.execute()
            default_filename = project_summary.project_name
        except Exception:
            default_filename = "score_export"
        self._view.simple_tab.set_filename(default_filename)

    def on_export_requested(self) -> None:
        """エクスポート要求"""
        folder_path = self._view.simple_tab.get_folder_path()
        filename = self._view.simple_tab.get_filename()
        format_enum = self._view.simple_tab.get_selected_format()
        data = self._get_simple_export_data_usecase.execute()

        if not folder_path:
            self._view.show_export_error("出力先フォルダを指定してください。")
            return
        
        if not filename:
            self._view.show_export_error("ファイル名を入力してください。")
            return

        try:
            folder = Path(folder_path)
            exported_path = self._execute_simple_export_usecase.execute(
                folder=folder,
                filename_no_ext=filename,
                export_format=format_enum,
                data=data,
            )
            
            message = f"エクスポートが完了しました。\n{exported_path}\n\nファイルを開きますか？"
            if self._view.show_export_success(None, message):
                os.startfile(exported_path)
        except Exception as e:
            self._view.show_export_error(f"エクスポートに失敗しました: {e}")

