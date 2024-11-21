from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QPlainTextEdit

from controls.widget_testcase_result_otuput_file_view import TestCaseResultOutputFileViewWidget
from domain.models.student_stage_result import TestResultOutputFileMapping
from domain.models.values import FileID, SpecialFileType
from res.fonts import get_font
from res.icons import get_icon
from usecases.dto.student_mark_view_data import AbstractStudentTestCaseTestResultViewData


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
                    title = "標準出力"
                    icon = get_icon("console")
                elif file_id.special_file_type == SpecialFileType.STDIN:
                    title = "標準入力"
                    icon = get_icon("console")
                else:
                    assert False, file_id.special_file_type
            else:
                title = str(file_id.deployment_relative_path)
                icon = get_icon("article")

            w = TestCaseResultOutputFileViewWidget(self)
            w.set_data(output_file_entry)
            self._w_file_tab.addTab(w, icon, title)
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


class TestCaseTestResultViewWidget(QWidget):
    selected_file_id_changed = pyqtSignal(FileID, name="selected_file_id_changed")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__w: TestCaseValidTestResultViewWidget | TestCaseInvalidTestResultViewWidget | None \
            = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def _init_signals(self):
        pass

    def __set_widget(self, w: QWidget) -> None:
        # remove widget
        while self.layout().count() > 0:
            self.layout().takeAt(0).widget().deleteLater()
        self.__w = None

        # set widget w
        self.layout().addWidget(w)
        self.__w = w

        # connect signals
        if isinstance(self.__w, TestCaseValidTestResultViewWidget):
            # noinspection PyUnresolvedReferences
            self.__w.selected_file_id_changed.connect(self.selected_file_id_changed)

    def __get_widget(self) -> QWidget | None:
        return self.__w

    def set_data(self, data: AbstractStudentTestCaseTestResultViewData | str) -> None:
        # data: str - エラーメッセージ
        if isinstance(data, AbstractStudentTestCaseTestResultViewData):
            if data.is_success:
                # 正常完了時用ウィジェットを設定
                w = TestCaseValidTestResultViewWidget()
                w.set_data(test_result_output_files=data.output_and_results)
                self.__set_widget(w)
            else:
                # エラー用ウィジェットを設定
                w = TestCaseInvalidTestResultViewWidget()
                w.set_data(detailed_reason=data.detailed_reason)
                self.__set_widget(w)
        elif isinstance(data, str):
            # エラー用ウィジェットを設定
            w = TestCaseInvalidTestResultViewWidget()
            w.set_data(detailed_reason=data)
            self.__set_widget(w)
        else:
            assert False  # invalid call arguments passed

    def set_selected(self, file_id_to_select: FileID | None) -> None:
        w = self.__get_widget()
        if not isinstance(w, TestCaseValidTestResultViewWidget):
            return
        w.set_selected(file_id_to_select)
