"""採点画面の表示、画面内の移動、点数保存を管理する。"""

from dataclasses import dataclass

from PyQt5.QtCore import QObject, pyqtSlot, Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QKeyEvent, QCloseEvent
from PyQt5.QtWidgets import QDialog, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QPushButton

from autoprogen.control.dialog_mark_help import MarkHelpDialog
from autoprogen.control.widget_mark_score_edit import MarkScoreEditWidget
from autoprogen.control.widget_page_button import PageButton
from autoprogen.control.widget_student_source_code_view import StudentSourceCodeView
from autoprogen.control.widget_testcase_test_result_list import TestCaseTestResultListWidget
from autoprogen.control.widget_testcase_test_result_view import TestCaseTestResultViewWidget
from autoprogen.domain.model.student import Student
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import StudentID, TestCaseID, FileID
from autoprogen.res.font import get_font
from autoprogen.res.icon import get_icon
from autoprogen.usecase.dto.student_mark_view_data import (
    AbstractStudentTestCaseTestResultViewData,
    StudentMarkSummaryViewData,
)
from autoprogen.usecase.global_settings import GlobalSettingsGetUseCase
from autoprogen.usecase.student import StudentListIDUseCase
from autoprogen.usecase.student_mark import StudentMarkGetUseCase, StudentMarkPutUseCase
from autoprogen.usecase.student_mark_view_data import (
    StudentMarkViewDataGetTestResultUseCase,
    StudentMarkViewDataGetMarkSummaryUseCase,
)
from autoprogen.usecase.student_source_code import StudentSourceCodeGetUseCase
from autoprogen.usecase.testcase_config import TestCaseListIDUseCase
from autoprogen.util.app_logging import create_logger


class MarkStudentControlWidget(QWidget):
    """採点対象の学生名を表示し、前後移動の操作を通知する。"""

    next_student_triggered = pyqtSignal(name="next_testcase_triggered")
    prev_student_triggered = pyqtSignal(name="prev_testcase_triggered")

    def __init__(self, parent: QObject = None):
        """学生の表示欄と前後移動ボタンを構築する。"""
        super().__init__(parent)
        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        """既存の学生ヘッダーを配置する。"""
        self.setFixedHeight(50)
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._b_prev = PageButton(self, text="< (A)")
        layout.addWidget(self._b_prev)
        layout.addStretch(1)

        self._l_student_id = QLabel(self)
        self._l_student_id.setFixedWidth(150)
        self._l_student_id.setFont(
            get_font(monospace=True, large=True, bold=True))
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
        """学生移動ボタンのシグナルを転送する。"""
        self._b_prev.clicked.connect(self.prev_student_triggered)
        self._b_next.clicked.connect(self.next_student_triggered)

    def set_data(self, student: Student | None) -> None:
        """学生名を表示し、未選択時には空欄にする。"""
        if student is None:
            self._l_student_id.setText("")
            self._l_student_name.setText("")
        else:
            self._l_student_id.setText(str(student.student_id))
            self._l_student_name.setText(student.name)


class MarkTestCaseControlWidget(QWidget):
    """現在のテストケースを表示し、前後移動の操作を通知する。"""

    next_testcase_triggered = pyqtSignal(name="next_testcase_triggered")
    prev_testcase_triggered = pyqtSignal(name="prev_testcase_triggered")

    def __init__(self, parent: QObject = None):
        """テストケースの表示欄と移動ボタンを構築する。"""
        super().__init__(parent)
        self._testcase_id: TestCaseID | None = None
        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        """既存のテストケースヘッダーを配置する。"""
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
        """テストケース移動ボタンのシグナルを転送する。"""
        self._b_prev.clicked.connect(self.prev_testcase_triggered)
        self._b_next.clicked.connect(self.next_testcase_triggered)

    def set_data(self, testcase_id: TestCaseID | None):
        """選択したテストケースを表示する。"""
        self._testcase_id = testcase_id
        if self._testcase_id is None:
            self._l_testcase_id.setText("")
        else:
            self._l_testcase_id.setText(str(testcase_id))


