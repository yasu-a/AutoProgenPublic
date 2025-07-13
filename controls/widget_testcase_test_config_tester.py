from PyQt5.QtCore import QObject, pyqtSignal, QEvent, Qt
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QGroupBox, QPlainTextEdit, QHBoxLayout, QPushButton

from application.dependency.usecases import get_test_test_stage_usecase
from controls.widget_horizontal_line import HorizontalLineWidget
from controls.widget_plain_text_edit import PlainTextEdit
from controls.widget_test_summary_indicator import TestCaseTestSummaryIndicatorWidget
from controls.widget_testcase_result_output_file_text_view import TestCaseResultOutputFileTextView
from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.test_config_options import TestConfigOptions
from domain.models.test_result_output_file_entry import AbstractTestResultOutputFileEntry
from res.fonts import get_font
from usecases.dto.student_mark_view_data import StudentTestCaseSummaryState
from usecases.dto.test_test_stage import TestTestStageResult


class TestCaseTestConfigTesterWidget(QGroupBox):
    run_requested = pyqtSignal(name="run_requested")  # 実行を要求する

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(
            QLabel("<html><b>入力</b>&nbsp;Ctrl+Enterでテストを実行</html>", self)
        )

        layout_cell = QHBoxLayout()
        layout_cell.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(layout_cell)

        layout_cell_buttons = QVBoxLayout()
        layout_cell_buttons.setContentsMargins(0, 0, 0, 0)
        layout_cell_buttons.setAlignment(Qt.AlignTop)
        layout_cell.addLayout(layout_cell_buttons)

        self._b_run = QPushButton(self)
        self._b_run.setText("▶")
        self._b_run.setFixedWidth(30)
        self._b_run.setFixedHeight(30)
        # noinspection PyUnresolvedReferences
        self._b_run.clicked.connect(self.run_requested)
        layout_cell_buttons.addWidget(self._b_run)

        self._editor = QPlainTextEdit(self)
        self._editor.setFont(get_font(monospace=True, small=True))
        self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._editor.installEventFilter(self)
        layout_cell.addWidget(self._editor)

        layout.addWidget(HorizontalLineWidget(self))

        layout.addWidget(QLabel("<html><b>生成された正規表現パターン</b></html>", self))

        # noinspection PyTypeChecker
        self._te_regex_pattern = PlainTextEdit(self)
        self._te_regex_pattern.setFont(get_font(monospace=True, small=True))
        self._te_regex_pattern.setReadOnly(True)
        self._te_regex_pattern.set_line_wrap(True)
        layout.addWidget(self._te_regex_pattern)

        layout.addWidget(QLabel("<html><b>テスト結果</b></html>", self))

        self._l_test_result = QLabel(self)
        self._l_test_result.setWordWrap(True)
        layout.addWidget(self._l_test_result)

        self._result_view = TestCaseResultOutputFileTextView()
        layout.addWidget(self._result_view)

        # noinspection PyTypeChecker
        self._w_test_summary_indicator = TestCaseTestSummaryIndicatorWidget(self)
        layout.addWidget(self._w_test_summary_indicator, alignment=Qt.AlignHCenter)

    def _init_signals(self):
        pass

    def run_and_update(
            self,
            *,
            expected_output_file: ExpectedOutputFile,
            test_config_options: TestConfigOptions,
    ):
        test_result: TestTestStageResult = get_test_test_stage_usecase().execute(
            expected_output_file=expected_output_file,
            test_config_options=test_config_options,
            content_text=self._editor.toPlainText(),
        )

        if test_result.has_error:
            message_first_line = test_result.error_message.split('\n')[0]
            self._l_test_result.setText(
                f"テストに失敗しました: {message_first_line}",
            )
        else:
            self._l_test_result.setText(
                f"実行時間: {test_result.test_execution_timedelta.total_seconds():,.3f}秒",
            )

            self._te_regex_pattern.setPlainText(test_result.regex_pattern)

            test_result_output_file_entry: AbstractTestResultOutputFileEntry \
                = test_result.file_test_result
            self._result_view.set_data(
                source_code_text=test_result_output_file_entry.actual.content_string,
                matched_tokens=test_result_output_file_entry.test_result.matched_tokens,
            )

            if test_result_output_file_entry.has_actual \
                    and test_result_output_file_entry.has_expected:
                if test_result_output_file_entry.test_result.is_accepted:
                    self._w_test_summary_indicator.set_data(
                        StudentTestCaseSummaryState.ACCEPTED
                    )
                else:
                    self._w_test_summary_indicator.set_data(
                        StudentTestCaseSummaryState.WRONG_ANSWER)

            else:
                self._w_test_summary_indicator.set_data(None)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        # self._editorでCtrl+Enterが押されたら実行をリクエストする
        if source is self._editor and event.type() == QEvent.KeyPress:
            # noinspection PyUnresolvedReferences
            if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
                # noinspection PyUnresolvedReferences
                self.run_requested.emit()
                return True
        return super().eventFilter(source, event)
