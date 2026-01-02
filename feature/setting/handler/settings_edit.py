import copy
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from feature.setting.handler.interface import (
    ISettingEditHandler,
    ISettingEditView,
    SettingEditDTO,
    SettingEditValidationError,
    PathNotAbsoluteError,
    PathNotExistsError,
)
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
        self._initial_dto: SettingEditDTO | None = None  # 初期DTOを保存

    def set_view(self, view: ISettingEditView) -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        self._view = view

    # ===== ISettingEditHandler実装 =====
    def on_view_initialized(self) -> None:
        """View初期化時に呼ばれる"""
        # 設定を読み込んでViewに設定
        setting = self._setting_get_usecase.execute()
        dto = self._setting_to_dto(setting)
        self._initial_dto = copy.deepcopy(dto)  # 初期DTOを保存
        self._view.set_settings(dto)

    def on_compiler_test_requested(self, compiler_tool_fullpath: Path) -> None:
        """コンパイルテストが要求されたとき"""
        def task(progress_callback: Callable[[str], None]):
            # progress_callbackは受け取るが使用しない（UseCaseが進捗を返さないため）
            _ = progress_callback
            return self._test_compile_stage_usecase.execute(compiler_tool_fullpath)
        
        result = self._navigator.run_blocking_task(
            parent=self._view.get_parent_widget(),
            title="コンパイルテスト",
            initial_message="コンパイルテストを実行しています...",
            task_func=task,
        )
        self._view.show_test_result(result)

    def on_compiler_search_requested(self) -> None:
        """コンパイラ自動検索が要求されたとき"""
        # Navigator経由でダイアログを開く
        result = self._navigator.open_compiler_search_dialog(
            self._view.get_parent_widget()
        )
        if result is not None:
            self._view.set_compiler_tool_fullpath(result)

    def on_save_requested(self, setting: Setting) -> None:
        """
        保存が要求されたとき
        """
        self._setting_put_usecase.execute(setting)

    def on_save_button_clicked(self) -> bool:
        """
        保存ボタンがクリックされたとき
        戻り値: 閉じることを許可するか（True=許可、False=拒否）
        """
        # DTOを取得
        dto = self._view.get_settings_dto()
        
        # バリデーション（Handlerの責務）
        try:
            self.validate_dto(dto)
        except SettingEditValidationError as e:
            # バリデーション失敗：Viewにエラー表示を依頼
            error_message = str(e) if str(e) else e.__class__.__name__
            self._view.show_validation_error(error_message)
            return False  # 閉じることを拒否

        # バリデーション成功：DTOをSettingに変換して保存
        setting = self._dto_to_setting(dto)
        self.on_save_requested(setting)

        return True  # 閉じることを許可

    def on_cancel_requested(self) -> bool:
        """
        キャンセルボタンがクリックされたとき
        戻り値: 閉じることを許可するか（True=許可、False=拒否）
        """
        # 変更があるか確認
        if not self._has_changes():
            # 変更なし：そのまま閉じる
            return True
        
        # 変更あり：Viewに確認を依頼
        if not self._view.confirm_discard_changes():
            return False  # 閉じることを拒否
        
        return True  # 閉じることを許可

    def on_close_requested(self) -> bool:
        """
        ダイアログが閉じられようとしたとき（×ボタン）
        戻り値: 閉じることを許可するか（True=許可、False=拒否）
        """
        # キャンセルと同じ処理
        return self.on_cancel_requested()

    # ===== 内部メソッド =====
    
    def _setting_to_dto(self, setting: Setting) -> SettingEditDTO:
        """SettingをDTOに変換"""
        return SettingEditDTO(
            compiler_tool_fullpath=str(setting.compiler_tool_fullpath) if setting.compiler_tool_fullpath else None,
            compile_timeout=setting.compile_timeout,
            max_workers=setting.max_workers,
            backup_before_export=setting.backup_before_export,
            show_editing_symbols_in_stream_content=setting.show_editing_symbols_in_stream_content,
            show_editing_symbols_in_source_code=setting.show_editing_symbols_in_source_code,
            enable_line_wrap_in_stream_content=setting.enable_line_wrap_in_stream_content,
            enable_line_wrap_in_source_code=setting.enable_line_wrap_in_source_code,
        )
    
    def _dto_to_setting(self, dto: SettingEditDTO) -> Setting:
        """DTOをSettingに変換"""
        return Setting(
            compiler_tool_fullpath=Path(dto.compiler_tool_fullpath) if dto.compiler_tool_fullpath else None,
            compile_timeout=dto.compile_timeout,
            max_workers=dto.max_workers,
            backup_before_export=dto.backup_before_export,
            show_editing_symbols_in_stream_content=dto.show_editing_symbols_in_stream_content,
            show_editing_symbols_in_source_code=dto.show_editing_symbols_in_source_code,
            enable_line_wrap_in_stream_content=dto.enable_line_wrap_in_stream_content,
            enable_line_wrap_in_source_code=dto.enable_line_wrap_in_source_code,
        )
    
    def validate_dto(self, dto: SettingEditDTO) -> None:
        """
        DTOのバリデーション（Handlerの責務）
        バリデーションに失敗した場合はSettingEditValidationErrorのサブクラスを投げる
        """
        # コンパイラツールパスのチェック
        if dto.compiler_tool_fullpath:
            path = Path(dto.compiler_tool_fullpath)
            
            # 絶対パスかどうかをチェック
            if not path.is_absolute():
                raise PathNotAbsoluteError("パスは絶対パスである必要があります。")
            
            # 存在するかどうかをチェック
            if not path.exists():
                raise PathNotExistsError("指定されたパスが存在しません。")
        
        # compile_timeoutとmax_workersのバリデーションは現在エラーなし
        # （Widgetの範囲チェックで防がれているため）
    
    def _has_changes(self) -> bool:
        """変更があるかどうかを判定（Handlerの責務）"""
        if self._initial_dto is None:
            return False  # 初期値が設定されていない場合は変更なしとみなす
        
        current_dto = self._view.get_settings_dto()
        return current_dto != self._initial_dto
