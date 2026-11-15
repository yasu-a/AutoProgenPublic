import itertools
from copy import deepcopy

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from autoprogen.control.dialog_testcase_config_edit import TestCaseConfigEditDialog
from autoprogen.control.dialog_settings_edit import AbstractSettingsEditDialog
from autoprogen.control.widget_button_box import ButtonBox
from autoprogen.domain.model.testcase_config import TestCaseConfig
from autoprogen.domain.model.value import TestCaseID
from autoprogen.usecase.global_settings import GlobalSettingsGetUseCase
from autoprogen.usecase.testcase_config import TestCaseDeleteUseCase, TestCaseGetUseCase, TestCasePutUseCase
from autoprogen.usecase.testcase_list_edit import TestCaseListSummaryUseCase
from autoprogen.usecase.test_test_stage import TestTestStageUseCase


class TestCaseListWidget(QListWidget):
    """テストケース概要の一覧を表示して選択を通知する。"""

    testcase_item_double_clicked = pyqtSignal(TestCaseID, name="testcase_item_double_clicked")

    def __init__(self, parent: QObject = None):
        """空のテストケース一覧を初期化する。"""
        super().__init__(parent)

        self._testcase_configs: list[TestCaseConfig] = []

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        """一覧固有の表示設定を初期化する。"""
        pass

    def _init_signals(self):
        """ダブルクリックをテストケースIDの通知へ接続する。"""
        # noinspection PyUnresolvedReferences
        self.doubleClicked.connect(self.__double_clicked)

    def get_selected_testcase_id(self) -> TestCaseID | None:
        """一件だけ選択されている場合にテストケースIDを返す。"""
        indexes = self.selectedIndexes()
        if len(indexes) != 1:
            return None
        i_row = indexes[0].row()
        return self._testcase_configs[i_row].testcase_id

    def __double_clicked(self):
        """選択中のテストケースIDをダブルクリック通知へ変換する。"""
        testcase_id = self.get_selected_testcase_id()
        if testcase_id is None:
            return
        self.testcase_item_double_clicked.emit(testcase_id)

    def set_data(self, data: list[TestCaseConfig]) -> None:
        """テストケース設定を受け取り、一覧表示を置き換える。"""
        self.clear()
        self._testcase_configs = deepcopy(data)
        for testcase_config in self._testcase_configs:
            self.addItem(str(testcase_config.testcase_id))

    def get_data(self) -> list[TestCaseConfig]:
        """現在表示しているテストケース設定を返す。"""
        return deepcopy(self._testcase_configs)


class TestCaseListEditWidget(QWidget):
    """テストケース概要の一覧と編集操作を提供する。"""

    testcase_modified = pyqtSignal(name="testcase_modified")

    def __init__(
            self,
            parent: QObject = None,
            *,
            global_settings_get_usecase: GlobalSettingsGetUseCase,
            test_test_stage_usecase: TestTestStageUseCase,
    ):
        super().__init__(parent)
        self._global_settings_get_usecase = global_settings_get_usecase
        self._test_test_stage_usecase = test_test_stage_usecase
        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        """テストケース一覧と操作ボタンを配置する。"""
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._w_testcase_list = TestCaseListWidget(self)  # type: ignore
        layout.addWidget(self._w_testcase_list)

        self._w_buttons = ButtonBox(self, orientation=Qt.Vertical)
        self._w_buttons.add_button("新規作成", "add")
        self._w_buttons.add_button("編集", "edit")
        self._w_buttons.add_button("コピー", "copy")
        self._w_buttons.add_button("削除", "delete")
        layout.addWidget(self._w_buttons)

    def _init_signals(self):
        """一覧操作と変更後の再読み込みを接続する。"""
        self._w_buttons.triggered.connect(self.__w_buttons_triggered)
        self._w_testcase_list.testcase_item_double_clicked.connect(self.dispatch_action_edit)

    def set_data(self, data: list[TestCaseConfig]) -> None:
        """編集対象のテストケース設定を一覧へ設定する。"""
        self._w_testcase_list.set_data(data)

    def get_data(self) -> list[TestCaseConfig]:
        """現在の一覧に含まれるテストケース設定を返す。"""
        return self._w_testcase_list.get_data()

    def _create_new_name(self) -> str:
        """一時編集中の一覧と衝突しないテストケース名を生成する。"""
        testcase_ids = {config.testcase_id for config in self.get_data()}
        for number in itertools.count(1):
            testcase_id = TestCaseID(f"テストケース{number:02d}")
            if testcase_id not in testcase_ids:
                return str(testcase_id)
        raise AssertionError("unreachable")

    def _replace_config(self, updated: TestCaseConfig) -> None:
        """同じIDを持つ一時編集中のテストケース設定を置き換える。"""
        configs = self.get_data()
        for index, config in enumerate(configs):
            if config.testcase_id == updated.testcase_id:
                configs[index] = updated
                self.set_data(configs)
                self.testcase_modified.emit()
                return
        raise ValueError(f"テストケースが見つかりません: {updated.testcase_id!s}")

    @pyqtSlot()
    def dispatch_action_add(self):
        while True:
            testcase_name, ok = QInputDialog.getText(
                self,  # type: ignore
                "新しいテストケース",
                "新しいテストケースの名前を入力してください",
                text=self._create_new_name(),
            )
            if not ok:
                return
            testcase_name = testcase_name.strip()
            if not testcase_name:
                return
            testcase_id = TestCaseID(testcase_name)
            if any(config.testcase_id == testcase_id for config in self.get_data()):
                QMessageBox.critical(
                    self,  # type: ignore
                    "新しいテストケース",
                    f"{testcase_name}と同じ名前のテストケースが既に存在します",
                    buttons=QMessageBox.Ok,
                )
                continue
            configs = self.get_data()
            configs.append(TestCaseConfig.create_default(testcase_id))
            self.set_data(configs)
            break
        self.testcase_modified.emit()

    @pyqtSlot(TestCaseID)
    def dispatch_action_copy(self, testcase_id: TestCaseID):
        while True:
            new_testcase_name, ok = QInputDialog.getText(
                self,  # type: ignore
                f"{testcase_id!s}のコピー",
                "新しいテストケースの名前を入力してください",
                text=self._create_new_name(),
            )
            if not ok:
                return
            new_testcase_name = new_testcase_name.strip()
            if not new_testcase_name:
                return
            new_testcase_id = TestCaseID(new_testcase_name)
            configs = self.get_data()
            if any(config.testcase_id == new_testcase_id for config in configs):
                QMessageBox.critical(
                    self,  # type: ignore
                    f"{testcase_id!s}のコピー",
                    f"{new_testcase_name}と同じ名前のテストケースが既に存在します",
                    buttons=QMessageBox.Ok,
                )
                continue
            source = next(
                config
                for config in configs
                if config.testcase_id == testcase_id
            )
            configs.append(TestCaseConfig(
                testcase_id=new_testcase_id,
                execute_config=deepcopy(source.execute_config),
                test_config=deepcopy(source.test_config),
            ))
            self.set_data(configs)
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
        self.set_data([
            config
            for config in self.get_data()
            if config.testcase_id != testcase_id
        ])
        self.testcase_modified.emit()

    @pyqtSlot(TestCaseID)
    def dispatch_action_edit(self, testcase_id: TestCaseID):
        """テストケースを編集し、内容が変更された場合だけ一覧へ通知する。"""
        dialog = TestCaseConfigEditDialog(
            self,
            data=next(
                config
                for config in self.get_data()
                if config.testcase_id == testcase_id
            ),
            global_settings_get_usecase=self._global_settings_get_usecase,
            test_test_stage_usecase=self._test_test_stage_usecase,
        )
        if dialog.exec_() == QDialog.Accepted:
            self._replace_config(dialog.get_data())

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


