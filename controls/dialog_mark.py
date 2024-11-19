from PyQt5.QtCore import QObject, pyqtSlot, Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QKeyEvent, QCloseEvent
from PyQt5.QtWidgets import QDialog, QWidget, QHBoxLayout, QLabel, \
    QVBoxLayout, QPushButton

from application.dependency.usecases import get_student_list_id_usecase, \
    get_student_mark_view_data_get_test_result_usecase, \
    get_student_mark_view_data_get_mark_summary_usecase, get_student_source_code_get_usecase, \
    get_testcase_config_list_id_usecase, get_student_mark_get_usecase, get_student_mark_put_usecase
from controls.dialog_mark_help import MarkHelpDialog
from controls.dto.dialog_mark import MarkDialogState
from controls.res.fonts import get_font
from controls.res.icons import get_icon
from controls.widget_mark_score_edit import MarkScoreEditWidget
from controls.widget_page_button import PageButton
from controls.widget_student_source_code_view import StudentSourceCodeViewWidget
from controls.widget_testcase_test_result_list import TestCaseTestResultListWidget
from controls.widget_testcase_test_result_view import TestCaseTestResultViewWidget
from domain.models.student import Student
from domain.models.student_mark import StudentMark
from domain.models.values import StudentID, TestCaseID, FileID
from usecases.dto.student_mark_view_data import AbstractStudentTestCaseTestResultViewData, \
    StudentMarkSummaryViewData
from utils.app_logging import create_logger


class MarkStudentControlWidget(QWidget):
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


class MarkTestCaseControlWidget(QWidget):
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


# TODO: アルゴリズム改善 アクション入力と現在の状態から次の状態を生成するステートマシンを表現するとわかりやすい？
# noinspection DuplicatedCode
class MarkDialogStateCreator:
    # アクションに応じて呼ばれたメソッド内でダイアログの現在の状態から次の状態を生成する

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
    # 採点画面

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

                # 上に表示する生徒の学籍番号と名前とボタン
                self._w_student_control = MarkStudentControlWidget(self)
                layout_middle_left.addWidget(self._w_student_control)

                if "middle-left-inner":
                    layout_middle_left_inner = QHBoxLayout()
                    layout_middle_left_inner.setContentsMargins(0, 0, 0, 0)
                    layout_middle_left.addLayout(layout_middle_left_inner)

                    self._w_source_code_view = StudentSourceCodeViewWidget(self)
                    layout_middle_left_inner.addWidget(self._w_source_code_view)

                    self._w_testcase_test_result_view \
                        = TestCaseTestResultViewWidget(self)
                    layout_middle_left_inner.addWidget(self._w_testcase_test_result_view)

            if "middle-right":
                layout_middle_right = QVBoxLayout()
                layout_middle.addLayout(layout_middle_right)

                self._w_testcase_control = MarkTestCaseControlWidget(self)
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
        self._w_testcase_test_result_view.selected_file_id_changed.connect(
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
            self._w_testcase_test_result_view.set_data(data="生徒が選択されていません")
        elif self._state.testcase_id is None:
            self._w_testcase_test_result_view.set_data(data="テストケースが選択されていません")
        else:
            summary_view_data = self.__get_student_mark_summary_view_data(self._state.student_id)
            if summary_view_data.is_ready:
                testcase_result_view_data = self.__get_student_testcase_test_result_view_data(
                    student_id=self._state.student_id,
                    testcase_id=self._state.testcase_id,
                )
                self._w_testcase_test_result_view.set_data(data=testcase_result_view_data)
                self._w_testcase_test_result_view.set_selected(self._state.file_id)
            else:
                self._w_testcase_test_result_view.set_data(
                    data=summary_view_data.reason,
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

    def set_state(self, state: MarkDialogState):
        if self._state == state:
            return
        self.__save_data()
        self._state = state
        self.__reflect_state()

    @pyqtSlot(TestCaseID)
    def __w_testcase_result_list_testcase_clicked(self, testcase_id: TestCaseID):
        new_state = self.states.create_state_by_testcase_id(testcase_id)
        self.set_state(new_state)

    @pyqtSlot()
    def __w_testcase_control_next_testcase_triggered(self):
        new_state = self.states.create_state_of_next_testcase()
        self.set_state(new_state)

    @pyqtSlot()
    def __w_testcase_control_prev_testcase_triggered(self):
        new_state = self.states.create_state_of_prev_testcase()
        self.set_state(new_state)

    @pyqtSlot()
    def __w_student_control_next_student_triggered(self):
        new_state = self.states.create_state_of_next_student()
        self.set_state(new_state)

    @pyqtSlot()
    def __w_student_control_prev_student_triggered(self):
        new_state = self.states.create_state_of_prev_student()
        self.set_state(new_state)

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
            self.set_state(new_state)

    def eventFilter(self, target: QObject, evt: QEvent):
        if evt.type() == QEvent.KeyPress:
            self.__on_key_press(evt)
            return True
        return False

    def closeEvent(self, evt: QCloseEvent):
        self.__save_data()
