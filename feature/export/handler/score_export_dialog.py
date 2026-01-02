import os
from pathlib import Path

from PyQt5.QtCore import QStandardPaths

from feature.export.handler.interface import IScoreExportDialogHandler, IScoreExportDialogView
from feature.export.usecase.interface import IScoreExportUseCase
from feature.scoring.usecase.interface import IStudentMarkListUseCase
from feature.setting.usecase.interface import ISettingGetUseCase
from shared.domain.value.identifier import TargetID


class ScoreExportDialogHandler(IScoreExportDialogHandler):
    """点数エクスポートダイアログ専任のHandler"""

    def __init__(
            self,
            *,
            view: IScoreExportDialogView | None,
            score_export_usecase: IScoreExportUseCase,
            student_list_id_usecase,  # IStudentListIDUseCase
            student_mark_list_usecase: IStudentMarkListUseCase,
            setting_get_usecase: ISettingGetUseCase,
            target_id: TargetID,
    ):
        self._view: IScoreExportDialogView | None = view
        self._score_export_usecase = score_export_usecase
        self._student_list_id_usecase = student_list_id_usecase
        self._student_mark_list_usecase = student_mark_list_usecase
        self._setting_get_usecase = setting_get_usecase
        self._target_id = target_id

    def set_view(self, view: IScoreExportDialogView) -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        self._view = view

    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        pass  # 初期化時は特に何もしない

    def on_excel_path_select_requested(self) -> None:
        """Excelファイル選択要求"""
        default_path = Path(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))
        selected_path = self._view.show_file_dialog(default_path)
        if selected_path:
            self._view.set_excel_path(str(selected_path))
            # パスが変更されたので、on_excel_path_changedを呼ぶ
            self.on_excel_path_changed(str(selected_path))

    def on_excel_path_changed(self, excel_path: str) -> None:
        """Excelファイルパスが変更されたとき"""
        excel_fullpath = Path(excel_path)

        # パスの検証
        if not excel_fullpath.exists() or not excel_fullpath.is_file() or excel_fullpath.suffix != ".xlsx":
            self._view.set_excel_path_valid(False)
            self._view.set_worksheet_names([])
            self._view.set_message("")
            self._view.set_export_enabled(False)
            return

        # 生徒IDリストを取得
        student_ids = self._student_list_id_usecase.execute()

        # ワークシートの状態を取得
        worksheet_stats = self._score_export_usecase.list_worksheet_stats(
            excel_fullpath=excel_fullpath,
            student_ids=student_ids,
        )

        # 有効なワークシート名を設定
        valid_names = [stat.name for stat in worksheet_stats if stat.valid]
        self._view.set_worksheet_names(valid_names)

        # メッセージを構築
        messages = []
        invalid_stats = [stat for stat in worksheet_stats if not stat.valid]

        if invalid_stats and not valid_names:
            messages.append(
                "すべてのワークシートが読み込めません。\n成績記録用のワークブックを指定しましたか？")
        elif invalid_stats:
            messages.append(
                "ワークシートの読み込みが完了しました。\nただし次のシートにはエクスポートできません。")
        else:
            messages.append("すべてのワークシートを読み込みました")

        for stat in invalid_stats:
            messages.append(f" [ {stat.name} ] \n{stat.message}")

        self._view.set_message("\n\n".join(messages))

        # 有効なワークシートがある場合はエクスポートボタンを有効化
        self._view.set_excel_path_valid(len(valid_names) > 0)
        self._view.set_export_enabled(len(valid_names) > 0)

    def on_export_requested(self) -> None:
        """エクスポート要求"""
        excel_path = self._view.get_excel_path()
        excel_fullpath = Path(excel_path)

        # パスの検証
        if not excel_fullpath.exists() or not excel_fullpath.is_file() or excel_fullpath.suffix != ".xlsx":
            return

        worksheet_name = self._view.get_selected_worksheet_name()
        if not worksheet_name:
            return

        # 生徒IDリストと採点データを取得
        student_ids = self._student_list_id_usecase.execute()
        student_marks = self._student_mark_list_usecase.execute()

        # 既存データの確認
        has_existing_data = self._score_export_usecase.has_data(
            excel_fullpath=excel_fullpath,
            worksheet_name=worksheet_name,
            student_ids=student_ids,
            target_id=self._target_id,
        )

        if has_existing_data:
            confirmation_message = (
                f"シート名{worksheet_name}の設問{int(self._target_id)}に入力データが存在しますが上書きしますか？"
            )
            if not self._view.show_export_confirmation(confirmation_message):
                return

        # バックアップ設定を取得
        setting = self._setting_get_usecase.execute()
        do_backup = setting.backup_before_export

        # エクスポート実行
        result = self._score_export_usecase.execute(
            excel_fullpath=excel_fullpath,
            worksheet_name=worksheet_name,
            student_marks=student_marks,
            target_id=self._target_id,
            do_backup=do_backup,
        )

        if not result.success:
            self._view.show_export_error(result.error_message or "エクスポートに失敗しました")
            return

        # 成功メッセージを表示
        backup_message = (
            f"Excelファイルのバックアップを取りました：\n{result.backup_path!s}\n\n"
            if result.backup_path
            else ""
        )
        success_message = backup_message + "エクスポートが完了しました。ワークブックを開いて確認しますか？"

        if self._view.show_export_success(result.backup_path, success_message):
            # ファイルを開く
            os.startfile(excel_fullpath)
            # ダイアログを閉じる（View側でaccept()を呼ぶ必要があるが、ここでは通知のみ）
