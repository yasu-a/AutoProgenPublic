from PyQt5.QtCore import QObject, pyqtSlot, Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog, QListWidget, QWidget, QHBoxLayout, QLabel, \
    QListWidgetItem

from app_logging import create_logger
from application.dependency import get_mark_snapshot_service
from domain.models.result_test import TestCaseTestResult, TestCaseTestResultSet
from domain.models.values import StudentID, TestCaseID
from dto.mark import StudentMarkSnapshot
from fonts import font


class MarkStudentListItemWidget(QWidget):
    # 採点ダイアログの生徒リストの項目
    # 生徒が選択中かどうか・学籍番号・名前・ステータス(点数 or 未採点 or 再実行が必要）を表示する

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

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
    def set_data(self, student_mark_snapshot: StudentMarkSnapshot):
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
            self._l_score.setText("未採点")
            set_background_color("lightgray")
        # ステータス
        if student_mark_snapshot.is_rerun_required:
            self._l_status.setText("再実行が必要")
            set_background_color("orange")
        elif student_mark_snapshot.is_markable:
            self._l_status.setText("")
        else:
            self._l_status.setText("エラー")
            self._l_status.setToolTip(student_mark_snapshot.detailed_reason)
            set_background_color("red")

    @pyqtSlot(bool)
    def set_selected(self, is_selected: bool):
        if is_selected:
            self._l_selected.setText("●")
        else:
            self._l_selected.setText("")
        # TODO: not working:
        # for label in self.layout().findChildren(QLabel):
        #     assert isinstance(label, QLabel)
        #     if is_selected:
        #         label.setStyleSheet("font-weight: bold")
        #     else:
        #         label.setStyleSheet("font-weight: normal")

    def is_selected(self) -> bool:
        return bool(self._l_selected.text())  # TODO: 内部状態で管理する


class MarkStudentListWidget(QListWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._w_item_mapping: dict[StudentID, MarkStudentListItemWidget] = {}

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        pass

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, student_snapshot_mapping: dict[StudentID, StudentMarkSnapshot]):
        for student_id, student_mark_snapshot in student_snapshot_mapping.items():
            # 項目のウィジェットを初期化
            item_widget = MarkStudentListItemWidget(self)
            item_widget.set_data(student_mark_snapshot)
            # リストに登録
            self._w_item_mapping[student_id] = item_widget
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
        self.setMinimumWidth(self.sizeHintForColumn(0) + 20)

    @pyqtSlot(StudentID)
    def set_selected_id(self, student_id_to_select: StudentID):
        for student_id, item_widget in self._w_item_mapping.items():
            if student_id == student_id_to_select:
                item_widget.set_selected(True)
            else:
                item_widget.set_selected(False)

    def get_selected_id(self) -> StudentID:
        for student_id, item_widget in self._w_item_mapping.items():
            if item_widget.is_selected():
                return student_id
        assert False, "No selection found"


class MarkResultTestCaseListItemWidget(QWidget):
    # テスト結果のテストケースのリストの項目
    # 選択中かどうか・テストケース名・テスト結果インジケータ・詳細テキストを表示する

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

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

        self._l_testcase_name = QLabel(self)
        self._l_testcase_name.setFixedWidth(200)
        self._l_testcase_name.setFont(font(monospace=False, small=True))
        layout.addWidget(self._l_testcase_name)

        # TODO: インジケータ実装
        # TODO: 詳細テキスト実装

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, testcase_test_result: TestCaseTestResult):
        # 選択中かどうか
        self._l_selected.setText("")
        # テストケース名
        self._l_testcase_name.setText(str(testcase_test_result.testcase_id))

    @pyqtSlot(bool)
    def set_selected(self, is_selected: bool):
        if is_selected:
            self._l_selected.setText("●")
        else:
            self._l_selected.setText("")

    def is_selected(self):
        return bool(self._l_selected.text())  # TODO: 内部状態で管理する


class MarkResultTestCaseListWidget(QListWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._w_item_mapping: dict[TestCaseID, MarkResultTestCaseListItemWidget] = {}

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        pass

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, testcase_test_result_set: TestCaseTestResultSet):
        for test_result in testcase_test_result_set:
            # 項目のウィジェットを初期化
            item_widget = MarkResultTestCaseListItemWidget(self)
            item_widget.set_data(test_result)
            # リストに登録
            self._w_item_mapping[test_result.testcase_id] = item_widget
            # Qtのリスト項目を初期化
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            # リストに追加
            self.addItem(list_item)
            # 項目のウィジェットとQtのリスト項目を関連付ける
            self.setItemWidget(list_item, item_widget)
        # 幅を内容に合わせて調整
        self.setMinimumWidth(self.sizeHintForColumn(0) + 20)

    @pyqtSlot(TestCaseID)
    def set_selected_id(self, testcase_id_to_select: TestCaseID):
        for testcase_id, item_widget in self._w_item_mapping.items():
            if testcase_id == testcase_id_to_select:
                item_widget.set_selected(True)
            else:
                item_widget.set_selected(False)

    def get_selected_id(self) -> TestCaseID:
        for testcase_id, item_widget in self._w_item_mapping.items():
            if item_widget.is_selected():
                return testcase_id
        assert False, "No selection found"


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

    def _init_ui(self):
        self.setWindowTitle(f"採点")
        self.setModal(True)
        self.resize(1200, 700)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._w_student_list = MarkStudentListWidget(self)
        self._w_student_list.set_data(self._project_mark_snapshot.student_snapshot_mapping)
        layout.addWidget(self._w_student_list)

        self._w_testcase_result_list = MarkResultTestCaseListWidget(self)
        layout.addWidget(self._w_testcase_result_list)

        layout.addStretch(1)

        self.set_selected_student(self._project_mark_snapshot.get_first_student_id())

    @pyqtSlot(StudentID)
    def set_selected_student(self, student_id: StudentID):
        self._w_student_list.set_selected_id(
            student_id_to_select=student_id,
        )
        self.set_selected_testcase(
            testcase_id=self._project_mark_snapshot.get_first_testcase_id(),
        )

    @pyqtSlot(TestCaseID)
    def set_selected_testcase(self, testcase_id: TestCaseID):
        current_student_id: StudentID = self._w_student_list.get_selected_id()
        student_snapshot = self._project_mark_snapshot.student_snapshot_mapping[current_student_id]
        self._w_testcase_result_list.set_data(
            testcase_test_result_set=student_snapshot.test_result.testcase_result_set,
        )
        self._w_testcase_result_list.set_selected_id(
            testcase_id_to_select=testcase_id,
        )

    def closeEvent(self, evt: QCloseEvent):
        # config = self._w_testcase_edit.get_data()
        # get_testcase_edit_service().set_config(
        #     testcase_id=self._testcase_id,
        #     config=config,
        # )
        pass
