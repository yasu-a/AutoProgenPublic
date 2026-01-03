import os
from pathlib import Path

from PyQt5.QtCore import QStandardPaths

from feature.export.domain.interface.service import (
    ExcelLayoutDetectionError,
    HeaderRowNotFoundError,
    StudentNameColumnNotFoundError,
    ScoreColumnNotFoundError,
    DataRowNotFoundError,
)
from feature.export.handler.interface import (
    IExcelScoreExportTabHandler,
    IExcelScoreExportTabView,
)
from feature.export.usecase.interface import (
    IListExcelWorksheetUseCase,
    IGetExcelSheetPreviewUseCase,
    IAutoDetectExcelLayoutUseCase,
    IExecuteExcelScoreUpdateUseCase,
)
from shared.domain.value.excel_cell_table import ExcelCellTable
from shared.domain.value.identifier import TargetID


class ExcelScoreExportTabHandler(IExcelScoreExportTabHandler):
    """ExcelScoreExportTab専任のHandler"""

    def __init__(
            self,
            *,
            view: IExcelScoreExportTabView | None,
            list_excel_worksheet_usecase: IListExcelWorksheetUseCase,
            get_excel_sheet_preview_usecase: IGetExcelSheetPreviewUseCase,
            auto_detect_excel_layout_usecase: IAutoDetectExcelLayoutUseCase,
            execute_excel_score_update_usecase: IExecuteExcelScoreUpdateUseCase,
            target_id: TargetID,
    ):
        self._view: IExcelScoreExportTabView | None = view
        self._list_excel_worksheet_usecase = list_excel_worksheet_usecase
        self._get_excel_sheet_preview_usecase = get_excel_sheet_preview_usecase
        self._auto_detect_excel_layout_usecase = auto_detect_excel_layout_usecase
        self._execute_excel_score_update_usecase = execute_excel_score_update_usecase
        self._target_id = target_id
        self._current_excel_cell_table: ExcelCellTable | None = None

    def set_view(self, view: IExcelScoreExportTabView) -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        self._view = view

    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        # Excelタブの初期化処理（必要に応じて実装）
        pass

    def on_excel_path_select_requested(self) -> None:
        """Excelファイル選択要求"""
        default_path = Path(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        selected_path = self._view.show_file_dialog(default_path)
        if selected_path:
            self._view.excel_tab.set_excel_path(str(selected_path))
            self.on_excel_path_changed(str(selected_path))

    def on_excel_path_changed(self, excel_path: str) -> None:
        """Excelファイルパスが変更されたとき"""
        excel_fullpath = Path(excel_path)

        # パスの検証
        if not excel_fullpath.exists() or not excel_fullpath.is_file() or excel_fullpath.suffix != ".xlsx":
            self._view.excel_tab.set_sheet_names([])
            self._view.excel_tab.set_sheet_preview_data({})
            return

        try:
            # シート名一覧を取得
            sheet_names = self._list_excel_worksheet_usecase.execute(excel_path=excel_fullpath)
            self._view.excel_tab.set_sheet_names(sheet_names)

            # 最初のシートを選択してプレビューを表示
            if sheet_names:
                self._view.excel_tab._list_sheets.setCurrentRow(0)
                self.on_excel_sheet_selection_changed()
        except Exception as e:
            self._view.show_export_error(f"Excelファイルの読み込みに失敗しました: {e}")

    def on_excel_sheet_selection_changed(self) -> None:
        """Excelシート選択が変更されたとき"""
        excel_path = self._view.excel_tab.get_excel_path()
        if not excel_path:
            self._view.excel_tab.clear_message()
            return

        excel_fullpath = Path(excel_path)
        sheet_name = self._view.excel_tab.get_selected_sheet_name()
        if not sheet_name:
            self._view.excel_tab.clear_message()
            return

        try:
            # プレビューデータを取得
            preview_data = self._get_excel_sheet_preview_usecase.execute(
                excel_path=excel_fullpath,
                sheet_name=sheet_name,
            )
            # dictからExcelCellTableに変換
            from shared.domain.value.excel_cell_table import ExcelCellTable
            excel_cell_table = ExcelCellTable(preview_data)
            self._current_excel_cell_table = excel_cell_table
            self._view.excel_tab.set_sheet_preview_data(preview_data)

            # 自動検出を実行
            self._auto_detect_and_update_message()
        except Exception as e:
            self._view.excel_tab.show_message(f"シートの読み込みに失敗しました: {e}",
                                              is_success=False)
            self._view.show_export_error(f"シートの読み込みに失敗しました: {e}")

    def _auto_detect_and_update_message(self) -> None:
        """自動検出を実行してメッセージを更新"""
        if self._current_excel_cell_table is None:
            self._view.excel_tab.show_message("シートデータが読み込まれていません。",
                                              is_success=False)
            return

        try:
            # 自動検出を実行
            mapping, row_range = self._auto_detect_excel_layout_usecase.execute(
                excel_cell_table=self._current_excel_cell_table,
                target_id=self._target_id,
            )

            # プレビュー用に問X列のインデックスを渡す（書き込み列が問X列）
            self._view.excel_tab.set_mapping_settings(
                mapping,
                row_range,
                target_id_col=mapping.score_write_column_index,
            )

            # 成功メッセージ
            self._view.excel_tab.show_message(
                f"レイアウトを自動検出しました。学籍番号列: {mapping.student_id_column_index}, "
                f"氏名列: {mapping.student_name_column_index}, "
                f"書き込み列: {mapping.score_write_column_index}, "
                f"行範囲: {row_range.start_row_index + 1}～{row_range.end_row_index + 1}",
                is_success=True
            )
        except HeaderRowNotFoundError:
            error_msg = "「学籍番号」を含むヘッダー行が見つかりません。手動で設定してください。"
            self._view.excel_tab.show_message(error_msg, is_success=False)
            # 未設定にする
            self._view.excel_tab.set_mapping_settings(None, None)
        except StudentNameColumnNotFoundError:
            error_msg = "「氏名」を含む列が見つかりません。手動で設定してください。"
            self._view.excel_tab.show_message(error_msg, is_success=False)
            # 未設定にする
            self._view.excel_tab.set_mapping_settings(None, None)
        except ScoreColumnNotFoundError as e:
            error_msg = f"設問番号列（問{int(e.target_id)}）が見つかりません。手動で設定してください。"
            self._view.excel_tab.show_message(error_msg, is_success=False)
            # 未設定にする
            self._view.excel_tab.set_mapping_settings(None, None)
        except DataRowNotFoundError:
            error_msg = "有効なデータ行が見つかりません。手動で設定してください。"
            self._view.excel_tab.show_message(error_msg, is_success=False)
            # 未設定にする
            self._view.excel_tab.set_mapping_settings(None, None)
        except ExcelLayoutDetectionError:
            error_msg = "レイアウトの自動検出に失敗しました。手動で設定してください。"
            self._view.excel_tab.show_message(error_msg, is_success=False)
            # 未設定にする
            self._view.excel_tab.set_mapping_settings(None, None)
        except Exception as e:
            error_msg = f"予期せぬエラーが発生しました: {e}"
            self._view.excel_tab.show_message(error_msg, is_success=False)

    def on_excel_mapping_changed(self) -> None:
        """マッピング設定が変更されたとき"""
        # Viewに色の更新を通知
        self._view.excel_tab.update_preview_colors()

    def on_export_requested(self) -> None:
        """エクスポート要求"""
        excel_path = self._view.excel_tab.get_excel_path()
        sheet_name = self._view.excel_tab.get_selected_sheet_name()

        if not excel_path:
            self._view.show_export_error("Excelファイルを選択してください。")
            return

        if not sheet_name:
            self._view.show_export_error("シートを選択してください。")
            return

        excel_fullpath = Path(excel_path)
        mapping, row_range = self._view.excel_tab.get_mapping_settings()

        try:
            backup_path = self._execute_excel_score_update_usecase.execute(
                excel_path=excel_fullpath,
                sheet_name=sheet_name,
                mapping=mapping,
                row_range=row_range,
            )

            backup_message = (
                f"Excelファイルのバックアップを取りました：\n{backup_path!s}\n\n"
                if backup_path
                else ""
            )
            message = backup_message + "エクスポートが完了しました。ワークブックを開いて確認しますか？"

            if self._view.show_export_success(backup_path, message):
                os.startfile(excel_fullpath)
        except Exception as e:
            self._view.show_export_error(f"エクスポートに失敗しました: {e}")
