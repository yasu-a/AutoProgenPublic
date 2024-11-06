from PyQt5.QtCore import QObject, pyqtSlot, Qt, pyqtSignal, QEvent, QRegExp
from PyQt5.QtGui import QSyntaxHighlighter, QColor, QTextCharFormat, QKeyEvent, QRegExpValidator, \
    QCloseEvent
from PyQt5.QtWidgets import QDialog, QListWidget, QWidget, QHBoxLayout, QLabel, \
    QListWidgetItem, QVBoxLayout, QTabWidget, QPlainTextEdit, QPushButton, QLineEdit

from application.dependency.usecases import get_student_list_id_usecase, \
    get_student_mark_view_data_get_test_result_usecase, \
    get_student_mark_view_data_get_mark_summary_usecase, get_student_source_code_get_usecase, \
    get_testcase_config_list_id_usecase, get_student_mark_get_usecase, get_student_mark_put_usecase
from controls.dialog_mark_help import MarkHelpDialog
from controls.dto.dialog_mark import MarkDialogState
from controls.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from controls.res.fonts import get_font
from controls.res.icons import get_icon
from controls.widget_page_button import PageButton
from controls.widget_source_text_edit import SourceTextEdit
from controls.widget_test_summary_indicator import TestCaseTestSummaryIndicatorWidget
from domain.models.output_file_test_result import OutputFileTestResult
from domain.models.student_mark import StudentMark
from domain.models.student_master import Student
from domain.models.student_stage_result import TestResultOutputFileMapping
from domain.models.test_result_output_file_entry import AbstractTestResultOutputFileEntry
from domain.models.values import StudentID, TestCaseID, FileID, SpecialFileType
from usecases.dto.student_mark_view_data import AbstractStudentTestCaseTestResultViewData, \
    StudentMarkSummaryViewData
from utils.app_logging import create_logger


class MarkScoreEditWidget(QWidget):
    key_pressed = pyqtSignal(QKeyEvent, name="key_pressed")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._student_id: StudentID | None = None
        self._is_modified = False

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._le_score = QLineEdit(self)
        self._le_score.setValidator(QRegExpValidator(QRegExp("[1-9][0-9]|[0-9]|")))
        self._le_score.setFont(get_font(monospace=True, very_large=True, bold=True))
        print(self._le_score.font().pointSize())
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
        if student_mark is None:
            self._le_score.setEnabled(False)
            self._b_unmark.setEnabled(False)
            self._student_id = None
        else:
            if student_mark.is_marked:
                self._le_score.setText(str(student_mark.score))
            else:
                self._le_score.setText("")
            self._le_score.setEnabled(True)
            self._b_unmark.setEnabled(True)
            self._student_id = student_mark.student_id
        self._is_modified = False

    def set_unmarked(self) -> None:
        if self._student_id is None:
            return None
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
            )
        else:
            return StudentMark(
                student_id=self._student_id,
                score=score_int,
            )

    @pyqtSlot()
    def __b_unmark_clicked(self):
        self._le_score.setText("")

    @pyqtSlot()
    def __le_score_text_changed(self):
        self._is_modified = True


class StudentSourceCodeView(SourceTextEdit):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self):
        self.setEnabled(False)
        self.setReadOnly(True)
        self.setPlainText("")

    def set_data(self, source_code_text: str | None):
        if source_code_text is None:
            self.setEnabled(False)
            self.setPlainText("")
        else:
            self.setEnabled(True)
            self.setPlainText(source_code_text)


class _TestCaseResultOutputFileHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, *, test_result: OutputFileTestResult):
        super().__init__(parent)

        self._test_result = test_result

        self._format = QTextCharFormat()
        self._format.setBackground(QColor("lightgreen"))

    def highlightBlock(self, text, **kwargs):
        for token in self._test_result.matched_tokens:
            self.setFormat(token.match_begin, token.match_end, self._format)


