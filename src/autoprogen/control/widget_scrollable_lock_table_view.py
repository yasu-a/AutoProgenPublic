"""スクロールを維持しながら入力操作を制限できるテーブルビュー。"""

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QAbstractItemView, QTableView


class ScrollableLockTableView(QTableView):
    """セルとヘッダーの入力を制限し、スクロールと表示更新を維持する。"""

    _BLOCKED_POINTER_EVENTS = frozenset({
        QEvent.MouseButtonPress,
        QEvent.MouseButtonRelease,
        QEvent.MouseButtonDblClick,
        QEvent.MouseMove,
        QEvent.ContextMenu,
        QEvent.DragEnter,
        QEvent.DragMove,
        QEvent.DragLeave,
        QEvent.Drop,
        QEvent.TouchBegin,
        QEvent.TouchUpdate,
        QEvent.TouchEnd,
        QEvent.TouchCancel,
    })
    _BLOCKED_KEY_EVENTS = frozenset({
        QEvent.KeyPress,
        QEvent.KeyRelease,
        QEvent.ShortcutOverride,
    })

    def __init__(self, parent=None) -> None:
        """初期状態を操作可能とし、ヘッダーの入力監視を設定する。"""
        super().__init__(parent)
        self._interaction_enabled = True
        self._saved_edit_triggers = None
        self._saved_selection_mode = None
        self._saved_focus_policy = None
        self._saved_viewport_palette = None

        for header in (self.horizontalHeader(), self.verticalHeader()):
            header.installEventFilter(self)
            header.viewport().installEventFilter(self)

    def is_interaction_enabled(self) -> bool:
        """ユーザーによるテーブル操作が有効かを返す。"""
        return self._interaction_enabled

    def set_interaction_enabled(self, enabled: bool) -> None:
        """スクロールを維持したままセル・ヘッダー操作を切り替える。"""
        enabled = bool(enabled)
        if self._interaction_enabled == enabled:
            return

        if not enabled:
            # 元の設定を保持し、操作禁止中の編集・選択・フォーカスを抑える。
            self._saved_edit_triggers = self.editTriggers()
            self._saved_selection_mode = self.selectionMode()
            self._saved_focus_policy = self.focusPolicy()
            self._saved_viewport_palette = self.viewport().palette()
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.setSelectionMode(QAbstractItemView.NoSelection)
            self.setFocusPolicy(Qt.NoFocus)
            self.viewport().unsetCursor()

            # 無効化せず、操作禁止中であることだけを背景色で示す。
            locked_palette = QPalette(self._saved_viewport_palette)
            locked_palette.setColor(QPalette.Base, QColor(240, 240, 240))
            locked_palette.setColor(QPalette.AlternateBase, QColor(232, 232, 232))
            locked_palette.setColor(QPalette.Highlight, QColor(224, 224, 224))
            locked_palette.setColor(QPalette.HighlightedText, QColor(64, 64, 64))
            self.viewport().setPalette(locked_palette)
        else:
            # 連続切替でも最初に保存した設定に戻す。
            if self._saved_edit_triggers is not None:
                self.setEditTriggers(self._saved_edit_triggers)
            if self._saved_selection_mode is not None:
                self.setSelectionMode(self._saved_selection_mode)
            if self._saved_focus_policy is not None:
                self.setFocusPolicy(self._saved_focus_policy)
            if self._saved_viewport_palette is not None:
                self.viewport().setPalette(self._saved_viewport_palette)
            self._saved_edit_triggers = None
            self._saved_selection_mode = None
            self._saved_focus_policy = None
            self._saved_viewport_palette = None

        self._interaction_enabled = enabled

    def viewportEvent(self, event) -> bool:
        """セルへのポインター入力だけを破棄し、ホイールを通す。"""
        if (
            not self._interaction_enabled
            and event.type() in self._BLOCKED_POINTER_EVENTS
        ):
            event.accept()
            return True
        return super().viewportEvent(event)

    def eventFilter(self, watched, event) -> bool:
        """ヘッダーの入力操作を破棄し、表示処理は通す。"""
        if not self._interaction_enabled:
            headers = (self.horizontalHeader(), self.verticalHeader())
            for header in headers:
                if watched is header or watched is header.viewport():
                    if event.type() in (
                        self._BLOCKED_POINTER_EVENTS | self._BLOCKED_KEY_EVENTS
                    ):
                        event.accept()
                        return True
                    break
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        """操作禁止中のキー入力を破棄する。"""
        if not self._interaction_enabled:
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        """操作禁止中のキー解放イベントを破棄する。"""
        if not self._interaction_enabled:
            event.accept()
            return
        super().keyReleaseEvent(event)
