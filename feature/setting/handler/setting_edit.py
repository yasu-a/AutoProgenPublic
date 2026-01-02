from pathlib import Path
from typing import TYPE_CHECKING

from feature.setting.handler.interface import ISettingEditHandler, ISettingEditView
from feature.setting.usecase.interface import (
    ISettingGetUseCase,
    ISettingPutUseCase,
    ITestCompileStageUseCase,
    ICompilerSearchUseCase,
)
from shared.domain.value.setting import Setting
from shared.handler.interface import INavigator

if TYPE_CHECKING:
    pass


class SettingEditHandler(ISettingEditHandler):
    """
    SettingEditView専任のHandler
    責務: 設定の読み込み、保存、コンパイルテスト、コンパイラ検索
    """

    def __init__(
            self,
            *,
            view: ISettingEditView | None,
            navigator: INavigator,
            setting_get_usecase: ISettingGetUseCase,
            setting_put_usecase: ISettingPutUseCase,
            test_compile_stage_usecase: ITestCompileStageUseCase,
            compiler_search_usecase: ICompilerSearchUseCase,
    ):
        self._view: ISettingEditView | None = view
        self._navigator = navigator
        self._setting_get_usecase = setting_get_usecase
        self._setting_put_usecase = setting_put_usecase
        self._test_compile_stage_usecase = test_compile_stage_usecase
        self._compiler_search_usecase = compiler_search_usecase

    def set_view(self, view: ISettingEditView) -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        self._view = view

    # ===== ISettingEditHandler実装 =====
    def on_view_initialized(self) -> None:
        """View初期化時に呼ばれる"""
        # 設定を読み込んでViewに設定
        setting = self._setting_get_usecase.execute()
        self._view.set_settings(setting)

    def on_compiler_test_requested(self, compiler_tool_fullpath: Path) -> None:
        """コンパイルテストが要求されたとき"""
        result = self._test_compile_stage_usecase.execute(compiler_tool_fullpath)
        self._view.show_test_result(result)

    def on_compiler_search_requested(self) -> None:
        """コンパイラ自動検索が要求されたとき"""
        # Navigator経由でダイアログを開く
        result = self._navigator.open_compiler_search_dialog(
            self._view.get_parent_widget()
        )
        if result is not None:
            self._view.set_compiler_tool_fullpath(result)

    def on_save_requested(self, setting: Setting) -> tuple[bool, str | None]:
        """
        保存が要求されたとき
        戻り値: (成功したか, エラーメッセージ)
        """
        try:
            self._setting_put_usecase.execute(setting)
            return (True, None)
        except Exception as e:
            return (False, str(e))

    def on_close_requested(self) -> bool:
        """
        ダイアログが閉じられようとしたとき
        戻り値: 閉じることを許可するか（True=許可、False=拒否）
        """
        # バリデーション（Handlerの責務）
        validation_errors = [
            self._view.get_compiler_tool_path_validation_error(),
            self._view.get_compile_timeout_validation_error(),
            self._view.get_max_workers_validation_error(),
        ]
        errors = [e for e in validation_errors if e is not None]
        
        if errors:
            # バリデーション失敗：ユーザーに確認
            from PyQt5.QtWidgets import QMessageBox
            error_text = "\n".join(errors)
            res = QMessageBox.warning(
                self._view.get_parent_widget(),  # type: ignore
                "設定",
                f"設定内容にエラーがあります。\n\n{error_text}\n\n設定内容を破棄して終了しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if res == QMessageBox.No:
                return False  # 閉じることを拒否

        # バリデーション成功：Viewから個別フィールド値を取得してSettingオブジェクトを構築（Handlerの責務）
        setting = Setting(
            compiler_tool_fullpath=self._view.get_compiler_tool_fullpath(),
            compile_timeout=self._view.get_compile_timeout(),
            max_workers=self._view.get_max_workers(),
            backup_before_export=self._view.get_backup_before_export(),
            show_editing_symbols_in_stream_content=self._view.get_show_editing_symbols_in_stream_content(),
            show_editing_symbols_in_source_code=self._view.get_show_editing_symbols_in_source_code(),
            enable_line_wrap_in_stream_content=self._view.get_enable_line_wrap_in_stream_content(),
            enable_line_wrap_in_source_code=self._view.get_enable_line_wrap_in_source_code(),
        )
        
        success, error_message = self.on_save_requested(setting)
        if not success:
            # 保存失敗
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self._view.get_parent_widget(),  # type: ignore
                "設定",
                f"設定の保存に失敗しました。\n\n{error_message}",
            )
            return False  # 閉じることを拒否

        return True  # 閉じることを許可