class TestCaseResultOutputFileViewWidget(QPlainTextEdit, HorizontalScrollWithShiftAndWheelMixin):
    def __init__(
            self,
            parent: QObject = None,
            *,
            output_file_entry: AbstractTestResultOutputFileEntry,
    ):
        super().__init__(parent)

        self._output_file_entry = output_file_entry

        self._init_ui()

    def _init_ui(self):
        self.setFont(get_font(monospace=True, small=True))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setReadOnly(True)

        errors = []
        view = True
        if not self._output_file_entry.has_actual and self._output_file_entry.has_expected:
            errors.append("⚠ 出力されませんでした")
            view = False
        elif self._output_file_entry.has_actual and not self._output_file_entry.has_expected:
            errors.append("⚠ 出力されましたがテスト対象ではありません")

        if self._output_file_entry.has_actual \
                and self._output_file_entry.actual.content_string is None:
            errors.append("⚠ 出力されたストリームのエンコーディングが不明です")

        if errors and not view:
            self.setPlainText("\n".join(errors))
        elif errors and view:
            if self._output_file_entry.actual.content_string is None:
                content_text = "（不明な文字コード）"
            elif self._output_file_entry.actual.content_string == "":
                content_text = "（空）"
            else:
                content_text = self._output_file_entry.actual.content_string
            self.setPlainText(
                "\n".join(
                    errors) + "\n\n＜ストリームの内容＞\n" + content_text
            )
        else:
            self.setPlainText(self._output_file_entry.actual.content_string)

        if self._output_file_entry.has_actual and self._output_file_entry.has_expected:
            self._h = _TestCaseResultOutputFileHighlighter(
                self.document(),
                test_result=self._output_file_entry.test_result,
            )


class TestCaseValidTestResultViewWidget(QWidget):
    selected_file_id_changed = pyqtSignal(FileID, name="selected_file_id_changed")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._file_ids: list[FileID] = []

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_file_tab = QTabWidget(self)
        layout.addWidget(self._w_file_tab)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._w_file_tab.currentChanged.connect(self.__w_file_tab_current_changed)

    def set_data(self, test_result_output_files: TestResultOutputFileMapping) -> None:
        self._w_file_tab.blockSignals(True)
        self._w_file_tab.clear()
        self._file_ids.clear()
        for file_id, output_file_entry in test_result_output_files.items():
            if file_id.is_special:
                if file_id.special_file_type == SpecialFileType.STDOUT:
                    title = "[標準出力]"
                elif file_id.special_file_type == SpecialFileType.STDIN:
                    title = "[標準入力]"
                else:
                    assert False, file_id.special_file_type
            else:
                title = str(file_id.deployment_relative_path)

            self._w_file_tab.addTab(
                TestCaseResultOutputFileViewWidget(
                    self,
                    output_file_entry=output_file_entry,
                ),
                title,
            )
            self._file_ids.append(file_id)
        self._w_file_tab.blockSignals(False)

    def set_selected(self, file_id_to_select: FileID | None) -> None:
        if file_id_to_select is None:
            return
        if file_id_to_select not in self._file_ids:
            return
        i = self._file_ids.index(file_id_to_select)
        self._w_file_tab.setCurrentIndex(i)

    @pyqtSlot(int)
    def __w_file_tab_current_changed(self, i):
        # noinspection PyUnresolvedReferences
        self.selected_file_id_changed.emit(self._file_ids[i])


class TestCaseInvalidTestResultViewWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._l_title = QLabel(self)
        self._l_title.setText("テスト結果を表示できません")
        self._l_title.setFont(get_font(bold=True))
        self._l_title.setStyleSheet("color: red")
        layout.addWidget(self._l_title)

        self._l_detailed_reason = QPlainTextEdit(self)
        self._l_detailed_reason.setReadOnly(True)
        self._l_detailed_reason.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self._l_detailed_reason.setEnabled(False)
        self._l_detailed_reason.setStyleSheet("color: red")
        layout.addWidget(self._l_detailed_reason)

    def _init_signals(self):
        pass

    def set_data(self, detailed_reason: str) -> None:
        self._l_detailed_reason.setPlainText(detailed_reason)


