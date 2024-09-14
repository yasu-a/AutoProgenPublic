from PyQt5.QtCore import QObject, pyqtSlot, Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QShowEvent, QSyntaxHighlighter, QColor, QTextCharFormat
from PyQt5.QtWidgets import QDialog, QListWidget, QWidget, QHBoxLayout, QLabel, \
    QListWidgetItem, QVBoxLayout, QTabWidget, QPlainTextEdit

from app_logging import create_logger
from application.dependency.services import get_mark_snapshot_service
from controls.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from controls.widget_test_summary_indicator import TestCaseTestSummaryIndicatorWidget
from domain.models.result_test import TestCaseTestResult, TestCaseTestResultMapping, \
    OutputFileTestResult
from domain.models.student_master import Student
from domain.models.values import StudentID, TestCaseID
from dto.mark import AbstractStudentMarkSnapshot, StudentMarkSnapshotMapping, \
    TestCaseExecuteAndTestResultPair, OutputFileAndTestResultPair
from fonts import font


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
            output_file_and_test_result: OutputFileAndTestResultPair,
    ):
        super().__init__(parent)

        self._output_file_and_test_result = output_file_and_test_result

        self._init_ui()

    def _init_ui(self):
        self.setFont(font(monospace=True, small=True))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setReadOnly(True)
        content_string = self._output_file_and_test_result.output_file.content_string
        if content_string is None:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            self.setPlainText(content_string)
        self._h = _TestCaseResultOutputFileHighlighter(
            self.document(),
            test_result=self._output_file_and_test_result.test_result,
        )


class StudentTestCaseTitleWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setFixedHeight(50)

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addStretch(1)

        self._l_student_id = QLabel(self)
        self._l_student_id.setFixedWidth(150)
        self._l_student_id.setFont(font(monospace=True, large=True))
        layout.addWidget(self._l_student_id)

        self._l_student_name = QLabel(self)
        self._l_student_name.setFixedWidth(150)
        self._l_student_name.setFont(font(large=True))
        layout.addWidget(self._l_student_name)

        self._l_testcase_id = QLabel(self)
        self._l_testcase_id.setFixedWidth(150)
        self._l_testcase_id.setFont(font(large=True))
        layout.addWidget(self._l_testcase_id)

        layout.addStretch(1)

    def _init_signals(self):
        pass

    def set_data(self, student: Student = None, testcase_id: TestCaseID = None) -> None:
        if student is None:
            self._l_student_id.setText("")
            self._l_student_name.setText("")
        else:
            self._l_student_id.setText(str(student.student_id))
            self._l_student_name.setText(student.name)

        if testcase_id is None:
            self._l_testcase_id.setText("")
        else:
            self._l_testcase_id.setText(str(testcase_id))


class TestCaseValidTestResultViewWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_file_tab = QTabWidget(self)
        layout.addWidget(self._w_file_tab)

    def _init_signals(self):
        pass

    def set_data(self, result_pair: TestCaseExecuteAndTestResultPair) -> None:
        self._w_file_tab.clear()
        for file_id in result_pair.list_file_ids():
            output_file_and_test_result = result_pair.get_output_file_and_test_result_pair(file_id)
            self._w_file_tab.addTab(
                TestCaseResultOutputFileViewWidget(
                    self,
                    output_file_and_test_result=output_file_and_test_result,
                ),
                str(file_id.deployment_relative_path),
            )


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
        self._l_title.setStyleSheet("color: red")
        layout.addWidget(self._l_title)

        self._l_detailed_reason = QLabel(self)
        self._l_detailed_reason.setWordWrap(True)
        self._l_detailed_reason.setStyleSheet("color: red")
        layout.addWidget(self._l_detailed_reason)

        layout.addStretch(1)

    def _init_signals(self):
        pass

    def set_data(self, detailed_reason: str) -> None:
        self._l_detailed_reason.setText(detailed_reason)


class TestCaseTestResultViewPlaceholderWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

    def _init_signals(self):
        pass

    def __remove_widget(self) -> None:
        while self.layout().count() > 0:
            self.layout().takeAt(0).widget().deleteLater()

    def __set_widget(self, w: QWidget) -> None:
        self.__remove_widget()
        self.layout().addWidget(w)

    def set_data(
            self,
            arg: None = object(),  # デフォルト引数は引数に何も渡されていないことを示すセンチネルオブジェクト
            /,
            *,
            detailed_reason: str = None,
            result_pair: TestCaseExecuteAndTestResultPair = None,
    ):
        if arg is None:
            # set_data(None)
            assert detailed_reason is None and result_pair is None
            # ウィジェットをクリア
            self.__remove_widget()
        elif detailed_reason is not None:
            # set_data(detailed_reason=...)
            assert arg is not None and result_pair is None
            # エラー用ウィジェットを設定
            w = TestCaseInvalidTestResultViewWidget()
            w.set_data(detailed_reason=detailed_reason)
            self.__set_widget(w)
        elif result_pair is not None:
            # set_data(results=...)
            assert arg is not None and detailed_reason is None
            # 正常完了時用ウィジェットを設定
            w = TestCaseValidTestResultViewWidget()
            w.set_data(result_pair=result_pair)
            self.__set_widget(w)
        else:
            assert False  # invalid call arguments passed


class MarkStudentListItemWidget(QWidget):
    # 採点ダイアログの生徒リストの項目
    # 生徒が選択中かどうか・学籍番号・名前・ステータス(点数 or 未採点 or 再実行が必要）を表示する

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._student_mark_snapshot: AbstractStudentMarkSnapshot | None = None  # 初期値だけNone

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        self.setLayout(layout)

        self._l_selected = QLabel(self)
        self._l_selected.setFixedWidth(30)
        self._l_selected.setAlignment(Qt.AlignCenter)
        self._l_selected.setFont(font(monospace=True, small=False))
        layout.addWidget(self._l_selected)

        self._l_student_id = QLabel(self)
        self._l_student_id.setFixedWidth(90)
        self._l_student_id.setFont(font(monospace=True, small=True))
        layout.addWidget(self._l_student_id)

        self._l_student_name = QLabel(self)
        self._l_student_name.setFixedWidth(100)
        self._l_student_name.setFont(font(monospace=False, small=True))
        layout.addWidget(self._l_student_name)

        self._l_score = QLabel(self)
        self._l_score.setFixedWidth(40)
        self._l_score.setFont(font(monospace=False, small=True))
        layout.addWidget(self._l_score)

        self._l_status = QLabel(self)
        self._l_status.setFixedWidth(80)
        self._l_status.setFont(font(monospace=False, small=True))
        layout.addWidget(self._l_status)

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, student_mark_snapshot: AbstractStudentMarkSnapshot):
        assert student_mark_snapshot is not None
        self._student_mark_snapshot = student_mark_snapshot

        def set_background_color(color):
            self.setAttribute(Qt.WA_StyledBackground, True)
            self.setStyleSheet(f"background-color: {color}")

        # 生徒が選択中かどうか
        self._l_selected.setText("")
        # 学籍番号
        self._l_student_id.setText(str(student_mark_snapshot.student.student_id))
        # 名前
        self._l_student_name.setText(student_mark_snapshot.student.name)
        # 点数
        if student_mark_snapshot.mark.is_marked:
            self._l_score.setText(f"{student_mark_snapshot.mark.score:>2d}点")
            set_background_color("lightgreen")
        else:
            self._l_score.setText("--")
            set_background_color("lightgray")
        # ステータス
        self._l_status.setText(student_mark_snapshot.preparation_state_title)
        self._l_status.setToolTip(student_mark_snapshot.preparation_state_detailed_text)
        set_background_color(student_mark_snapshot.indicator_color)

    def get_data(self) -> AbstractStudentMarkSnapshot:
        return self._student_mark_snapshot

    @pyqtSlot(bool)
    def set_selected(self, is_selected: bool):
        if is_selected:
            self._l_selected.setText("●")
        else:
            self._l_selected.setText("")

    def is_selected(self) -> bool:
        return bool(self._l_selected.text())


