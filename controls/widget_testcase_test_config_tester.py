from PyQt5.QtCore import QObject, pyqtSignal, QEvent, Qt
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QGroupBox, QPlainTextEdit

from application.dependency.usecases import get_test_test_stage_usecase
from controls.res.fonts import get_font
from controls.widget_test_summary_indicator import TestCaseTestSummaryIndicatorWidget
from controls.widget_testcase_result_otuput_file_view import TestCaseResultOutputFileViewWidget
from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.test_config_options import TestConfigOptions
from usecases.dto.student_mark_view_data import StudentTestCaseSummaryState


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

        self._editor = QPlainTextEdit(self)
        self._editor.setFont(get_font(monospace=True, small=True))
        self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._editor.installEventFilter(self)
        layout.addWidget(self._editor)

        layout.addWidget(QLabel("<html><b>テスト結果</b></html>", self))

        self._result_view = TestCaseResultOutputFileViewWidget()
        layout.addWidget(self._result_view)

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
        test_result_output_file_entry = get_test_test_stage_usecase().execute(
            expected_output_file=expected_output_file,
            test_config_options=test_config_options,
            content_text=self._editor.toPlainText(),
        )
        self._result_view.set_data(test_result_output_file_entry)
        if test_result_output_file_entry.has_actual and test_result_output_file_entry.has_expected:
            if test_result_output_file_entry.test_result.is_accepted:
                self._w_test_summary_indicator.set_data(StudentTestCaseSummaryState.ACCEPTED)
            else:
                self._w_test_summary_indicator.set_data(StudentTestCaseSummaryState.WRONG_ANSWER)
        else:
            self._w_test_summary_indicator.set_data(None)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        # self._editorでCtrl+Enterが押されたら実行をリクエストする
        if source is self._editor and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
                # noinspection PyUnresolvedReferences
                self.run_requested.emit()
                return True
        return super().eventFilter(source, event)
