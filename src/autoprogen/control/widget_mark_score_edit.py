from PyQt5.QtCore import pyqtSignal, QObject, QRegExp, Qt, QEvent, pyqtSlot
from PyQt5.QtGui import QKeyEvent, QRegExpValidator
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QLabel

from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.res.font import get_font


class MarkScoreEditWidget(QWidget):
    key_pressed = pyqtSignal(QKeyEvent, name="key_pressed")
    confirmation_changed = pyqtSignal(bool, name="confirmation_changed")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._student_id: StudentID | None = None
        self._confirmed = False
        self._is_modified = False

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._le_score = QLineEdit(self)
        self._le_score.setValidator(QRegExpValidator(QRegExp("[1-9][0-9]|[0-9]|")))
        self._le_score.setFont(get_font(monospace=True, very_large=True, bold=True))
        self._le_score.setPlaceholderText("--")
        self._le_score.setFixedWidth(50)
        self._le_score.setFixedHeight(50)
        self._le_score.setEnabled(False)
        self._le_score.installEventFilter(self)
        layout.addWidget(self._le_score)

        layout_right = QVBoxLayout()
        layout.addLayout(layout_right)

        self._b_unmark = QPushButton(self)
        self._b_unmark.setText("×")
        self._b_unmark.setFixedWidth(25)
        self._b_unmark.setFixedHeight(25)
        self._b_unmark.setEnabled(False)
        self._b_unmark.setFocusPolicy(Qt.NoFocus)
        layout_right.addWidget(self._b_unmark)

        # noinspection PyArgumentList
        l_unit = QLabel(self)
        l_unit.setText("点")
        layout_right.addWidget(l_unit)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._b_unmark.clicked.connect(self.__b_unmark_clicked)
        # noinspection PyUnresolvedReferences
        self._le_score.textChanged.connect(self.__le_score_text_changed)

    def eventFilter(self, target: QObject, evt: QEvent):
        if evt.type() == QEvent.KeyPress:
            # noinspection PyUnresolvedReferences
            self.key_pressed.emit(evt)
            return False
        return False

    def set_data(self, student_mark: StudentMark | None) -> None:
        """採点結果を入力欄と確定状態の表示へ反映する。"""
        previous_blocked = self._le_score.blockSignals(True)
        try:
            if student_mark is None:
                self._le_score.setText("")
                self._le_score.setEnabled(False)
                self._b_unmark.setEnabled(False)
                self._student_id = None
                self._confirmed = False
            else:
                if student_mark.marked:
                    self._le_score.setText(str(student_mark.score))
                else:
                    self._le_score.setText("")
                self._le_score.setEnabled(True)
                self._b_unmark.setEnabled(True)
                self._student_id = student_mark.student_id
                self._confirmed = student_mark.confirmed
        finally:
            self._le_score.blockSignals(previous_blocked)

        self._is_modified = False
        self._update_confirmation_display()
        self.confirmation_changed.emit(self._confirmed)

    def _update_confirmation_display(self) -> None:
        """確定済みの場合だけ点数入力欄を緑色で表示する。"""
        if self._confirmed:
            self._le_score.setStyleSheet(
                "QLineEdit { background-color: #dffe8b; }"
            )
        else:
            self._le_score.setStyleSheet("")

    def set_unmarked(self) -> None:
        if self._student_id is None:
            return
        self._le_score.setText("")

    def is_modified(self) -> bool:
        return self._is_modified

    def get_data(self) -> StudentMark | None:
        if self._student_id is None:
            return None
        try:
            score_int = int(self._le_score.text())
        except ValueError:
            return StudentMark(
                student_id=self._student_id,
                score=None,
                confirmed=False,
            )
        else:
            return StudentMark(
                student_id=self._student_id,
                score=score_int,
                confirmed=self._confirmed,
            )

    @pyqtSlot()
    def __b_unmark_clicked(self):
        self._le_score.setText("")

    @pyqtSlot()
    def __le_score_text_changed(self):
        confirmation_changed = False
        if not self._le_score.text():
            confirmation_changed = self._confirmed
            self._confirmed = False
        if confirmation_changed:
            self._update_confirmation_display()
            self.confirmation_changed.emit(False)
        self._is_modified = True