class TestCaseTestResultViewPlaceholderWidget(QWidget):
    selected_file_id_changed = pyqtSignal(FileID, name="selected_file_id_changed")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__w: TestCaseValidTestResultViewWidget | None = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def _init_signals(self):
        pass

    def __remove_widget(self) -> None:
        while self.layout().count() > 0:
            self.layout().takeAt(0).widget().deleteLater()
        self.__w = None

    def __set_widget(self, w: QWidget) -> None:
        self.__remove_widget()
        self.layout().addWidget(w)
        self.__w = w
        if isinstance(self.__w, TestCaseValidTestResultViewWidget):
            # noinspection PyUnresolvedReferences
            self.__w.selected_file_id_changed.connect(self.selected_file_id_changed)

    def __get_widget(self) -> QWidget | None:
        return self.__w

    def set_data(
            self,
            arg: None = object(),  # デフォルト引数は引数に何も渡されていないことを示すセンチネルオブジェクト
            /,
            *,
            detailed_reason: str = None,
            test_result_output_files: TestResultOutputFileMapping = None,
    ):
        if arg is None:
            # set_data(None)
            assert detailed_reason is None and test_result_output_files is None
            # ウィジェットをクリア
            self.__remove_widget()
        elif detailed_reason is not None:
            # set_data(detailed_reason=...)
            assert arg is not None and test_result_output_files is None
            # エラー用ウィジェットを設定
            w = TestCaseInvalidTestResultViewWidget()
            w.set_data(detailed_reason=detailed_reason)
            self.__set_widget(w)
        elif test_result_output_files is not None:
            # set_data(results=...)
            assert arg is not None and detailed_reason is None
            # 正常完了時用ウィジェットを設定
            w = TestCaseValidTestResultViewWidget()
            w.set_data(test_result_output_files=test_result_output_files)
            self.__set_widget(w)
        else:
            assert False  # invalid call arguments passed

    def set_selected(self, file_id_to_select: FileID | None) -> None:
        w = self.__get_widget()
        if not isinstance(w, TestCaseValidTestResultViewWidget):
            return
        w.set_selected(file_id_to_select)


class TestCaseTestResultListItemWidget(QWidget):
    # テスト結果のテストケースのリストの項目
    # 選択中かどうか・テストケース名・テスト結果インジケータ・詳細テキストを表示する

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        layout_title = QHBoxLayout()
        layout_title.setContentsMargins(0, 2, 0, 2)
        layout_root.addLayout(layout_title)

        self._l_selected = QLabel(self)
        self._l_selected.setFixedWidth(30)
        self._l_selected.setAlignment(Qt.AlignCenter)
        self._l_selected.setFont(get_font(monospace=True, small=False))
        layout_title.addWidget(self._l_selected)

        self._l_testcase_name = QLabel(self)
        self._l_testcase_name.setMinimumWidth(200)
        self._l_testcase_name.setFont(get_font(monospace=False, small=True))
        layout_title.addWidget(self._l_testcase_name)

        layout_detail = QHBoxLayout()
        layout_root.addLayout(layout_detail)

        # noinspection PyTypeChecker
        self._l_indicator = TestCaseTestSummaryIndicatorWidget(self)
        layout_detail.addWidget(self._l_indicator)

        self._l_detail = QLabel(self)
        self._l_detail.setWordWrap(True)
        layout_detail.addWidget(self._l_detail)

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, student_testcase_test_summary: AbstractStudentTestCaseTestResultViewData):
        assert student_testcase_test_summary is not None

        # 選択中かどうか
        self._l_selected.setText("")
        # テストケース名
        self._l_testcase_name.setText(str(student_testcase_test_summary.testcase_id))
        # インジケータ
        self._l_indicator.set_data(student_testcase_test_summary.state)
        # 詳細テキスト
        if student_testcase_test_summary.is_success:
            self._l_detail.setText(student_testcase_test_summary.title_text)
        else:
            self._l_detail.setText(
                student_testcase_test_summary.title_text
            )

    @pyqtSlot(bool)
    def set_selected(self, is_selected: bool):
        if is_selected:
            self._l_selected.setText("●")
        else:
            self._l_selected.setText("")


