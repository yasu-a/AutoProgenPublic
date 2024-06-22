from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QCheckBox, QWidget, QHBoxLayout, QSpinBox

from models.testcase import TestCaseConfig


class TestCaseConfigEditWidget(QFrame):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setFrameStyle(QFrame.Panel | QFrame.Plain)

        layout = QGridLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("【出力をあいまいに比較するためのオプション】", self), 0, 0)

        w_field = QCheckBox("行頭のスペースを無視", self)
        self.cb_allow_spaces_start_of_line = w_field
        layout.addWidget(w_field, 1, 0)

        w_field = QCheckBox("行末のスペースを無視", self)
        self.cb_allow_spaces_end_of_line = w_field
        layout.addWidget(w_field, 2, 0)

        w_field = QCheckBox("単語間の複数のスペースを1つのスペースとして扱う", self)
        self.cb_allow_multiple_spaces_between_words = w_field
        layout.addWidget(w_field, 3, 0)

        w_field = QCheckBox("空行を無視", self)
        self.cb_allow_empty_lines = w_field
        layout.addWidget(w_field, 1, 1)

        w_field = QCheckBox("大文字と小文字を区別しない", self)
        self.cb_allow_letter_case_difference = w_field
        layout.addWidget(w_field, 2, 1)

        w_field = QWidget()
        layout.addWidget(w_field, 4, 0)
        w_field.setLayout(QHBoxLayout())
        w_field.layout().setContentsMargins(0, 0, 0, 0)
        w_field.layout().setSpacing(3)
        w_field.layout().addWidget(
            QLabel("各行の最大編集距離（0で完全一致）", self)
        )
        sp = QSpinBox(self)
        sp.setRange(0, 10)
        self.spin_allowable_line_levenshtein_distance = sp
        w_field.layout().addWidget(sp)

        w_field = QWidget()
        layout.addWidget(w_field, 4, 1)
        w_field.setLayout(QHBoxLayout())
        w_field.layout().setContentsMargins(0, 0, 0, 0)
        w_field.layout().setSpacing(3)
        w_field.layout().addWidget(
            QLabel("実行時間のタイムアウト", self)
        )
        sp = QSpinBox(self)
        sp.setRange(0, 20 * 1000)
        sp.setSingleStep(500)
        self.spin_timeout_millis = sp
        w_field.layout().addWidget(sp)
        w_field.layout().addWidget(
            QLabel("ミリ秒", self)
        )

    def set_fields_with_testcase_config(self, config: TestCaseConfig):
        self.cb_allow_spaces_start_of_line \
            .setChecked(config.allow_spaces_start_of_line)
        self.cb_allow_spaces_end_of_line \
            .setChecked(config.allow_spaces_end_of_line)
        self.cb_allow_multiple_spaces_between_words \
            .setChecked(config.allow_multiple_spaces_between_words)
        self.cb_allow_empty_lines \
            .setChecked(config.allow_empty_lines)
        self.cb_allow_letter_case_difference \
            .setChecked(config.allow_letter_case_difference)
        self.spin_allowable_line_levenshtein_distance \
            .setValue(config.allowable_line_levenshtein_distance)
        self.spin_timeout_millis \
            .setValue(int(config.timeout * 1000))

    def get_testcase_config_from_fields(self) -> TestCaseConfig:
        config = TestCaseConfig.create_empty()
        config.allow_spaces_start_of_line \
            = self.cb_allow_spaces_start_of_line.isChecked()
        config.allow_spaces_end_of_line \
            = self.cb_allow_spaces_end_of_line.isChecked()
        config.allow_multiple_spaces_between_words \
            = self.cb_allow_multiple_spaces_between_words.isChecked()
        config.allow_empty_lines \
            = self.cb_allow_empty_lines.isChecked()
        config.allow_letter_case_difference \
            = self.cb_allow_letter_case_difference.isChecked()
        config.allowable_line_levenshtein_distance \
            = self.spin_allowable_line_levenshtein_distance.value()
        config.timeout \
            = self.spin_timeout_millis.value() / 1000
        return config