@dataclass
class MarkDialogState:
    # ダイアログの表示状態を表す

    student_id: StudentID | None = None  # 現在表示中の学籍番号 [^]
    testcase_id: TestCaseID | None = None  # 現在表示中のテストケースID [^]
    file_id: FileID | None = None  # 現在表示中のファイルID [^]
    # ^: Noneは未選択（表示がない状態）を表す


class MarkDialogStateCreator:
    """現在の表示状態と移動操作から次の表示状態を生成する。"""

    def __init__(
        self,
        *,
        state: MarkDialogState,
        student_ids: list[StudentID],
        testcase_ids: list[TestCaseID],
        student_mark_view_data_get_test_result_usecase: StudentMarkViewDataGetTestResultUseCase,
    ):
        """現在の状態、移動対象の一覧、出力ファイル取得処理を受け取る。"""
        self._state = state
        self._student_ids = student_ids
        self._testcase_ids = testcase_ids
        self._student_mark_view_data_get_test_result_usecase = (
            student_mark_view_data_get_test_result_usecase
        )

    @property
    def _file_ids_by_testcase(self) -> dict[TestCaseID, list[FileID]]:
        """各テストケースの出力ファイル一覧を現在の学生から取得する。"""
        if not self._student_ids:
            return {}
        if not self._testcase_ids:
            return {}
        if self._state.student_id is None:
            return {}
        file_ids_by_testcase = {}
        for testcase_id in self._testcase_ids:
            view_data = self._student_mark_view_data_get_test_result_usecase.execute(
                student_id=self._state.student_id,
                testcase_id=testcase_id,
            )
            if view_data.is_success:
                file_ids_by_testcase[testcase_id] = list(
                    view_data.output_and_results.file_ids
                )
            else:
                file_ids_by_testcase[testcase_id] = []
        return file_ids_by_testcase

    def __create_file_id_field(self, new_testcase_id: TestCaseID | None) -> FileID | None:
        """元のファイル選択を維持し、初回のみ先頭のファイルを選ぶ。"""
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
        """指定テストケースを選択した状態を生成する。"""
        if self._state.student_id is None:
            if self._student_ids:
                new_student_id = self._student_ids[0]
            else:
                new_student_id = None
        else:
            new_student_id = self._state.student_id
        return MarkDialogState(
            student_id=new_student_id,
            testcase_id=testcase_id,
            file_id=self.__create_file_id_field(testcase_id),
        )

    def create_state_by_student_id(self, student_id: StudentID) -> MarkDialogState:
        """指定学生を選択した状態を生成する。"""
        if self._state.testcase_id is None:
            if self._testcase_ids:
                new_testcase_id = self._testcase_ids[0]
            else:
                new_testcase_id = None
        else:
            new_testcase_id = self._state.testcase_id
        return MarkDialogState(
            student_id=student_id,
            testcase_id=new_testcase_id,
            file_id=self.__create_file_id_field(new_testcase_id),
        )

    def create_state_of_next_testcase(self, *, delta=1) -> MarkDialogState:
        """隣接するテストケースへ移動した状態を生成する。"""
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
        """前のテストケースへ移動した状態を生成する。"""
        return self.create_state_of_next_testcase(delta=-1)

    def create_state_of_first_student(self) -> MarkDialogState:
        """先頭の学生を選択した状態を生成する。"""
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
        """隣接する学生へ移動した状態を生成する。"""
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
        """前の学生へ移動した状態を生成する。"""
        return self.create_state_of_next_student(delta=-1)

    def create_state_of_next_file(self, *, delta=1) -> MarkDialogState:
        """隣接する出力ファイルへ移動した状態を生成する。"""
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
        """前の出力ファイルへ移動した状態を生成する。"""
        return self.create_state_of_next_file(delta=-1)


