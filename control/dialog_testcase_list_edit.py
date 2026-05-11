from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from control.dialog_testcase_config_edit import TestCaseConfigEditDialog
from control.widget_button_box import ButtonBox
from domain.error import UseCaseError
from domain.model.value import TestCaseID
from usecase.global_settings import GlobalSettingsGetUseCase
from usecase.testcase_config import TestCaseDeleteUseCase, TestCaseGetUseCase, TestCasePutUseCase
from usecase.testcase_list_edit import TestCaseListSummaryUseCase, TestCaseCreateNewNameUseCase, TestCaseCreateUseCase, \
    TestCaseCopyUseCase
from usecase.test_test_stage import TestTestStageUseCase
from usecase.dto.testcase_list_edit import TestCaseListEditTestCaseSummary


class TestCaseListWidget(QListWidget):
    testcase_item_double_clicked = pyqtSignal(TestCaseID, name="testcase_item_double_clicked")

    def __init__(self, parent: QObject = None, *, testcase_list_summary_usecase: TestCaseListSummaryUseCase):
        super().__init__(parent)
        self._testcase_list_summary_usecase = testcase_list_summary_usecase

        self._testcase_config_summary_lst: list[TestCaseListEditTestCaseSummary] = []

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
        return self._testcase_config_summary_lst[i_row].testcase_id

    def __double_clicked(self):
        testcase_id = self.get_selected_testcase_id()
        if testcase_id is None:
            return
        self.testcase_item_double_clicked.emit(testcase_id)

    @pyqtSlot()
    def update_data(self):
        self.clear()
        self._testcase_config_summary_lst = self._testcase_list_summary_usecase.execute()
        for testcase_config_summary in self._testcase_config_summary_lst:
            self.addItem(testcase_config_summary.name)


