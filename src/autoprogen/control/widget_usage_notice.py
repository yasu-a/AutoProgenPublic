from collections.abc import Sequence

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from autoprogen.res.font import get_font


USAGE_NOTICE_ITEMS: tuple[str, ...] = (
    "AutoProgenの実行結果やテスト結果だけで点数を決定せず、最終的な採点は自分で確認します。",
    "AutoProgenでコンパイルに失敗した場合は、環境の違いを考慮し、必要に応じてVisual Studioでも確認します。",
    "提出物のファイル名の重複や構成の誤りによって処理に失敗した場合は、自動的に0点とせず、提出内容を確認して必要な修正と再実行を行います。",
    "学生のプログラムを実行するPCに危険が及ぶ可能性があり、特に安全性チェックを無効にする操作にはリスクがあることを理解しています。",
)


class UsageNoticeChecklistWidget(QWidget):
    """使用上の注意事項を確認するチェックボックス一覧を表示する。"""

    confirmation_changed = pyqtSignal(bool, name="confirmation_changed")

    def __init__(
            self,
            parent: QWidget | None = None,
            *,
            notice_items: Sequence[str],
    ) -> None:
        """確認項目を受け取り、チェックボックス一覧を構築する。"""
        super().__init__(parent)
        self._notice_items = tuple(notice_items)
        self._confirmation_checkboxes: list[QCheckBox] = []

        self._init_ui()
        self._init_signals()

    def _init_ui(self) -> None:
        """確認項目を左余白付きで縦に配置する。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        for notice_item in self._notice_items:
            checkbox = QCheckBox(notice_item, self)
            checkbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self._confirmation_checkboxes.append(checkbox)
            layout.addWidget(checkbox)

    def _init_signals(self) -> None:
        """各確認欄の変更を一覧全体の確認状態として通知する。"""
        for checkbox in self._confirmation_checkboxes:
            checkbox.toggled.connect(self._emit_confirmation_changed)

    def _emit_confirmation_changed(self) -> None:
        """現在の全項目確認状態を通知する。"""
        self.confirmation_changed.emit(self.is_confirmed())

    def is_confirmed(self) -> bool:
        """すべての注意事項が確認されている場合にTrueを返す。"""
        return bool(self._confirmation_checkboxes) and all(
            checkbox.isChecked()
            for checkbox in self._confirmation_checkboxes
        )


class UsageNoticeWidget(QWidget):
    """プロジェクトを開く前に確認する使用上の注意事項を表示する。"""

    confirmation_changed = pyqtSignal(bool, name="confirmation_changed")

    def __init__(
            self,
            parent: QWidget | None = None,
            *,
            app_version_text: str,
            notice_items: Sequence[str] = USAGE_NOTICE_ITEMS,
    ) -> None:
        """対象バージョンと確認項目を受け取り、確認用Widgetを構築する。"""
        super().__init__(parent)
        self._app_version_text = app_version_text
        self._notice_items = tuple(notice_items)

        self._init_ui()
        self._init_signals()

    def _init_ui(self) -> None:
        """見出し、注意事項、確認欄を上から順に配置する。"""
        layout_root = QVBoxLayout(self)
        layout_root.setContentsMargins(8, 8, 8, 8)
        layout_root.setSpacing(10)

        layout_header = QHBoxLayout()
        layout_root.addLayout(layout_header)

        label_title = QLabel("使用上の注意事項", self)
        label_title.setFont(get_font(bold=True))
        layout_header.addWidget(label_title)
        layout_header.addStretch(1)

        label_version = QLabel(self._app_version_text, self)
        label_version.setFont(get_font(small=True))
        layout_header.addWidget(label_version)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout_root.addWidget(separator)

        label_introduction = QLabel(
            "プロジェクトを開く前に、以下の事項を確認してください。",
            self,
        )
        label_introduction.setWordWrap(True)
        layout_root.addWidget(label_introduction)

        self._checklist_widget = UsageNoticeChecklistWidget(
            self,
            notice_items=self._notice_items,
        )
        layout_root.addWidget(self._checklist_widget)

    def _init_signals(self) -> None:
        """チェックリストの確認状態をWidget全体の状態として通知する。"""
        self._checklist_widget.confirmation_changed.connect(
            self.confirmation_changed.emit,
        )

    def is_confirmed(self) -> bool:
        """すべての注意事項が確認されている場合にTrueを返す。"""
        return self._checklist_widget.is_confirmed()
