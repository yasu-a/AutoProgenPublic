from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget

from controls.widget_testcase_result_output_file_text_view import \
    TestCaseResultOutputFileTextView
from domain.models.test_result_output_file_entry import AbstractTestResultOutputFileEntry


class TestCaseResultOutputFileViewWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._output_file_entry: AbstractTestResultOutputFileEntry | None = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # エラーメッセージを表示するラベル
        self._l_messages = QLabel(self)
        self._l_messages.setWordWrap(True)
        self._l_messages.setStyleSheet("color: red")
        layout.addWidget(self._l_messages)

        # 内容を表示するテキストエディタ
        self._te = TestCaseResultOutputFileTextView()
        layout.addWidget(self._te)

    def _init_signals(self):
        pass

    def __update(self):
        of = self._output_file_entry

        # データがない
        if of is None:
            self._te.setPlainText("")
            self._te.setEnabled(False)
            return

        # ウィジェットを有効化
        self._te.setEnabled(True)

        # エラーを分析
        errors: list[tuple[str, str | None]] = []  # message, detailed_message
        content_replacement = None
        actual_content = ""
        if of.has_actual:
            actual_content = of.actual.content_string
            if actual_content is None:
                errors.append(
                    (
                        "文字コードが不明です",
                        None,
                    )
                )
                actual_content = ""
                content_replacement = "（不明な文字コード）"
            elif actual_content == "":
                content_replacement = "（空）"
            else:
                pass  # 正常な出力
            if of.has_expected:
                pass  # 正常な結果
            else:
                errors.append(
                    (
                        "テスト対象ではありません",
                        "テスト対象である場合はテストケースの自動テストの構成でストリームを追加してください",
                    ),
                )
        else:
            if of.has_expected:
                errors.append(
                    (
                        "プログラムから出力されませんでした",
                        None,
                    ),
                )
            else:
                assert False, "unreachable"

        # エラーを表示
        if errors:
            self._l_messages.show()
            error_text = []
            for message, detailed_message in errors:
                error_text.append(f"⚠ {message}")
                if detailed_message is not None:
                    error_text[-1] += f" - {detailed_message}"
            self._l_messages.setText("\n".join(error_text))
        else:
            self._l_messages.hide()

        # プレイスホルダーを表示するか実際の内容を表示するか
        if content_replacement is None:
            content_text = actual_content
            pure_text_shown = True
        else:
            content_text = content_replacement
            pure_text_shown = False

        # テキストをセット
        if of.has_actual and of.has_expected and pure_text_shown:
            self._te.set_data(
                source_code_text=content_text,
                matched_tokens=of.test_result.matched_tokens,
            )
        else:
            self._te.set_data(
                source_code_text=content_text,
                matched_tokens=None,  # ハイライトしない
            )

    def set_data(self, output_file_entry: AbstractTestResultOutputFileEntry):
        self._output_file_entry = output_file_entry
        self.__update()