class TestCaseListEditDialog(AbstractSettingsEditDialog[list[TestCaseConfig]]):
    """テストケース一覧を一時編集し、明示操作でまとめて保存する。"""

    def __init__(
            self,
            parent: QObject = None,
            *,
            global_settings_get_usecase: GlobalSettingsGetUseCase,
            test_test_stage_usecase: TestTestStageUseCase,
            testcase_list_summary_usecase: TestCaseListSummaryUseCase,
            testcase_delete_usecase: TestCaseDeleteUseCase,
            testcase_get_usecase: TestCaseGetUseCase,
            testcase_put_usecase: TestCasePutUseCase,
    ):
        super().__init__(parent)
        self._global_settings_get_usecase = global_settings_get_usecase
        self._test_test_stage_usecase = test_test_stage_usecase
        self._testcase_list_summary_usecase = testcase_list_summary_usecase
        self._testcase_delete_usecase = testcase_delete_usecase
        self._testcase_get_usecase = testcase_get_usecase
        self._testcase_put_usecase = testcase_put_usecase

        self._init_ui()

    def _set_data(self, data: list[TestCaseConfig]) -> None:
        """編集対象のテストケース設定を一覧Widgetへ設定する。"""
        self._w_testcase_edit.set_data(data)

    def get_data(self) -> list[TestCaseConfig]:
        """現在の一覧Widgetが保持するテストケース設定を返す。"""
        return self._w_testcase_edit.get_data()

    def save_data(self, data: list[TestCaseConfig]) -> None:
        """一時編集した一覧を既存のテストケース群へ反映する。"""
        existing_ids = {
            summary.testcase_id
            for summary in self._testcase_list_summary_usecase.execute()
        }
        current_ids = {config.testcase_id for config in data}

        # 一時一覧から削除されたテストケースを永続化先から削除する。
        for testcase_id in existing_ids - current_ids:
            self._testcase_delete_usecase.execute(testcase_id)

        # 新規作成・複製・編集された現在の一覧を保存する。
        for config in data:
            self._testcase_put_usecase.execute(config)

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("テストケースの編集")
        self.setModal(True)
        self.resize(400, 700)

        self._w_testcase_edit = TestCaseListEditWidget(
            self,  # type: ignore
            global_settings_get_usecase=self._global_settings_get_usecase,
            test_test_stage_usecase=self._test_test_stage_usecase,
        )
        self.content_layout.addWidget(self._w_testcase_edit)
        self.add_standard_buttons()
        summaries = self._testcase_list_summary_usecase.execute()
        self.set_data([
            self._testcase_get_usecase.execute(summary.testcase_id)
            for summary in summaries
        ])