class MarkStudentListWidget(QListWidget):
    student_clicked = pyqtSignal(StudentID)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        pass

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self.itemClicked.connect(self.__item_clicked)

    @pyqtSlot()
    def set_data(self, student_snapshot_mapping: StudentMarkSnapshotMapping):
        for student_id, student_mark_snapshot in student_snapshot_mapping.items():
            # 項目のウィジェットを初期化
            item_widget = MarkStudentListItemWidget(self)
            item_widget.set_data(student_mark_snapshot)
            # Qtのリスト項目を初期化
            # QListWidgetItemのコンストラクタにselfをつけてはいけない！！！
            # https://forum.qt.io/topic/30164/adding-item-to-beginning-of-qlistwidget-doesn-t-work-for-me-solved
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            # リストに追加
            self.addItem(list_item)
            # 項目のウィジェットとQtのリスト項目を関連付ける
            self.setItemWidget(list_item, item_widget)
        # 幅を内容に合わせて調整
        self.setFixedWidth(self.sizeHintForColumn(0) + 40)

    @pyqtSlot(StudentID)
    def set_selected_id(self, student_id_to_select: StudentID | None) -> None:
        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, MarkStudentListItemWidget)
            student_id = item_widget.get_data().student_id
            item_widget.set_selected(
                student_id_to_select is not None and student_id == student_id_to_select
            )

    def get_selected_id(self) -> StudentID | None:
        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, MarkStudentListItemWidget)
            if item_widget.is_selected():
                return item_widget.get_data().student_id
        return None

    @pyqtSlot(QListWidgetItem)
    def __item_clicked(self, item: QListWidgetItem):
        item_widget = self.itemWidget(item)
        assert isinstance(item_widget, MarkStudentListItemWidget)
        student_id = item_widget.get_data().student_id
        # noinspection PyUnresolvedReferences
        self.student_clicked.emit(student_id)


class MarkResultTestCaseListItemWidget(QWidget):
    # テスト結果のテストケースのリストの項目
    # 選択中かどうか・テストケース名・テスト結果インジケータ・詳細テキストを表示する

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._testcase_test_result: TestCaseTestResult | None = None  # 初期値だけNone

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
        self._l_selected.setFont(font(monospace=True, small=False))
        layout_title.addWidget(self._l_selected)

        self._l_testcase_name = QLabel(self)
        self._l_testcase_name.setFixedWidth(200)
        self._l_testcase_name.setFont(font(monospace=False, small=True))
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
    def set_data(self, testcase_test_result: TestCaseTestResult):
        assert testcase_test_result is not None
        self._testcase_test_result = testcase_test_result

        # 選択中かどうか
        self._l_selected.setText("")
        # テストケース名
        self._l_testcase_name.setText(str(testcase_test_result.testcase_id))
        # インジケータ
        self._l_indicator.set_data(testcase_test_result.summary)
        # 詳細テキスト
        self._l_detail.setText(testcase_test_result.reason or "")

    def get_data(self) -> TestCaseTestResult:
        return self._testcase_test_result

    @pyqtSlot(bool)
    def set_selected(self, is_selected: bool):
        if is_selected:
            self._l_selected.setText("●")
        else:
            self._l_selected.setText("")

    def is_selected(self):
        return bool(self._l_selected.text())  # TODO: 内部状態で管理する


class MarkResultTestCaseListWidget(QListWidget):
    testcase_clicked = pyqtSignal(TestCaseID)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        pass

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self.itemClicked.connect(self.__item_clicked)

    @pyqtSlot()
    def set_data(self, testcase_test_results: TestCaseTestResultMapping | None):
        self.clear()
        if testcase_test_results is not None:
            for testcase_id, test_result in testcase_test_results.items():
                # 項目のウィジェットを初期化
                item_widget = MarkResultTestCaseListItemWidget(self)
                item_widget.set_data(test_result)
                # Qtのリスト項目を初期化
                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                # リストに追加
                self.addItem(list_item)
                # 項目のウィジェットとQtのリスト項目を関連付ける
                self.setItemWidget(list_item, item_widget)
            # 幅を内容に合わせて調整
            self.setFixedWidth(self.sizeHintForColumn(0) + 40)

    @pyqtSlot(TestCaseID)
    def set_selected_id(self, testcase_id_to_select: TestCaseID | None) -> None:
        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, MarkResultTestCaseListItemWidget)
            testcase_id = item_widget.get_data().testcase_id
            item_widget.set_selected(
                testcase_id_to_select is not None and testcase_id == testcase_id_to_select
            )

    def get_selected_id(self) -> TestCaseID | None:
        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            assert isinstance(item_widget, MarkResultTestCaseListItemWidget)
            if item_widget.is_selected():
                return item_widget.get_data().testcase_id
        return None

    @pyqtSlot(QListWidgetItem)
    def __item_clicked(self, item: QListWidgetItem):
        item_widget = self.itemWidget(item)
        assert isinstance(item_widget, MarkResultTestCaseListItemWidget)
        testcase_id = item_widget.get_data().testcase_id
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


