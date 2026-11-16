from PyQt5.QtCore import QObject, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QAction, QToolButton, QVBoxLayout, QWidget

from autoprogen.res.icon import get_icon


class StudentTableControlWidget(QWidget):
    """学生テーブルで選択した学生に対する操作を提供する。"""

    open_folder_requested = pyqtSignal(name="open_folder_requested")
    open_scoring_requested = pyqtSignal(name="open_scoring_requested")
    clear_mark_requested = pyqtSignal(name="clear_mark_requested")

    def __init__(self, parent: QObject = None) -> None:
        """操作用Actionと縦並びのボタンを構築する。"""
        super().__init__(parent)

        self._open_folder_action = QAction(
            get_icon("folder"),
            "展開された提出ファイルを編集",
            self,
        )
        self._open_folder_action.setObjectName("open-student-folder")
        self._open_folder_action.setToolTip(
            "選択した学生の展開済み提出ファイルを編集します"
        )

        self._open_scoring_action = QAction(
            get_icon("marker"),
            "採点画面を開く",
            self,
        )
        self._open_scoring_action.setObjectName("open-student-scoring")
        self._open_scoring_action.setToolTip("選択した学生の採点画面を開きます")

        self._clear_mark_action = QAction(
            get_icon("trash"),
            "点数をクリア",
            self,
        )
        self._clear_mark_action.setObjectName("clear-student-mark")
        self._clear_mark_action.setToolTip(
            "選択した学生の点数をクリアして未確定にします"
        )

        self._init_ui()
        self._init_signals()
        self.set_selection_state(
            selected=False,
            marked=False,
            has_submission=False,
        )

    def _init_ui(self) -> None:
        """Actionを共有するボタンを縦に配置する。"""
        layout = QVBoxLayout(self)

        for action in self.context_actions():
            button = QToolButton(self)
            button.setDefaultAction(action)
            button.setToolButtonStyle(Qt.ToolButtonIconOnly)
            button.setIconSize(QSize(20, 20))
            button.setFixedSize(30, 30)
            layout.addWidget(button)

        layout.addStretch(1)

    def _init_signals(self) -> None:
        """各Actionを外部向けの操作要求へ接続する。"""
        self._open_folder_action.triggered.connect(
            self._on_open_folder_triggered
        )
        self._open_scoring_action.triggered.connect(
            self._on_open_scoring_triggered
        )
        self._clear_mark_action.triggered.connect(
            self._on_clear_mark_triggered
        )

    def context_actions(self) -> tuple[QAction, ...]:
        """ボタンとコンテキストメニューで共有するActionを返す。"""
        return (
            self._open_folder_action,
            self._open_scoring_action,
            self._clear_mark_action,
        )

    def set_selection_state(
            self,
            *,
            selected: bool,
            marked: bool,
            has_submission: bool,
    ) -> None:
        """学生の選択・採点・提出状態に応じて操作可否を更新する。"""
        self._open_folder_action.setEnabled(selected and has_submission)
        self._open_scoring_action.setEnabled(selected)
        self._clear_mark_action.setEnabled(selected and marked)

    @pyqtSlot(bool)
    def _on_open_folder_triggered(self, _: bool = False) -> None:
        """展開済み提出ファイルの編集要求を通知する。"""
        self.open_folder_requested.emit()

    @pyqtSlot(bool)
    def _on_open_scoring_triggered(self, _: bool = False) -> None:
        """採点画面を開く要求を通知する。"""
        self.open_scoring_requested.emit()

    @pyqtSlot(bool)
    def _on_clear_mark_triggered(self, _: bool = False) -> None:
        """点数をクリアする要求を通知する。"""
        self.clear_mark_requested.emit()
