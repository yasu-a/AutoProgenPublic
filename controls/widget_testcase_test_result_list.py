from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem

from controls.widget_test_summary_indicator import TestCaseTestSummaryIndicatorWidget
from domain.models.values import TestCaseID
from res.fonts import get_font
from usecases.dto.student_mark_view_data import AbstractStudentTestCaseTestResultViewData


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
        layout_root.addLayout(layout_title)

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
        layout_detail.addWidget(self._l_detail)

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, student_testcase_test_summary: AbstractStudentTestCaseTestResultViewData):
        assert student_testcase_test_summary is not None

        # テストケース名
        self._l_testcase_name.setText(str(student_testcase_test_summary.testcase_id))
        # インジケータ
        self._l_indicator.set_data(student_testcase_test_summary.state)
        # 詳細テキスト
        self._l_detail.setText(student_testcase_test_summary.title_text)

    @pyqtSlot(bool)
    def set_selected(self, is_selected: bool):
        if is_selected:
            self._l_testcase_name.setStyleSheet(
                "color: white;"
                "background-color: #0033aa;"
                "border-radius: 4px;"
                "padding: 2px;"
            )
        else:
            self._l_testcase_name.setStyleSheet(
                "border-radius: 4px;"
                "padding: 2px;"
            )


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
