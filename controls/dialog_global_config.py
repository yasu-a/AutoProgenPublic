from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import *

from application.dependency.usecases import get_global_config_get_usecase, \
    get_global_config_put_usecase, get_compile_test_run_usecase
from controls.dialog_compiler_search import CompilerSearchDialog
from controls.res.icons import icon
from domain.models.global_config import GlobalConfig
from infra.external.compiler_location import is_compiler_location
from utils.app_logging import create_logger


class CompilerToolPathEditWidget(QWidget):
    compile_test_requested = pyqtSignal(Path, name="compile_test_requested")

    # Pathはテストしたいコンパイルツールのパス

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._le_path = QLineEdit(self)
        self._le_path.setReadOnly(True)
        layout.addWidget(self._le_path)

        self._b_open = QPushButton(self)
        self._b_open.setIcon(icon("open"))
        layout.addWidget(self._b_open)

        self._b_search = QPushButton(self)
        self._b_search.setText("自動検索")
        layout.addWidget(self._b_search)

        self._b_test = QPushButton(self)
        self._b_test.setText("テスト")
        layout.addWidget(self._b_test)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._b_open.clicked.connect(self.__b_open_clicked)
        # noinspection PyUnresolvedReferences
        self._b_search.clicked.connect(self.__b_search_clicked)
        # noinspection PyUnresolvedReferences
        self._b_test.clicked.connect(self.__b_test_clicked)

    def set_value(self, path: Path | None) -> None:
        self._le_path.setText(str(path) if path else "")

    def get_value(self) -> Path | None:
        return Path(self._le_path.text()) if self._le_path.text() else None

    def validate_and_get_reason(self) -> str | None:
        path = self._le_path.text()
        path = Path(path)
        if not is_compiler_location(path):
            return "VsDevCmd.batへのパスを指定して下さい。通常はVisual Studioのインストールフォルダ内にあります。"
        else:
            return None

    @pyqtSlot()
    def __b_open_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,  # type: ignore
            "VsDevCmd.batを開く",
            filter="VsDevCmd.bat (*VsDevCmd.bat)",
        )
        filepath = filepath.strip()
        if not filepath:
            return
        filepath = Path(filepath)
        if not filepath.exists():
            return
        self._le_path.setText(str(filepath))

    @pyqtSlot()
    def __b_search_clicked(self):
        dialog_auto_find = CompilerSearchDialog(self)
        dialog_auto_find.exec_()
        if dialog_auto_find.get_value() is not None:
            self._le_path.setText(str(dialog_auto_find.get_value()))

    @pyqtSlot()
    def __b_test_clicked(self):
        self.compile_test_requested.emit(Path(self._le_path.text()))


class CompilerTimeoutWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._sb_value = QSpinBox(self)
        self._sb_value.setMinimum(1)
        self._sb_value.setMaximum(30)
        self._sb_value.setSingleStep(1)
        self._sb_value.setFixedWidth(100)
        layout.addWidget(self._sb_value)

        layout.addWidget(QLabel("秒", self))

        layout.addStretch(1)

    def _init_signals(self):
        pass

    def set_value(self, timeout: int) -> None:
        self._sb_value.setValue(timeout)

    def get_value(self) -> int:
        return self._sb_value.value()

    # noinspection PyMethodMayBeStatic
    def validate_and_get_reason(self) -> str | None:
        return None


class MaxWorkersWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._sb_value = QSpinBox(self)
        self._sb_value.setMinimum(1)
        self._sb_value.setMaximum(16)
        self._sb_value.setSingleStep(1)
        self._sb_value.setFixedWidth(100)
        layout.addWidget(self._sb_value)

        layout.addStretch(1)

    def _init_signals(self):
        pass

    def set_value(self, timeout: int) -> None:
        self._sb_value.setValue(timeout)

    def get_value(self) -> int:
        return self._sb_value.value()

    # noinspection PyMethodMayBeStatic
    def validate_and_get_reason(self) -> str | None:
        return None