class TestCaseTestResultListWidget(QListWidget):
    testcase_clicked = pyqtSignal(TestCaseID)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._testcase_ids: list[TestCaseID] = []

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        pass

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self.itemClicked.connect(self.__item_clicked)

    @pyqtSlot()
    def set_data(
            self,
            test_summary_lst: list[AbstractStudentTestCaseTestResultViewData] | None,
    ):
        self.clear()
        self._testcase_ids.clear()
        if test_summary_lst is not None:
            for test_summary in test_summary_lst:
                self._testcase_ids.append(test_summary.testcase_id)
                # 項目のウィジェットを初期化
                item_widget = TestCaseTestResultListItemWidget(self)
                item_widget.set_data(test_summary)
                # Qtのリスト項目を初期化
                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                # リストに追加
                self.addItem(list_item)
                # 項目のウィジェットとQtのリスト項目を関連付ける
                self.setItemWidget(list_item, item_widget)
            # # 幅を内容に合わせて調整
            # self.setFixedWidth(self.sizeHintForColumn(0) + 40)

    @pyqtSlot(TestCaseID)
    def set_selected_id(self, testcase_id_to_select: TestCaseID | None) -> None:
        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, TestCaseTestResultListItemWidget)
            testcase_id = self._testcase_ids[i]
            item_widget.set_selected(
                testcase_id_to_select is not None and testcase_id == testcase_id_to_select
            )

    @pyqtSlot(QListWidgetItem)
    def __item_clicked(self, target_list_item: QListWidgetItem):
        for i in range(self.count()):
            list_item = self.item(i)
            if list_item != target_list_item:
                continue
            testcase_id = self._testcase_ids[i]
            # noinspection PyUnresolvedReferences
            self.testcase_clicked.emit(testcase_id)


# class ExecuteResultWidget(QTabWidget):
#     def __init__(self, parent: QObject = None):
#         super().__init__(parent)
#
#         self._init_ui()
#         self._init_signals()
#
#     def _init_ui(self):
#         pass
#
#     def _init_signals(self):
#         pass
#
#     def set_data(self, execute_result: ExecuteResult):
#         for testcase_execute_result in execute_result.testcase_result_set:
#             name = str(testcase_execute_result.output_files)
#

class StudentTitleViewWidget(QWidget):
    next_student_triggered = pyqtSignal(name="next_testcase_triggered")
    prev_student_triggered = pyqtSignal(name="prev_testcase_triggered")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    # noinspection DuplicatedCode
    def _init_ui(self):
        self.setFixedHeight(50)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._b_prev = PageButton(self, text="< (A)")
        layout.addWidget(self._b_prev)

        layout.addStretch(1)

        self._l_student_id = QLabel(self)
        self._l_student_id.setFixedWidth(150)
        self._l_student_id.setFont(get_font(monospace=True, large=True, bold=True))
        self._l_student_id.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._l_student_id)

        self._l_student_name = QLabel(self)
        self._l_student_name.setFixedWidth(200)
        self._l_student_name.setFont(get_font(large=True, bold=True))
        self._l_student_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._l_student_name)

        layout.addStretch(1)

        self._b_next = PageButton(self, text="(D) >")
        layout.addWidget(self._b_next)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._b_prev.clicked.connect(self.prev_student_triggered)
        # noinspection PyUnresolvedReferences
        self._b_next.clicked.connect(self.next_student_triggered)

    def set_data(self, student: Student | None) -> None:
        if student is None:
            self._l_student_id.setText("")
            self._l_student_name.setText("")
        else:
            self._l_student_id.setText(str(student.student_id))
            self._l_student_name.setText(student.name)


class TestCaseControlWidget(QWidget):
    next_testcase_triggered = pyqtSignal(name="next_testcase_triggered")
    prev_testcase_triggered = pyqtSignal(name="prev_testcase_triggered")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._testcase_id: TestCaseID | None = None

        self._init_ui()
        self._init_signals()

    # noinspection DuplicatedCode
    def _init_ui(self):
        self.setFixedHeight(50)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._b_prev = PageButton(self, text="< (Q)")
        layout.addWidget(self._b_prev)

        layout.addStretch(1)

        self._l_testcase_id = QLabel(self)
        self._l_testcase_id.setFixedWidth(150)
        self._l_testcase_id.setFont(get_font(large=True, bold=True))
        self._l_testcase_id.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._l_testcase_id)

        layout.addStretch(1)

        self._b_next = PageButton(self, text="(E) >")
        layout.addWidget(self._b_next)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._b_prev.clicked.connect(self.prev_testcase_triggered)
        # noinspection PyUnresolvedReferences
        self._b_next.clicked.connect(self.next_testcase_triggered)

    def set_data(self, testcase_id: TestCaseID | None):
        self._testcase_id = testcase_id
        if self._testcase_id is None:
            self._l_testcase_id.setText("")
        else:
            self._l_testcase_id.setText(str(testcase_id))


