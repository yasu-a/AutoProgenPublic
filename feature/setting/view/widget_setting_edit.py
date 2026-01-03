from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QCheckBox, QMessageBox

from feature.setting.handler.interface import ISettingEditHandler, ISettingEditView, SettingEditDTO
from feature.setting.view.widget_compiler_timeout import CompilerTimeoutWidget
from feature.setting.view.widget_compiler_tool_path_edit import CompilerToolPathEditWidget
from feature.setting.view.widget_max_workers import MaxWorkersWidget


class SettingEditWidget(QWidget, ISettingEditView):
    def __init__(
            self,
            parent: QObject = None,
    ):
        super().__init__(parent)
        self._handler: ISettingEditHandler

        self._init_ui()

    def set_handler(self, handler: ISettingEditHandler) -> None:
        """Handlerを注入（DI）"""
        # noinspection PyAttributeOutsideInit
        self._handler = handler

    def _init_ui(self):
        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        layout_content = QGridLayout()
        layout_root.addLayout(layout_content)

        i = 0

        def add_item(title: str | None, widget: QWidget):
            nonlocal i
            if title is not None:
                label = QLabel(title, self)
                font = label.font()
                font.setBold(True)
                label.setFont(font)
                layout_content.addWidget(label, i, 0)
                i += 1
            layout_content.addWidget(widget, i, 0)
            i += 1

        # Setting::compiler_tool_fullpath: Path | None
        # noinspection PyTypeChecker
        self._w_compiler_tool_path = CompilerToolPathEditWidget(self)
        add_item(
            title="Visual Studio開発者ツールのパス",
            widget=self._w_compiler_tool_path,
        )

        # Setting::compiler_timeout: float
        # noinspection PyTypeChecker
        self._w_compiler_timeout = CompilerTimeoutWidget(self)
        add_item(
            title="コンパイルのタイムアウト",
            widget=self._w_compiler_timeout,
        )

        # Setting::max_workers: int
        # noinspection PyTypeChecker
        self._w_max_workers = MaxWorkersWidget(self)
        add_item(
            title="並列タスク実行数（反映するには再起動が必要です）",
            widget=self._w_max_workers,
        )

        # Setting::backup_before_export: bool
        self._w_backup_before_export = QCheckBox(
            "成績記録用のExcelに点数をエクスポートする前に同じフォルダにコピーをとる",
            self,
        )
        add_item(
            title="成績記録用Excelのバックアップ",
            widget=self._w_backup_before_export,
        )

        # Setting::show_editing_symbols_in_stream_content: bool
        self._w_show_editing_symbols_in_stream_content = QCheckBox(
            "ストリームの内容を表示するときに編集記号を表示する",
            self,
        )
        add_item(
            title="編集記号の表示",
            widget=self._w_show_editing_symbols_in_stream_content,
        )

        # Setting::show_editing_symbols_in_source_code: bool
        self._w_show_editing_symbols_in_source_code = QCheckBox(
            "ソースコードを表示するときに編集記号を表示する",
            self,
        )
        add_item(
            title=None,
            widget=self._w_show_editing_symbols_in_source_code,
        )

        # Setting::enable_line_wrap_in_stream_content: bool
        self._w_enable_line_wrap_in_stream_content = QCheckBox(
            "ストリームの内容の長い行を折り返す",
            self,
        )
        add_item(
            title="行折り返しの設定",
            widget=self._w_enable_line_wrap_in_stream_content,
        )

        # Setting::enable_line_wrap_in_source_code: bool
        self._w_enable_line_wrap_in_source_code = QCheckBox(
            "ソースコードの長い行を折り返す",
            self,
        )
        add_item(
            title=None,
            widget=self._w_enable_line_wrap_in_source_code,
        )

        layout_root.addStretch(1)

        # シグナル接続
        self._w_compiler_tool_path.compile_test_requested.connect(
            self.__w_compiler_tool_path_compile_test_requested,
        )
        self._w_compiler_tool_path.auto_search_requested.connect(
            self.__w_compiler_tool_path_auto_search_requested,
        )

    @pyqtSlot(Path)
    def __w_compiler_tool_path_compile_test_requested(self, compiler_tool_fullpath: Path):
        """コンパイルテストが要求されたとき → Handlerに通知"""
        self._handler.on_compiler_test_requested(compiler_tool_fullpath)

    @pyqtSlot()
    def __w_compiler_tool_path_auto_search_requested(self):
        """自動検索が要求されたとき → Handlerに通知"""
        self._handler.on_compiler_search_requested()

    # ===== ISettingEditView実装 =====
    def set_settings(self, dto: SettingEditDTO) -> None:
        """設定をViewに設定"""
        from pathlib import Path
        
        self._w_compiler_tool_path.set_value(
            Path(dto.compiler_tool_fullpath) if dto.compiler_tool_fullpath else None,
        )
        self._w_compiler_timeout.set_value(int(dto.compile_timeout))
        self._w_max_workers.set_value(dto.max_workers)
        self._w_backup_before_export.setChecked(dto.backup_before_export)
        self._w_show_editing_symbols_in_stream_content.setChecked(
            dto.show_editing_symbols_in_stream_content
        )
        self._w_show_editing_symbols_in_source_code.setChecked(
            dto.show_editing_symbols_in_source_code
        )
        self._w_enable_line_wrap_in_stream_content.setChecked(
            dto.enable_line_wrap_in_stream_content
        )
        self._w_enable_line_wrap_in_source_code.setChecked(
            dto.enable_line_wrap_in_source_code
        )

    def get_settings_dto(self) -> SettingEditDTO:
        """Viewから設定を取得（DTO形式）"""
        compiler_tool_path_value = self._w_compiler_tool_path.get_value()
        compiler_tool_fullpath_str = str(compiler_tool_path_value) if compiler_tool_path_value else None
        
        return SettingEditDTO(
            compiler_tool_fullpath=compiler_tool_fullpath_str,
            compile_timeout=float(self._w_compiler_timeout.get_value()),
            max_workers=self._w_max_workers.get_value(),
            backup_before_export=self._w_backup_before_export.isChecked(),
            show_editing_symbols_in_stream_content=self._w_show_editing_symbols_in_stream_content.isChecked(),
            show_editing_symbols_in_source_code=self._w_show_editing_symbols_in_source_code.isChecked(),
            enable_line_wrap_in_stream_content=self._w_enable_line_wrap_in_stream_content.isChecked(),
            enable_line_wrap_in_source_code=self._w_enable_line_wrap_in_source_code.isChecked(),
        )

    def show_test_result(self, result) -> None:
        """コンパイルテスト結果を表示"""
        if result.is_success:
            QMessageBox.information(
                self,  # type: ignore
                "コンパイルテスト",
                f"コンパイルが終了しました。コンパイラは正しく動作しています。\n"
                f"\n"
                f"{result.output}",
            )
        else:
            QMessageBox.critical(
                self,  # type: ignore
                "コンパイルテスト",
                f"{result.output}",
            )

    def set_compiler_tool_fullpath(self, path: Path | None) -> None:
        """コンパイラツールのパスを設定"""
        self._w_compiler_tool_path.set_value(path)

    def get_parent_widget(self):
        """親ウィジェットを取得（QMessageBoxのparent用）"""
        return self

    def show_validation_error(self, error_message: str) -> None:
        """バリデーションエラーを表示"""
        QMessageBox.warning(
            self,  # type: ignore
            "設定",
            f"設定内容にエラーがあります。\n\n{error_message}",
        )

    def confirm_discard_changes(self) -> bool:
        """
        変更内容を破棄するか確認
        戻り値: 破棄するか（True=破棄、False=キャンセル）
        """
        res = QMessageBox.question(
            self,  # type: ignore
            "設定",
            "変更内容が破棄されます。よろしいですか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return res == QMessageBox.Yes