class MarkDialog(QDialog):
    """採点内容を表示し、既存の入力・保存・画面移動を制御する。"""

    _logger = create_logger()

    def __init__(
        self,
        parent: QObject = None,
        *,
        global_settings_get_usecase: GlobalSettingsGetUseCase,
        student_list_id_usecase: StudentListIDUseCase,
        testcase_config_list_id_usecase: TestCaseListIDUseCase,
        student_mark_view_data_get_mark_summary_usecase: StudentMarkViewDataGetMarkSummaryUseCase,
        student_mark_view_data_get_test_result_usecase: StudentMarkViewDataGetTestResultUseCase,
        student_source_code_get_usecase: StudentSourceCodeGetUseCase,
        student_mark_get_usecase: StudentMarkGetUseCase,
        student_mark_put_usecase: StudentMarkPutUseCase,
    ):
        """依存関係を受け取り、画面部品と初期状態を構築する。"""
        super().__init__(parent)
        self._global_settings_get_usecase = global_settings_get_usecase
        self._student_list_id_usecase = student_list_id_usecase
        self._testcase_config_list_id_usecase = testcase_config_list_id_usecase
        self._student_mark_view_data_get_mark_summary_usecase = (
            student_mark_view_data_get_mark_summary_usecase
        )
        self._student_mark_view_data_get_test_result_usecase = (
            student_mark_view_data_get_test_result_usecase
        )
        self._student_source_code_get_usecase = student_source_code_get_usecase
        self._student_mark_get_usecase = student_mark_get_usecase
        self._student_mark_put_usecase = student_mark_put_usecase

        self._student_ids: list[StudentID] = self._student_list_id_usecase.execute(
        )
        self._testcase_ids: list[TestCaseID] = self._testcase_config_list_id_usecase.execute(
        )
        self._state = MarkDialogState()

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        """現行の画面構成を変更せずに各Widgetを配置する。"""
        self.setWindowTitle("採点")
        self.setModal(True)
        self.resize(1300, 700)
        self.installEventFilter(self)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout_middle = QHBoxLayout()
        layout.addLayout(layout_middle)

        layout_middle_left = QVBoxLayout()
        layout_middle.addLayout(layout_middle_left)

        self._w_student_control = MarkStudentControlWidget(self)
        layout_middle_left.addWidget(self._w_student_control)

        layout_middle_left_inner = QHBoxLayout()
        layout_middle_left_inner.setContentsMargins(0, 0, 0, 0)
        layout_middle_left.addLayout(layout_middle_left_inner)

        self._w_source_code_view = StudentSourceCodeView(
            self,
            global_settings_get_usecase=self._global_settings_get_usecase,
        )
        layout_middle_left_inner.addWidget(self._w_source_code_view)

        self._w_testcase_test_result_view = TestCaseTestResultViewWidget(
            self,
            global_settings_get_usecase=self._global_settings_get_usecase,
        )
        layout_middle_left_inner.addWidget(self._w_testcase_test_result_view)

        layout_middle_right = QVBoxLayout()
        layout_middle.addLayout(layout_middle_right)

        self._w_testcase_control = MarkTestCaseControlWidget(self)
        self._w_testcase_control.setFixedWidth(300)
        layout_middle_right.addWidget(self._w_testcase_control)

        self._w_test_result_list = TestCaseTestResultListWidget(self)
        self._w_test_result_list.setFixedWidth(300)
        self._w_test_result_list.setFocusPolicy(Qt.NoFocus)
        layout_middle_right.addWidget(self._w_test_result_list)

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
        """各Widgetの操作を既存のハンドラに接続する。"""
        self._w_test_result_list.testcase_clicked.connect(
            self.__w_test_result_list_testcase_clicked
        )
        self._w_testcase_control.next_testcase_triggered.connect(
            self.__w_testcase_control_next_testcase_triggered
        )
        self._w_testcase_control.prev_testcase_triggered.connect(
            self.__w_testcase_control_prev_testcase_triggered
        )
        self._w_student_control.next_student_triggered.connect(
            self.__w_student_control_next_student_triggered
        )
        self._w_student_control.prev_student_triggered.connect(
            self.__w_student_control_prev_student_triggered
        )
        self._w_testcase_test_result_view.selected_file_id_changed.connect(
            self.__w_test_result_view_placeholder_selected_file_id_changed
        )
        self._w_mark_score.key_pressed.connect(self.__w_mark_score_key_pressed)
        self._b_help.clicked.connect(self.__b_help_clicked)

    def __get_student_mark_summary_view_data(
        self, student_id: StudentID,
    ) -> StudentMarkSummaryViewData:
        """学生の採点画面向け概要を取得する。"""
        return self._student_mark_view_data_get_mark_summary_usecase.execute(student_id)

    def __get_student_testcase_test_result_view_data(
        self, student_id: StudentID, testcase_id: TestCaseID,
    ) -> AbstractStudentTestCaseTestResultViewData:
        """学生の指定テストケースの実行結果を取得する。"""
        return self._student_mark_view_data_get_test_result_usecase.execute(
            student_id, testcase_id
        )

    def __get_student_source_code(self, student_id: StudentID) -> SourceCode | None:
        """学生のソースコードを取得する。"""
        return self._student_source_code_get_usecase.execute(student_id)

    def __get_student_mark(self, student_id: StudentID) -> StudentMark:
        """学生の採点結果を取得する。"""
        return self._student_mark_get_usecase.execute(student_id)

    def __put_student_mark(self, student_mark: StudentMark) -> None:
        """学生の採点結果を保存する。"""
        self._student_mark_put_usecase.execute(student_mark)

    @property
    def states(self) -> MarkDialogStateCreator:
        """現在の状態を基準に移動先を計算する。"""
        return MarkDialogStateCreator(
            state=self._state,
            student_ids=self._student_ids,
            testcase_ids=self._testcase_ids,
            student_mark_view_data_get_test_result_usecase=(
                self._student_mark_view_data_get_test_result_usecase
            ),
        )

    def __reflect_state(self):
        """従来と同じ順序で各領域の表示内容を更新する。"""
        self._update_student_header()
        self._update_testcase_header()
        self._update_source_and_test_result()
        self._update_testcase_list()
        self._update_score_editor()

    def _update_student_header(self) -> None:
        """学生の学籍番号と名前を更新する。"""
        if self._state.student_id is None:
            self._w_student_control.set_data(None)
        else:
            self._w_student_control.set_data(
                student=self.__get_student_mark_summary_view_data(
                    self._state.student_id
                ).student,
            )

    def _update_testcase_header(self) -> None:
        """テストケースヘッダーを更新する。"""
        if self._state.student_id is None:
            self._w_testcase_control.set_data(testcase_id=None)
        else:
            self._w_testcase_control.set_data(
                testcase_id=self._state.testcase_id)

    def _update_source_and_test_result(self) -> None:
        """ソースコードと現在のテスト結果を表示する。"""
        if self._state.student_id is None:
            source_code = None
        else:
            source_code = self.__get_student_source_code(
                self._state.student_id)

        # ファイル未選択時とテスト結果が取得できない場合を従来どおり区別する。
        no_selection = object()
        if self._state.student_id is None:
            data_of_testcase_test_result_view = "生徒が選択されていません"
            selected_file_id = no_selection
        elif self._state.testcase_id is None:
            data_of_testcase_test_result_view = "テストケースが選択されていません"
            selected_file_id = no_selection
        else:
            summary_view_data = self.__get_student_mark_summary_view_data(
                self._state.student_id
            )
            if summary_view_data.is_ready:
                testcase_result_view_data = self.__get_student_testcase_test_result_view_data(
                    student_id=self._state.student_id,
                    testcase_id=self._state.testcase_id,
                )
                data_of_testcase_test_result_view = testcase_result_view_data
                selected_file_id = self._state.file_id
            else:
                data_of_testcase_test_result_view = summary_view_data.reason
                selected_file_id = no_selection

        self._w_testcase_test_result_view.set_data(
            data=data_of_testcase_test_result_view
        )
        if selected_file_id is not no_selection:
            self._w_testcase_test_result_view.set_selected(selected_file_id)
        self._w_source_code_view.set_data(
            source_code_text=source_code.text if source_code is not None else None,
        )

    def _update_testcase_list(self) -> None:
        """表示学生の全テストケースの結果一覧を更新する。"""
        if self._state.student_id is None:
            self._w_test_result_list.set_data(None)
        else:
            self._w_test_result_list.set_data(
                [
                    self.__get_student_testcase_test_result_view_data(
                        student_id=self._state.student_id,
                        testcase_id=testcase_id,
                    )
                    for testcase_id in self._testcase_ids
                ]
            )
            self._w_test_result_list.set_selected_id(self._state.testcase_id)

    def _update_score_editor(self) -> None:
        """選択学生の点数欄を読み込む。"""
        if self._state.student_id is None:
            self._w_mark_score.set_data(None)
        else:
            self._w_mark_score.set_data(
                self.__get_student_mark(self._state.student_id)
            )

    def __save_data(self):
        """点数欄が変更された場合に限り現在の学生へ保存する。"""
        if not self._w_mark_score.is_modified():
            return
        student_mark = self._w_mark_score.get_data()
        if student_mark is not None:
            self._logger.info(f"student mark saved\n{student_mark}")
            assert student_mark.student_id == self._state.student_id
            self.__put_student_mark(student_mark)

    def set_state(self, state: MarkDialogState):
        """状態が変わる場合のみ、点数を保存してから表示を更新する。"""
        if self._state == state:
            return
        self.__save_data()
        self._state = state
        self.__reflect_state()

    @pyqtSlot(TestCaseID)
    def __w_test_result_list_testcase_clicked(self, testcase_id: TestCaseID):
        """一覧でクリックされたテストケースへ移動する。"""
        new_state = self.states.create_state_by_testcase_id(testcase_id)
        self.set_state(new_state)

    @pyqtSlot()
    def __w_testcase_control_next_testcase_triggered(self):
        """次のテストケースへ移動する。"""
        new_state = self.states.create_state_of_next_testcase()
        self.set_state(new_state)

    @pyqtSlot()
    def __w_testcase_control_prev_testcase_triggered(self):
        """前のテストケースへ移動する。"""
        new_state = self.states.create_state_of_prev_testcase()
        self.set_state(new_state)

    @pyqtSlot()
    def __w_student_control_next_student_triggered(self):
        """次の学生へ移動する。"""
        new_state = self.states.create_state_of_next_student()
        self.set_state(new_state)

    @pyqtSlot()
    def __w_student_control_prev_student_triggered(self):
        """前の学生へ移動する。"""
        new_state = self.states.create_state_of_prev_student()
        self.set_state(new_state)

    @pyqtSlot(FileID)
    def __w_test_result_view_placeholder_selected_file_id_changed(
        self, file_id: FileID,
    ):
        """ファイル選択の変更を現在の状態へ反映する。"""
        self._state.file_id = file_id

    @pyqtSlot(QKeyEvent)
    def __w_mark_score_key_pressed(self, evt: QKeyEvent):
        """点数欄で押されたキーを共通の操作処理へ渡す。"""
        self.__on_key_press(evt)

    @pyqtSlot()
    def __b_help_clicked(self):
        """既存のショートカット一覧を表示する。"""
        dialog = MarkHelpDialog()
        dialog.exec_()

    def __on_key_press(self, evt: QKeyEvent):
        """既存のショートカットと遷移先を維持してキーを処理する。"""
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
            self.set_state(new_state)

    def eventFilter(self, target: QObject, evt: QEvent):
        """ダイアログ内のキー操作を従来どおり横取りする。"""
        if evt.type() == QEvent.KeyPress:
            assert isinstance(evt, QKeyEvent)
            self.__on_key_press(evt)
            return True
        return False

    def closeEvent(self, evt: QCloseEvent):
        """閉じる前に編集中の採点結果を保存する。"""
        self.__save_data()