# TODO: アルゴリズム改善
# noinspection DuplicatedCode
class MarkDialogStateCreator:
    def __init__(
            self,
            *,
            state: MarkDialogState,
            student_ids: list[StudentID],
            testcase_ids: list[TestCaseID],
    ):
        self._state = state
        self._student_ids = student_ids
        self._testcase_ids = testcase_ids

    @classmethod
    def __get_student_testcase_test_result_view_data(
            cls,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> AbstractStudentTestCaseTestResultViewData:
        return get_student_mark_view_data_get_test_result_usecase().execute(student_id, testcase_id)

    @property
    def _file_ids_by_testcase(self) -> dict[TestCaseID, list[FileID]]:
        if not self._student_ids:
            return {}
        if not self._testcase_ids:
            return {}
        if self._state.student_id is None:
            return {}
        file_ids_by_testcase = {}
        for testcase_id in self._testcase_ids:
            view_data = self.__get_student_testcase_test_result_view_data(
                student_id=self._state.student_id,
                testcase_id=self._state.testcase_id,
            )
            if view_data.is_success:
                file_ids_by_testcase[testcase_id] = list(view_data.output_and_results)
            else:
                file_ids_by_testcase[testcase_id] = []
        return file_ids_by_testcase

    def __create_file_id_field(self, new_testcase_id: TestCaseID | None) -> FileID | None:
        if new_testcase_id is None:
            return None
        if new_testcase_id not in self._file_ids_by_testcase:
            return None
        if self._state.file_id is None:
            file_ids = self._file_ids_by_testcase[new_testcase_id]
            if file_ids:
                return file_ids[0]
        return self._state.file_id

    def create_state_by_testcase_id(self, testcase_id: TestCaseID) -> MarkDialogState:
        if self._state.student_id is None:
            if self._student_ids:
                new_student_id = self._student_ids[0]
            else:
                new_student_id = None
        else:
            new_student_id = self._state.student_id
        new_state = MarkDialogState(
            student_id=new_student_id,
            testcase_id=testcase_id,
            file_id=self.__create_file_id_field(testcase_id),
        )
        return new_state

    def create_state_by_student_id(self, student_id: StudentID) -> MarkDialogState:
        if self._state.testcase_id is None:
            if self._testcase_ids:
                new_testcase_id = self._testcase_ids[0]
            else:
                new_testcase_id = None
        else:
            new_testcase_id = self._state.testcase_id
        new_state = MarkDialogState(
            student_id=student_id,
            testcase_id=new_testcase_id,
            file_id=self.__create_file_id_field(new_testcase_id),
        )
        return new_state

    def create_state_of_next_testcase(self, *, delta=1) -> MarkDialogState:
        if not self._testcase_ids:
            new_testcase_id = None
        elif self._state.testcase_id is None:
            new_testcase_id = self._testcase_ids[0]
        else:
            i = self._testcase_ids.index(self._state.testcase_id)
            i += delta
            if 0 <= i < len(self._testcase_ids):
                new_testcase_id = self._testcase_ids[i]
            else:
                new_testcase_id = self._state.testcase_id
        return MarkDialogState(
            student_id=self._state.student_id,
            testcase_id=new_testcase_id,
            file_id=self.__create_file_id_field(new_testcase_id),
        )

    def create_state_of_prev_testcase(self) -> MarkDialogState:
        return self.create_state_of_next_testcase(delta=-1)

    def create_state_of_first_student(self) -> MarkDialogState:
        if self._student_ids:
            new_student_id = self._student_ids[0]
        else:
            new_student_id = None

        if self._state.testcase_id is None:
            if self._testcase_ids:
                new_testcase_id = self._testcase_ids[0]
            else:
                new_testcase_id = None
        else:
            new_testcase_id = self._state.testcase_id

        return MarkDialogState(
            student_id=new_student_id,
            testcase_id=new_testcase_id,
            file_id=self.__create_file_id_field(new_testcase_id),
        )

    def create_state_of_next_student(self, *, delta=1) -> MarkDialogState:
        if self._state.student_id is None:
            return self.create_state_of_first_student()

        if self._state.student_id not in self._student_ids:
            return self.create_state_of_first_student()

        i = self._student_ids.index(self._state.student_id)
        i += delta
        if 0 <= i < len(self._student_ids):
            new_student_id = self._student_ids[i]
        else:
            new_student_id = self._state.student_id

        if self._state.testcase_id is None:
            if self._testcase_ids:
                new_testcase_id = self._testcase_ids[0]
            else:
                new_testcase_id = None
        else:
            new_testcase_id = self._state.testcase_id

        return MarkDialogState(
            student_id=new_student_id,
            testcase_id=new_testcase_id,
            file_id=self.__create_file_id_field(new_testcase_id),
        )

    def create_state_of_prev_student(self) -> MarkDialogState:
        return self.create_state_of_next_student(delta=-1)

    def create_state_of_next_file(self, *, delta=1) -> MarkDialogState:
        if self._state.testcase_id is None:
            new_file_id = None
        else:
            file_ids = self._file_ids_by_testcase[self._state.testcase_id]
            if self._state.file_id not in file_ids:
                new_file_id = None
            elif not file_ids:
                new_file_id = None
            else:
                i = file_ids.index(self._state.file_id)
                i += delta
                if 0 <= i < len(file_ids):
                    new_file_id = file_ids[i]
                else:
                    new_file_id = self._state.file_id

        return MarkDialogState(
            student_id=self._state.student_id,
            testcase_id=self._state.testcase_id,
            file_id=new_file_id,
        )

    def create_state_of_prev_file(self) -> MarkDialogState:
        return self.create_state_of_next_file(delta=-1)


class MarkDialog(QDialog):
    _logger = create_logger()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._student_ids: list[StudentID] = get_student_list_id_usecase().execute()
        # ^ get_student_id_list_usecase
        self._testcase_ids: list[TestCaseID] = get_testcase_config_list_id_usecase().execute()
        self._state = MarkDialogState()

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setWindowTitle("採点")
        self.setModal(True)
        self.resize(1300, 700)
        self.installEventFilter(self)

        layout = QVBoxLayout()
        self.setLayout(layout)

        if "middle":
            layout_middle = QHBoxLayout()
            layout.addLayout(layout_middle)

            if "middle-left":
                layout_middle_left = QVBoxLayout()
                layout_middle.addLayout(layout_middle_left)

                self._w_student_control = StudentTitleViewWidget(self)
                layout_middle_left.addWidget(self._w_student_control)

                if "middle-left-inner":
                    layout_middle_left_inner = QHBoxLayout()
                    layout_middle_left_inner.setContentsMargins(0, 0, 0, 0)
                    layout_middle_left.addLayout(layout_middle_left_inner)

                    self._w_source_code_view = StudentSourceCodeView(self)
                    layout_middle_left_inner.addWidget(self._w_source_code_view)

                    self._w_test_result_view_placeholder \
                        = TestCaseTestResultViewPlaceholderWidget(self)
                    layout_middle_left_inner.addWidget(self._w_test_result_view_placeholder)

            if "middle-right":
                layout_middle_right = QVBoxLayout()
                layout_middle.addLayout(layout_middle_right)

                self._w_testcase_control = TestCaseControlWidget(self)
                self._w_testcase_control.setFixedWidth(300)
                layout_middle_right.addWidget(self._w_testcase_control)

                self._w_testcase_result_list = TestCaseTestResultListWidget(self)
                self._w_testcase_result_list.setFixedWidth(300)
                self._w_testcase_result_list.setFocusPolicy(Qt.NoFocus)
                layout_middle_right.addWidget(self._w_testcase_result_list)

        if "bottom":
            layout_bottom = QHBoxLayout()
            layout.addLayout(layout_bottom)

            layout_bottom.addStretch(1)

            self._w_mark_score = MarkScoreEditWidget(self)
            layout_bottom.addWidget(self._w_mark_score)

            layout_bottom.addStretch(1)

            self._b_help = QPushButton("ショートカット一覧", self)
            self._b_help.setIcon(get_icon("keyboard"))
            self._b_help.setFixedHeight(30)
            self._b_help.setFocusPolicy(Qt.NoFocus)
            layout_bottom.addWidget(self._b_help)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._w_testcase_result_list.testcase_clicked.connect(
            self.__w_testcase_result_list_testcase_clicked
        )
        # noinspection PyUnresolvedReferences
        self._w_testcase_control.next_testcase_triggered.connect(
            self.__w_testcase_control_next_testcase_triggered
        )
        # noinspection PyUnresolvedReferences
        self._w_testcase_control.prev_testcase_triggered.connect(
            self.__w_testcase_control_prev_testcase_triggered
        )
        # noinspection PyUnresolvedReferences
        self._w_student_control.next_student_triggered.connect(
            self.__w_student_control_next_student_triggered
        )
        # noinspection PyUnresolvedReferences
        self._w_student_control.prev_student_triggered.connect(
            self.__w_student_control_prev_student_triggered
        )
        # noinspection PyUnresolvedReferences
        self._w_test_result_view_placeholder.selected_file_id_changed.connect(
            self.__w_test_result_view_placeholder_selected_file_id_changed
        )
        # noinspection PyUnresolvedReferences
        self._w_mark_score.key_pressed.connect(
            self.__w_mark_score_key_pressed
        )
        # noinspection PyUnresolvedReferences
        self._b_help.clicked.connect(
            self.__b_help_clicked
        )

    @classmethod
    def __get_student_mark_summary_view_data(
            cls,
            student_id: StudentID,
    ) -> StudentMarkSummaryViewData:
        return get_student_mark_view_data_get_mark_summary_usecase().execute(student_id)

    @classmethod
    def __get_student_testcase_test_result_view_data(
            cls,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> AbstractStudentTestCaseTestResultViewData:
        return get_student_mark_view_data_get_test_result_usecase().execute(student_id, testcase_id)

    @classmethod
    def __get_student_source_code(
            cls,
            student_id: StudentID,
    ) -> str | None:
        return get_student_source_code_get_usecase().execute(student_id)

    @classmethod
    def __get_student_mark(
            cls,
            student_id: StudentID,
    ) -> StudentMark:
        return get_student_mark_get_usecase().execute(student_id)

    @classmethod
    def __put_student_mark(
            cls,
            student_mark: StudentMark,
    ) -> None:
        get_student_mark_put_usecase().execute(student_mark)

    @property
    def states(self) -> MarkDialogStateCreator:
        return MarkDialogStateCreator(
            state=self._state,
            student_ids=self._student_ids,
            testcase_ids=self._testcase_ids,
        )

    def __reflect_state(self):
        # self._w_student_title_view: StudentTitleViewWidget
        if self._state.student_id is None:
            self._w_student_control.set_data(None)
        else:
            self._w_student_control.set_data(
                student=self.__get_student_mark_summary_view_data(self._state.student_id).student,
            )

        # self._w_testcase_control: TestCaseControlWidget(self)
        if self._state.student_id is None:
            self._w_testcase_control.set_data(
                testcase_id=None,
            )
        else:
            self._w_testcase_control.set_data(
                testcase_id=self._state.testcase_id,
            )

        # self._w_source_code_view: StudentSourceCodeView
        if self._state.student_id is None:
            self._w_source_code_view.set_data(
                source_code_text=None,
            )
        else:
            self._w_source_code_view.set_data(
                source_code_text=self.__get_student_source_code(
                    self._state.student_id
                ),
            )

        # self._w_test_result_view_placeholder: TestCaseTestResultViewPlaceholderWidget(self)
        if self._state.student_id is None:
            self._w_test_result_view_placeholder.set_data(
                detailed_reason="生徒が選択されていません",
            )
        elif self._state.testcase_id is None:
            self._w_test_result_view_placeholder.set_data(
                detailed_reason="テストケースが選択されていません",
            )
        else:
            summary_view_data = self.__get_student_mark_summary_view_data(self._state.student_id)
            if summary_view_data.is_ready:
                testcase_result_view_data = self.__get_student_testcase_test_result_view_data(
                    student_id=self._state.student_id,
                    testcase_id=self._state.testcase_id,
                )
                if testcase_result_view_data.is_success:
                    self._w_test_result_view_placeholder.set_data(
                        test_result_output_files=testcase_result_view_data.output_and_results,
                    )
                    self._w_test_result_view_placeholder.set_selected(self._state.file_id)
                else:
                    self._w_test_result_view_placeholder.set_data(
                        detailed_reason=testcase_result_view_data.detailed_reason,
                    )
            else:
                self._w_test_result_view_placeholder.set_data(
                    detailed_reason=summary_view_data.reason,
                )

        # self._w_testcase_result_list: TestCaseTestResultListWidget(self)
        if self._state.student_id is None:
            self._w_testcase_result_list.set_data(None)
        else:
            self._w_testcase_result_list.set_data(
                [
                    self.__get_student_testcase_test_result_view_data(
                        student_id=self._state.student_id,
                        testcase_id=testcase_id,
                    )
                    for testcase_id in self._testcase_ids
                ]
            )
            self._w_testcase_result_list.set_selected_id(self._state.testcase_id)

        # self._w_mark_score: MarkScoreEditWidget
        if self._state.student_id is None:
            self._w_mark_score.set_data(None)
        else:
            self._w_mark_score.set_data(self.__get_student_mark(self._state.student_id))

    def __save_data(self):
        if not self._w_mark_score.is_modified():
            return
        student_mark = self._w_mark_score.get_data()
        if student_mark is not None:
            self._logger.info(f"student mark saved\n{student_mark}")
            assert student_mark.student_id == self._state.student_id
            self.__put_student_mark(student_mark)

    def set_data(self, state: MarkDialogState):
        if self._state == state:
            return
        self.__save_data()
        self._state = state
        self.__reflect_state()

    @pyqtSlot(TestCaseID)
    def __w_testcase_result_list_testcase_clicked(self, testcase_id: TestCaseID):
        new_state = self.states.create_state_by_testcase_id(testcase_id)
        self.set_data(new_state)

    @pyqtSlot()
    def __w_testcase_control_next_testcase_triggered(self):
        new_state = self.states.create_state_of_next_testcase()
        self.set_data(new_state)

    @pyqtSlot()
    def __w_testcase_control_prev_testcase_triggered(self):
        new_state = self.states.create_state_of_prev_testcase()
        self.set_data(new_state)

    @pyqtSlot()
    def __w_student_control_next_student_triggered(self):
        new_state = self.states.create_state_of_next_student()
        self.set_data(new_state)

    @pyqtSlot()
    def __w_student_control_prev_student_triggered(self):
        new_state = self.states.create_state_of_prev_student()
        self.set_data(new_state)

    @pyqtSlot(FileID)
    def __w_test_result_view_placeholder_selected_file_id_changed(self, file_id: FileID):
        self._state.file_id = file_id

    @pyqtSlot(QKeyEvent)
    def __w_mark_score_key_pressed(self, evt: QKeyEvent):
        self.__on_key_press(evt)

    @pyqtSlot()
    def __b_help_clicked(self):
        dialog = MarkHelpDialog()
        dialog.exec_()

    def __on_key_press(self, evt: QKeyEvent):
        key = evt.key()
        new_state = None
        if key == Qt.Key_Q:
            new_state = self.states.create_state_of_prev_testcase()
        elif key == Qt.Key_E:
            new_state = self.states.create_state_of_next_testcase()
        elif key == Qt.Key_A or key == Qt.Key_Left:
            new_state = self.states.create_state_of_prev_student()
        elif key == Qt.Key_D or key == Qt.Key_Right:
            new_state = self.states.create_state_of_next_student()
        elif key == Qt.Key_Z:
            new_state = self.states.create_state_of_prev_file()
        elif key == Qt.Key_C:
            new_state = self.states.create_state_of_next_file()
        elif key == Qt.Key_Space or key == Qt.Key_Delete:
            self._w_mark_score.set_unmarked()
        elif key == Qt.Key_Escape:
            self.close()

        if new_state is not None:
            self.set_data(new_state)

    def eventFilter(self, target: QObject, evt: QEvent):
        if evt.type() == QEvent.KeyPress:
            self.__on_key_press(evt)
            return True
        return False

    def closeEvent(self, evt: QCloseEvent):
        self.__save_data()