class TestCaseListEditWidget(QWidget):
    testcase_modified = pyqtSignal(name="testcase_modified")

    def __init__(
            self,
            parent: QObject = None,
            *,
            global_settings_get_usecase: GlobalSettingsGetUseCase,
            test_test_stage_usecase: TestTestStageUseCase,
            testcase_list_summary_usecase: TestCaseListSummaryUseCase,
            testcase_create_new_name_usecase: TestCaseCreateNewNameUseCase,
            testcase_create_usecase: TestCaseCreateUseCase,
            testcase_copy_usecase: TestCaseCopyUseCase,
            testcase_delete_usecase: TestCaseDeleteUseCase,
            testcase_get_usecase: TestCaseGetUseCase,
            testcase_put_usecase: TestCasePutUseCase,
    ):
        super().__init__(parent)
        self._global_settings_get_usecase = global_settings_get_usecase
        self._test_test_stage_usecase = test_test_stage_usecase
        self._testcase_list_summary_usecase = testcase_list_summary_usecase
        self._testcase_create_new_name_usecase = testcase_create_new_name_usecase
        self._testcase_create_usecase = testcase_create_usecase
        self._testcase_copy_usecase = testcase_copy_usecase
        self._testcase_delete_usecase = testcase_delete_usecase
        self._testcase_get_usecase = testcase_get_usecase
        self._testcase_put_usecase = testcase_put_usecase

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._w_testcase_list = TestCaseListWidget(
            self,  # type: ignore
            testcase_list_summary_usecase=self._testcase_list_summary_usecase,
        )
        layout.addWidget(self._w_testcase_list)

        self._w_buttons = ButtonBox(self, orientation=Qt.Vertical)
        self._w_buttons.add_button("新規作成", "add")
        self._w_buttons.add_button("編集", "edit")
        self._w_buttons.add_button("コピー", "copy")
        self._w_buttons.add_button("削除", "delete")
        layout.addWidget(self._w_buttons)

    def _init_signals(self):
        self._w_buttons.triggered.connect(self.__w_buttons_triggered)
        self.testcase_modified.connect(self._w_testcase_list.update_data)
        self._w_testcase_list.testcase_item_double_clicked.connect(self.dispatch_action_edit)

    @pyqtSlot()
    def dispatch_action_add(self):
        while True:
            testcase_name, ok = QInputDialog.getText(
                self,  # type: ignore
                "新しいテストケース",
                "新しいテストケースの名前を入力してください",
                text=self._testcase_create_new_name_usecase.execute(),
            )
            if not ok:
                return
            testcase_name = testcase_name.strip()
            if not testcase_name:
                return
            try:
                self._testcase_create_usecase.execute(testcase_name)
            except UseCaseError:
                QMessageBox.critical(
                    self,  # type: ignore
                    "新しいテストケース",
                    f"{testcase_name}と同じ名前のテストケースが既に存在します",
                    buttons=QMessageBox.Ok,
                )
                continue
            else:
                break
        self.testcase_modified.emit()

    @pyqtSlot(TestCaseID)
    def dispatch_action_copy(self, testcase_id: TestCaseID):
        while True:
            new_testcase_name, ok = QInputDialog.getText(
                self,  # type: ignore
                f"{testcase_id!s}のコピー",
                "新しいテストケースの名前を入力してください",
                text=self._testcase_create_new_name_usecase.execute(),
            )
            if not ok:
                return
            new_testcase_name = new_testcase_name.strip()
            if not new_testcase_name:
                return
            try:
                self._testcase_copy_usecase.execute(
                    src_testcase_id=testcase_id,
                    new_testcase_name=new_testcase_name,
                )
            except UseCaseError:
                QMessageBox.critical(
                    self,  # type: ignore
                    f"{testcase_id!s}のコピー",
                    f"{new_testcase_name}と同じ名前のテストケースが既に存在します",
                    buttons=QMessageBox.Ok,
                )
                continue
            else:
                break
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
        self._testcase_delete_usecase.execute(testcase_id)
        self.testcase_modified.emit()

    @pyqtSlot(TestCaseID)
    def dispatch_action_edit(self, testcase_id: TestCaseID):
        dialog = TestCaseConfigEditDialog(
            self,
            testcase_id=testcase_id,
            global_settings_get_usecase=self._global_settings_get_usecase,
            test_test_stage_usecase=self._test_test_stage_usecase,
            testcase_get_usecase=self._testcase_get_usecase,
            testcase_put_usecase=self._testcase_put_usecase,
        )
        dialog.exec_()
        self.testcase_modified.emit()

    @pyqtSlot(str)
    def __w_buttons_triggered(self, name: str):
        if name == "add":
            self.dispatch_action_add()
        elif name == "copy":
            testcase_id = self._w_testcase_list.get_selected_testcase_id()
            if testcase_id is None:
                return
            self.dispatch_action_copy(testcase_id)
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
    def __init__(
            self,
            parent: QObject = None,
            *,
            global_settings_get_usecase: GlobalSettingsGetUseCase,
            test_test_stage_usecase: TestTestStageUseCase,
            testcase_list_summary_usecase: TestCaseListSummaryUseCase,
            testcase_create_new_name_usecase: TestCaseCreateNewNameUseCase,
            testcase_create_usecase: TestCaseCreateUseCase,
            testcase_copy_usecase: TestCaseCopyUseCase,
            testcase_delete_usecase: TestCaseDeleteUseCase,
            testcase_get_usecase: TestCaseGetUseCase,
            testcase_put_usecase: TestCasePutUseCase,
    ):
        super().__init__(parent)
        self._global_settings_get_usecase = global_settings_get_usecase
        self._test_test_stage_usecase = test_test_stage_usecase
        self._testcase_list_summary_usecase = testcase_list_summary_usecase
        self._testcase_create_new_name_usecase = testcase_create_new_name_usecase
        self._testcase_create_usecase = testcase_create_usecase
        self._testcase_copy_usecase = testcase_copy_usecase
        self._testcase_delete_usecase = testcase_delete_usecase
        self._testcase_get_usecase = testcase_get_usecase
        self._testcase_put_usecase = testcase_put_usecase

        self._init_ui()

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("テストケースの編集")
        self.setModal(True)
        self.resize(400, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_testcase_edit = TestCaseListEditWidget(
            self,  # type: ignore
            global_settings_get_usecase=self._global_settings_get_usecase,
            test_test_stage_usecase=self._test_test_stage_usecase,
            testcase_list_summary_usecase=self._testcase_list_summary_usecase,
            testcase_create_new_name_usecase=self._testcase_create_new_name_usecase,
            testcase_create_usecase=self._testcase_create_usecase,
            testcase_copy_usecase=self._testcase_copy_usecase,
            testcase_delete_usecase=self._testcase_delete_usecase,
            testcase_get_usecase=self._testcase_get_usecase,
            testcase_put_usecase=self._testcase_put_usecase,
        )
        layout.addWidget(self._w_testcase_edit)