class GlobalConfigEditWidget(QWidget):
    _logger = create_logger()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        layout_content = QGridLayout()
        layout_root.addLayout(layout_content)

        i = 0

        def add_item(title: str, widget: QWidget):
            nonlocal i
            label = QLabel(title, self)
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            layout_content.addWidget(label, i, 0)
            i += 1
            layout_content.addWidget(widget, i, 0)
            i += 1

        self._w_compiler_tool_path = CompilerToolPathEditWidget(self)
        add_item(
            "Visual Studio開発者ツールのパス",
            self._w_compiler_tool_path,
        )

        self._w_compiler_timeout = CompilerTimeoutWidget(self)
        add_item(
            "コンパイルのタイムアウト (秒)",
            self._w_compiler_timeout,
        )

        self._w_max_workers = MaxWorkersWidget(self)
        add_item(
            "並列タスク実行数（反映するには再起動が必要です）",
            self._w_max_workers,
        )

        self._w_backup_before_export = QCheckBox(
            "成績記録用のExcelに点数をエクスポートする前に同じフォルダにコピーをとる",
            self,
        )
        add_item(
            "成績記録用Excelのバックアップ",
            self._w_backup_before_export,
        )

        layout_root.addStretch(1)

    def _init_signals(self):
        self._w_compiler_tool_path.compile_test_requested.connect(
            self.__w_compiler_tool_path_compile_test_requested,
        )

    @pyqtSlot(Path)
    def __w_compiler_tool_path_compile_test_requested(self, compiler_tool_fullpath: Path):
        result = get_compile_test_run_usecase().execute(
            compiler_tool_fullpath=Path(compiler_tool_fullpath),
        )
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

    def set_value(self, settings: GlobalConfig) -> None:
        self._w_compiler_tool_path.set_value(settings.compiler_tool_fullpath)
        self._w_compiler_timeout.set_value(int(settings.compile_timeout))
        self._w_max_workers.set_value(settings.max_workers)
        self._w_backup_before_export.setChecked(settings.backup_before_export)

    def get_value(self) -> GlobalConfig:
        return GlobalConfig(
            compiler_tool_fullpath=self._w_compiler_tool_path.get_value(),
            compile_timeout=float(self._w_compiler_timeout.get_value()),
            max_workers=self._w_max_workers.get_value(),
            backup_before_export=self._w_backup_before_export.isChecked(),
        )

    # noinspection PyMethodMayBeStatic
    def validate_and_get_reason(self) -> str | None:
        validation_results = [
            self._w_compiler_tool_path.validate_and_get_reason(),
            self._w_compiler_timeout.validate_and_get_reason(),
            self._w_max_workers.validate_and_get_reason(),
        ]
        is_ok = all(validation_result is None for validation_result in validation_results)
        if is_ok:
            return None
        else:
            return "\n".join(filter(None, validation_results))


class GlobalConfigEditDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("設定")
        self.setModal(True)
        self.resize(700, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_settings_edit = GlobalConfigEditWidget(self)  # type: ignore
        self._w_settings_edit.set_value(get_global_config_get_usecase().execute())
        layout.addWidget(self._w_settings_edit)

    def _init_signals(self):
        pass

    # noinspection PyMethodOverriding
    def closeEvent(self, evt: QCloseEvent):
        reason = self._w_settings_edit.validate_and_get_reason()
        if reason is None:
            get_global_config_put_usecase().execute(self._w_settings_edit.get_value())
        else:
            # ユーザーにエラーを示して変更を破棄して閉じるか閉じずに編集するかを聞く
            res = QMessageBox.warning(
                self,  # type: ignore
                "設定",
                f"設定内容にエラーがあります。\n\n{reason}\n\n設定内容を破棄して終了しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if res == QMessageBox.No:
                evt.ignore()
            else:
                evt.accept()