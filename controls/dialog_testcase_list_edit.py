from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from application.dependency.services import get_testcase_edit_service
from controls.dialog_testcase_config_edit import TestCaseConfigEditDialog
from controls.widget_button_box import ButtonBox
from domain.models.values import TestCaseID


class TestCaseListWidget(QListWidget):
    testcase_item_double_clicked = pyqtSignal(TestCaseID, name="testcase_item_double_clicked")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._current_testcase_id_lst: list[TestCaseID] = []

        self._init_ui()
        self._init_signals()

        self.update_data()

    def _init_ui(self):
        pass

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self.doubleClicked.connect(self.__double_clicked)

    def get_selected_testcase_id(self) -> TestCaseID | None:
        indexes = self.selectedIndexes()
        if len(indexes) != 1:
            return None
        i_row = indexes[0].row()
        return self._current_testcase_id_lst[i_row]

    def __double_clicked(self):
        testcase_id = self.get_selected_testcase_id()
        if testcase_id is None:
            return
        self.testcase_item_double_clicked.emit(testcase_id)

    @pyqtSlot()
    def update_data(self):
        self.clear()
        self._current_testcase_id_lst = get_testcase_edit_service().list_testcase_ids()
        for testcase_id in self._current_testcase_id_lst:
            summary = get_testcase_edit_service().get_summary(testcase_id)
            self.addItem(summary.name)


class TestCaseListEditWidget(QWidget):
    testcase_modified = pyqtSignal(name="testcase_modified")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._w_testcase_list = TestCaseListWidget(self)  # type: ignore
        layout.addWidget(self._w_testcase_list)

        self._w_buttons = ButtonBox(self, orientation=Qt.Vertical)
        self._w_buttons.add_button("新規作成", "add")
        self._w_buttons.add_button("編集", "edit")
        self._w_buttons.add_button("削除", "delete")
        layout.addWidget(self._w_buttons)

    def _init_signals(self):
        self._w_buttons.triggered.connect(self.__w_buttons_triggered)
        self.testcase_modified.connect(self._w_testcase_list.update_data)
        self._w_testcase_list.testcase_item_double_clicked.connect(self.dispatch_action_edit)

    @pyqtSlot()
    def dispatch_action_add(self):
        testcase_name, ok = QInputDialog.getText(
            self,  # type: ignore
            "新しいテストケース",
            "新しいテストケースの名前を入力してください",
            text=str(get_testcase_edit_service().create_new_testcase_id()),
        )
        if not ok:
            return
        testcase_name = testcase_name.strip()
        if not testcase_name:
            return
        new_testcase_id = TestCaseID(testcase_name)
        get_testcase_edit_service().create(testcase_id=new_testcase_id)
        self.testcase_modified.emit()

    @pyqtSlot(TestCaseID)
    def dispatch_action_delete(self, testcase_id: TestCaseID):
        res = QMessageBox.warning(
            self,  # type: ignore
            "テストケースの削除",
            f"テストケース「{testcase_id!s}」を削除しますか？",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if res != QMessageBox.Yes:
            return
        get_testcase_edit_service().delete(testcase_id=testcase_id)
        self.testcase_modified.emit()

    @pyqtSlot(TestCaseID)
    def dispatch_action_edit(self, testcase_id: TestCaseID):
        dialog = TestCaseConfigEditDialog(self, testcase_id=testcase_id)
        dialog.exec_()
        self.testcase_modified.emit()

    @pyqtSlot(str)
    def __w_buttons_triggered(self, name: str):
        if name == "add":
            self.dispatch_action_add()
        elif name == "delete":
            testcase_id = self._w_testcase_list.get_selected_testcase_id()
            if testcase_id is None:
                return
            self.dispatch_action_delete(testcase_id)
        elif name == "edit":
            testcase_id = self._w_testcase_list.get_selected_testcase_id()
            if testcase_id is None:
                return
            self.dispatch_action_edit(testcase_id)
        else:
            assert False, name


class TestCaseListEditDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("テストケースの編集")
        self.setModal(True)
        self.resize(400, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_testcase_edit = TestCaseListEditWidget(self)  # type: ignore
        layout.addWidget(self._w_testcase_edit)
