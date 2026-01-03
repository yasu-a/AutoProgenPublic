from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog

from shared.view.style.icon import get_icon


class CompilerToolPathEditWidget(QWidget):
    compile_test_requested = pyqtSignal(Path, name="compile_test_requested")
    auto_search_requested = pyqtSignal(name="auto_search_requested")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._le_path = QLineEdit(self)
        self._le_path.setReadOnly(True)
        layout.addWidget(self._le_path)

        self._b_open = QPushButton(self)
        self._b_open.setIcon(get_icon("folder"))
        layout.addWidget(self._b_open)

        self._b_search = QPushButton(self)
        self._b_search.setText("自動検索")
        layout.addWidget(self._b_search)

        self._b_test = QPushButton(self)
        self._b_test.setText("テスト")
        layout.addWidget(self._b_test)

        # シグナル接続
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
        """パスの形式が正しいかチェック（形式チェックのみ）"""
        path_str = self._le_path.text()
        if not path_str:
            return None
        try:
            # Pathとして有効かどうかをチェック
            Path(path_str)
        except (ValueError, OSError):
            return "パスの形式が正しくありません。"
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
        """自動検索ボタンがクリックされたとき → シグナルを発火"""
        # noinspection PyUnresolvedReferences
        self.auto_search_requested.emit()

    @pyqtSlot()
    def __b_test_clicked(self):
        path = self.get_value()
        if path:
            # noinspection PyUnresolvedReferences
            self.compile_test_requested.emit(path)