class MarkDialog(QDialog):
    _logger = create_logger()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        # 全体（全生徒）の採点に必要なデータのスナップショットをとる
        self._project_mark_snapshot = get_mark_snapshot_service().take_project_snapshot()

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setWindowTitle(f"採点")
        self.setModal(True)
        self.resize(1200, 700)

        layout = QHBoxLayout()
        self.setLayout(layout)

        # 生徒リスト
        self._w_student_list = MarkStudentListWidget(self)
        self._w_student_list.set_data(self._project_mark_snapshot.student_snapshots)
        layout.addWidget(self._w_student_list)

        # メインパネル
        if "middle":
            layout_middle = QVBoxLayout()
            layout.addLayout(layout_middle)

            # タイトル
            self._w_title = StudentTestCaseTitleWidget(self)
            self._w_title.set_data(
                student=None,
                testcase_id=None,
            )
            layout_middle.addWidget(self._w_title)

            # テスト結果
            self._w_test_result_view_placeholder = TestCaseTestResultViewPlaceholderWidget(self)
            self._w_test_result_view_placeholder.set_data(None)
            layout_middle.addWidget(self._w_test_result_view_placeholder)

        # テストケースリスト
        self._w_testcase_result_list = MarkResultTestCaseListWidget(self)
        layout.addWidget(self._w_testcase_result_list)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._w_student_list.student_clicked.connect(
            self.__w_student_list_student_clicked
        )
        # noinspection PyUnresolvedReferences
        self._w_testcase_result_list.testcase_clicked.connect(
            self.__w_testcase_result_list_testcase_clicked
        )

    def __update_with_selection(self):
        selected_student_id = self._w_student_list.get_selected_id()
        selected_testcase_id = self._w_testcase_result_list.get_selected_id()

        # 生徒リスト
        self._w_student_list.set_selected_id(
            student_id_to_select=selected_student_id,
        )

        # テストケースリスト
        if selected_student_id is not None:
            student_snapshot = self._project_mark_snapshot.student_snapshots[selected_student_id]
            self._w_testcase_result_list.set_data(
                testcase_test_results=student_snapshot.testcase_test_results,
            )
        else:
            self._w_testcase_result_list.set_data(
                testcase_test_results=None,
            )

        # タイトル
        self._w_title.set_data(
            student=self._project_mark_snapshot.student_snapshots[selected_student_id].student,
            testcase_id=selected_testcase_id,
        )

        # テスト結果
        if selected_student_id is None:
            self._w_test_result_view_placeholder.set_data(
                detailed_reason="生徒を選択してください",
            )
        else:
            student_snapshot = self._project_mark_snapshot.student_snapshots[selected_student_id]
            if not student_snapshot.is_ready:
                self._w_test_result_view_placeholder.set_data(
                    detailed_reason="採点できません：" + student_snapshot.preparation_state_detailed_text,
                )
            else:
                if selected_testcase_id is None:
                    self._w_test_result_view_placeholder.set_data(
                        detailed_reason="テストケースを選択してください",
                    )  # unreachable
                elif selected_testcase_id not in student_snapshot.testcase_execute_and_test_results:
                    self._w_test_result_view_placeholder.set_data(
                        detailed_reason="テスト結果が存在しません",
                    )
                else:
                    result_pair \
                        = student_snapshot.testcase_execute_and_test_results[selected_testcase_id]
                    self._w_test_result_view_placeholder.set_data(
                        result_pair=result_pair,
                    )

    @pyqtSlot(StudentID)
    def set_selected_student(self, student_id: StudentID | None):  # None if deselecting
        # 指定された生徒を選択する
        self._w_student_list.set_selected_id(
            student_id_to_select=student_id,
        )

        # 表示を更新
        self.__update_with_selection()

    @pyqtSlot(TestCaseID)
    def set_selected_testcase(self, testcase_id: TestCaseID | None):  # None if deselecting
        # 指定されたテストケースを選択する
        self._w_testcase_result_list.set_selected_id(
            testcase_id_to_select=testcase_id,
        )

        # 表示を更新
        self.__update_with_selection()

    def showEvent(self, evt: QShowEvent):
        self.set_selected_student(self._project_mark_snapshot.get_first_student_id())

    def closeEvent(self, evt: QCloseEvent):
        pass

    @pyqtSlot(StudentID)
    def __w_student_list_student_clicked(self, student_id: StudentID):
        self.set_selected_student(student_id)

    @pyqtSlot(TestCaseID)
    def __w_testcase_result_list_testcase_clicked(self, testcase_id: TestCaseID):
        self.set_selected_testcase(testcase_id)
