# from dataclasses import dataclass
#
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# from PyQt5.QtWidgets import *
#
# import state
# from fonts import font
# from controls.gui_source_text import SourceTextEdit
# from controls.gui_testcase_result import TestCaseResultWidget
# from controls.gui_testcase_result_state import TestCaseResultStateIndicatorWidget
# from models.student import Student
# from models.testcase import TestCaseResultState, TestSessionResult, \
#     TestCaseResult
# from services.project import ProjectService
#
#
# # noinspection PyArgumentList
# class StudentMarkWidgetSignals(QObject):
#     request_next_testcase = pyqtSignal()
#     request_prev_testcase = pyqtSignal()
#     request_next_mark = pyqtSignal()
#     request_prev_mark = pyqtSignal()
#     show_shortcuts = pyqtSignal()
#
#
# @dataclass(slots=True, frozen=True)
# class _Data:
#     student: Student
#     active_target_number: int | None
#     active_testcase_order_index: int | None
#     progress_value: int
#     progress_total: int
#
#     def has_test_result(self) -> bool:
#         return self.student.test_result is not None
#
#     def has_active_session(self) -> bool:
#         if not self.has_test_result():
#             return False
#         if self.active_target_number is None:
#             return False
#         return self.active_target_number in self.student.test_result.test_session_results
#
#     @property
#     def active_session_result(self) -> TestSessionResult | None:
#         if not self.has_active_session():
#             return None
#         return self.student.test_result.test_session_results[self.active_target_number]
#
#     def is_active_session_success(self) -> bool:
#         if not self.has_active_session():
#             return False
#         return self.active_session_result.success
#
#     def get_target_number(self) -> int:
#         assert self.has_active_session()
#         return self.active_target_number
#
#     def get_student_id(self) -> str:
#         return self.student.meta.student_id
#
#     def get_student_name(self) -> str:
#         return self.student.meta.name
#
#     def get_active_session_submitted_source_code(self) -> str | None:
#         assert self.has_active_session()
#         return state.project_service.get_submitted_source_code_for(
#             student_id=self.get_student_id(),
#             target_number=self.get_target_number(),
#         )
#
#     def get_active_session_testcase_count(self) -> int:
#         assert self.is_active_session_success()
#         return len(self.active_session_result.testcase_results)
#
#     # i_testcase is the index of the testcase in the testcase_results, not a testcase number
#     def get_active_session_testcase_result(self) -> TestCaseResult:
#         assert self.is_active_session_success()
#         return self.active_session_result.testcase_results[self.active_testcase_order_index]
#
#     def get_active_session_testcase_result_state_mapping(self) -> dict[int, TestCaseResultState]:
#         assert self.is_active_session_success()
#         return {
#             result.testcase.number: result.result_state
#             for result in self.active_session_result.testcase_results
#         }
#
#     def has_next_testcase(self) -> bool:
#         assert self.is_active_session_success()
#         return self.active_testcase_order_index < self.get_active_session_testcase_count() - 1
#
#     def has_prev_testcase(self) -> bool:
#         assert self.is_active_session_success()
#         return self.active_testcase_order_index > 0
#
#     # def get_active_session_current_score(self) -> int:
#     #     assert self.is_active_session_success()
#     #     return 0
#     #
#     # def get_active_session_current_mark_reason(self) -> str:
#     #     assert self.is_active_session_success()
#     #     return ""
#
#
# class TestCaseResultStateListWidget(QWidget):
#     def __init__(
#             self,
#             parent: QObject = None,
#     ):
#         super().__init__(parent)
#
#         self.__mapping: dict[int, TestCaseResultState] | None = None
#
#         self._init_ui()
#
#     def _init_ui(self):
#         layout = QHBoxLayout()
#         self.setLayout(layout)
#
#         layout.addStretch(1)
#
#         self._layout_items = QHBoxLayout()
#         self._layout_items.setContentsMargins(0, 0, 0, 0)
#         layout.addLayout(self._layout_items)
#
#         layout.addStretch(1)
#
#     def set_testcase_result_state_mapping(self, states: dict[int, TestCaseResultState] | None):
#         self.__mapping = states
#         self._update_data()
#
#     def _update_data(self):
#         mapping = self.__mapping if self.__mapping else {}
#
#         while self._layout_items.count():
#             child = self._layout_items.takeAt(0)
#             if child.widget():
#                 child.widget().deleteLater()
#
#         for k in sorted(mapping.keys()):
#             # noinspection PyArgumentList
#             self._layout_items.addWidget(
#                 QLabel(
#                     f"{k}:",
#                     parent=self,
#                 )
#             )
#             self._layout_items.addWidget(
#                 TestCaseResultStateIndicatorWidget(
#                     value=mapping[k],
#                     parent=self,
#                 )
#             )
#
#
# class StudentMarkWidget(QWidget):
#     def __init__(
#             self,
#             parent: QObject = None,
#     ):
#         super().__init__(parent)
#
#         self.signals = StudentMarkWidgetSignals(self)
#
#         self._init_ui()
#
#         self.__data: _Data | None = None
#         self._update_data()
#
#     def _init_ui(self):
#         layout = QHBoxLayout()
#         self.setLayout(layout)
#
#         if "left":
#             layout_left = QVBoxLayout()
#             layout.addLayout(layout_left)
#
#             self._l_nav_session = QLabel(self)
#             self._l_nav_session.setFont(font(monospace=True, large=True))
#             layout_left.addWidget(self._l_nav_session)
#
#             # noinspection PyTypeChecker
#             self._te_source = SourceTextEdit(parent=self)
#             self._te_source.setReadOnly(True)
#             self._te_source.setMaximumWidth(450)
#             layout_left.addWidget(self._te_source)
#
#         if "right":
#             layout_right = QVBoxLayout()
#             layout.addLayout(layout_right)
#
#             if "testcase-top":
#                 layout_testcase_top = QHBoxLayout()
#                 layout_right.addLayout(layout_testcase_top)
#
#                 b = QPushButton("<", self)
#                 b.setToolTip("前のテスト結果")
#                 b.clicked.connect(self.signals.request_prev_testcase)
#                 layout_testcase_top.addWidget(b)
#                 self._b_prev_testcase = b
#
#                 layout_testcase_top.addStretch(1)
#
#                 self._l_nav_testcase = QLabel(self)
#                 layout_testcase_top.addWidget(self._l_nav_testcase)
#
#                 layout_testcase_top.addStretch(1)
#
#                 b = QPushButton(">", self)
#                 b.clicked.connect(self.signals.request_next_testcase)
#                 b.setToolTip("次のテスト結果")
#                 layout_testcase_top.addWidget(b)
#                 self._b_next_testcase = b
#
#             if "testcase-and-answer-view":
#                 # noinspection PyTypeChecker
#                 self._w_testcase = TestCaseResultWidget(parent=self)
#                 self._w_testcase.layout().setContentsMargins(0, 0, 0, 0)
#                 layout_right.addWidget(self._w_testcase)
#
#             if "testcase-state-list":
#                 self._w_testcase_state_list = TestCaseResultStateListWidget(parent=self)
#                 layout_right.addWidget(self._w_testcase_state_list)
#
#             if "mark-inputs":
#                 layout_mark_inputs = QHBoxLayout()
#                 layout_mark_inputs.setAlignment(Qt.AlignBottom)
#                 layout_right.addLayout(layout_mark_inputs)
#
#                 layout_mark_inputs.addStretch(1)
#
#                 self._spin_mark = QSpinBox(self)
#                 self._spin_mark.setRange(-1, 5)
#                 f = font(monospace=True)
#                 f.setPointSize(20)
#                 self._spin_mark.setFont(f)
#                 layout_mark_inputs.addWidget(self._spin_mark)
#
#                 label = QLabel("点", self)
#                 layout_mark_inputs.addWidget(label)
#                 layout_mark_inputs.setStretch(layout_mark_inputs.count() - 1, 0)
#
#                 layout_mark_inputs.addStretch(1)
#
#                 # self._c_mark_reason = QComboBox(self)
#                 # self._c_mark_reason.setEditable(True)
#                 # self._c_mark_reason.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
#                 # layout_mark_inputs.addWidget(self._c_mark_reason)
#
#             if "controls-bottom":
#                 layout_control_bottom = QHBoxLayout(self)
#                 layout_right.addLayout(layout_control_bottom)
#
#                 b = QPushButton("前の採点へ", self)
#                 b.clicked.connect(self.signals.request_prev_mark)
#                 layout_control_bottom.addWidget(b)
#
#                 layout_control_bottom.addStretch(1)
#
#                 b = QPushButton("ショートカットキー一覧")
#                 b.clicked.connect(self.signals.show_shortcuts)
#                 layout_control_bottom.addWidget(b)
#
#                 layout_control_bottom.addStretch(1)
#
#                 b = QPushButton("次の採点へ", self)
#                 b.clicked.connect(self.signals.request_next_mark)
#                 layout_control_bottom.addWidget(b)
#
#     @property
#     def score_value(self) -> int:
#         return self._spin_mark.value()
#
#     def _update_data(self):
#         item = self.__data
#
#         if item is not None and item.has_active_session():
#             self._l_nav_session.setText(
#                 f"設問 {item.get_target_number():02} "
#                 f"学籍番号 {item.get_student_id()} {item.get_student_name()}"
#             )
#         elif item is not None:
#             self._l_nav_session.setText(
#                 f"設問 -- "
#                 f"学籍番号 {item.get_student_id()} {item.get_student_name()}"
#             )
#         else:
#             self._l_nav_session.setText("（表示できる生徒がいません）")
#
#         if item is not None and item.has_active_session():
#             source_code = item.get_active_session_submitted_source_code()
#             if source_code is None:
#                 self._te_source.setPlainText("（ソースコードが見つかりません）")
#                 self._te_source.setEnabled(False)
#             else:
#                 self._te_source.setPlainText(source_code)
#                 self._te_source.setEnabled(True)
#         else:
#             self._te_source.setPlainText("（表示できる設問がありません）")
#             self._te_source.setEnabled(False)
#
#         if item is not None and item.is_active_session_success():
#             self._l_nav_testcase.setText(
#                 f"テストケース "
#                 f"{item.active_testcase_order_index + 1} / {item.get_active_session_testcase_count()}"
#             )
#         else:
#             self._l_nav_testcase.setText("（表示できるテストケースがありません）")
#
#         if item is not None and item.is_active_session_success():
#             self._b_prev_testcase.setEnabled(item.has_prev_testcase())
#             self._b_next_testcase.setEnabled(item.has_next_testcase())
#         else:
#             self._b_prev_testcase.setEnabled(False)
#             self._b_next_testcase.setEnabled(False)
#
#         if item is not None and item.is_active_session_success():
#             self._w_testcase.set_testcase_result(
#                 item.get_active_session_testcase_result()
#             )
#             self._w_testcase_state_list.set_testcase_result_state_mapping(
#                 item.get_active_session_testcase_result_state_mapping()
#             )
#         else:
#             self._w_testcase.set_testcase_result(None)
#             self._w_testcase_state_list.set_testcase_result_state_mapping(None)
#
#         self._spin_mark.setValue(
#             self.__data.student.mark_scores.get(self.__data.active_target_number, -1)
#             if self.__data is not None
#             else -1
#         )
#         self._spin_mark.setEnabled(True)
#         # self._c_mark_reason.clear()
#         # self._c_mark_reason.setEnabled(False)
#
#         self._spin_mark.setFocus()
#
#     def set_data(
#             self,
#             *,
#             student: Student,
#             active_target_number: int,
#             active_testcase_order_index: int,
#     ):
#         data = _Data(
#             student=student,
#             active_target_number=active_target_number,
#             active_testcase_order_index=active_testcase_order_index,
#             progress_value=0,
#             progress_total=0,
#         )
#         self.__data = data
#         self._update_data()
#
#     def set_value(self, value: int | None):
#         if value is None:
#             self._spin_mark.setValue(-1)
#         else:
#             self._spin_mark.setValue(value)
#
#     def move_to_next_testcase(self):
#         self._b_next_testcase.click()
#
#     def move_to_prev_testcase(self):
#         self._b_prev_testcase.click()
#
#     def set_session_navigation_color(self, color: str):
#         self._l_nav_session.setStyleSheet(f"background: {color};")
#
#     def switch_line_wrap_enabled(self):
#         self._w_testcase.set_line_wrap_enabled(
#             not self._w_testcase.get_line_wrap_enabled()
#         )
#
#
# class StudentMarkDialog(QDialog):
#     def __init__(
#             self,
#             parent: QObject = None,
#             student_id_filter: list[str] | None = None,
#     ):
#         super().__init__(parent)
#
#         self._init_ui(filtered=student_id_filter is not None)
#         self.__init_signals()
#
#         self.__set_initial_data(student_id_filter=student_id_filter)
#
#         self.installEventFilter(self)
#
#     def _init_ui(self, filtered):
#         self.resize(1600, 700)
#         if filtered:
#             self.setWindowTitle("採点（一部の生徒のみ）")
#         else:
#             self.setWindowTitle("採点（一括）")
#
#         layout = QVBoxLayout()
#         self.setLayout(layout)
#
#         # noinspection PyTypeChecker
#         self._w_mark = StudentMarkWidget(parent=self)
#         layout.addWidget(self._w_mark)
#
#         if filtered:
#             self._w_mark.set_session_navigation_color("yellow")
#
#     def __init_signals(self):
#         self._w_mark.signals.request_next_mark.connect(
#             self._on_request_next_mark
#         )
#         self._w_mark.signals.request_prev_mark.connect(
#             self._on_request_prev_mark
#         )
#         self._w_mark.signals.request_next_testcase.connect(
#             self._on_request_next_testcase
#         )
#         self._w_mark.signals.request_prev_testcase.connect(
#             self._on_request_prev_testcase
#         )
#         self._w_mark.signals.show_shortcuts.connect(
#             self._on_show_shortcuts
#         )
#
#     def __set_initial_data(self, student_id_filter: list[str] | None = None):
#         self.__current: ProjectService.MarkEntry | None
#
#         self.__mark_entries = state.project_service.list_mark_entries(
#             student_id_filter=student_id_filter,
#         )
#
#         self.__active_testcase_order_index: int | None = None
#         if self.__mark_entries:
#             self.__current = self.__mark_entries[0]
#         else:
#             self.__current = None
#         self.__reset_active_testcase_order_index()
#         self._update_data()
#
#     def request_show_target(self, student_id: str, target_index: int):
#         for entry in self.__mark_entries:
#             if entry.student.meta.student_id != student_id:
#                 continue
#             if entry.target_number != target_index:
#                 continue
#             self.__current = entry
#             break
#         self._update_data()
#
#     def _on_request_next_mark(self):
#         self.__transit_mark(delta=+1)
#
#     def _on_request_prev_mark(self):
#         self.__transit_mark(delta=-1)
#
#     def _on_request_next_testcase(self):
#         self.__active_testcase_order_index += 1
#         self._update_data()
#
#     def _on_request_prev_testcase(self):
#         self.__active_testcase_order_index -= 1
#         self._update_data()
#
#     def _update_data(self):
#         if self.__current:
#             self._w_mark.set_data(
#                 student=self.__current.student,
#                 active_target_number=self.__current.target_number,
#                 active_testcase_order_index=self.__active_testcase_order_index,
#             )
#
#     def __reset_active_testcase_order_index(self):
#         if self.__current is None:
#             self.__active_testcase_order_index = None
#         elif self.__current.student.test_result is None:
#             self.__active_testcase_order_index = None
#         else:
#             active_test_session_result = self.__current.student.test_result.test_session_results.get(
#                 self.__current.target_number
#             )
#             if active_test_session_result is None:
#                 self.__active_testcase_order_index = None
#             elif active_test_session_result.testcase_results:
#                 self.__active_testcase_order_index = 0
#             else:
#                 self.__active_testcase_order_index = None
#
#     def __transit_mark(self, delta: int):
#         self._save_w_mark()
#
#         if self.__current is None:
#             return
#
#         i = self.__mark_entries.index(self.__current)
#         i += delta
#         if i < 0:
#             # noinspection PyTypeChecker
#             QMessageBox.information(
#                 self,
#                 "前の採点へ",
#                 "これより前の採点はありません"
#             )
#             return
#         if i >= len(self.__mark_entries):
#             # noinspection PyTypeChecker
#             QMessageBox.information(
#                 self,
#                 "次の採点へ",
#                 "これより次の採点はありません"
#             )
#             return
#
#         self.__current = self.__mark_entries[i]
#         self.__reset_active_testcase_order_index()
#
#         self._update_data()
#
#     _NUMERIC_KEYS = [
#         Qt.Key_0,
#         Qt.Key_1,
#         Qt.Key_2,
#         Qt.Key_3,
#         Qt.Key_4,
#         Qt.Key_5,
#         Qt.Key_6,
#         Qt.Key_7,
#         Qt.Key_8,
#         Qt.Key_9,
#     ]
#
#     def eventFilter(self, obj: QObject, evt: QEvent):
#         if evt.type() == QEvent.KeyRelease:
#             assert isinstance(evt, QKeyEvent)
#             if evt.key() == Qt.Key_Left:
#                 self._w_mark.signals.request_prev_mark.emit()
#                 return False
#             elif evt.key() == Qt.Key_Right:
#                 self._w_mark.signals.request_next_mark.emit()
#                 return False
#             elif evt.key() == Qt.Key_Backspace:
#                 self._w_mark.set_value(None)
#                 return False
#             elif evt.key() in self._NUMERIC_KEYS:
#                 value = self._NUMERIC_KEYS.index(evt.key())
#                 self._w_mark.set_value(value)
#                 return False
#             elif evt.key() == Qt.Key_W:
#                 self._w_mark.switch_line_wrap_enabled()
#                 return False
#             elif evt.key() == Qt.Key_D:
#                 self._w_mark.move_to_next_testcase()
#                 return False
#             elif evt.key() == Qt.Key_A:
#                 self._w_mark.move_to_prev_testcase()
#                 return False
#         return super().eventFilter(obj, evt)
#
#     @pyqtSlot()
#     def _on_show_shortcuts(self):
#         shortcuts = [
#             ("←", "前の採点へ移動"),
#             ("→", "次の採点へ移動"),
#             ("A", "前のテストケースの結果へ移動"),
#             ("D", "次のテストケースの結果へ移動"),
#             ("数字", "点数を入力"),
#             ("バックスペース", "点数を消去"),
#             ("W", "テストケースの行の折り返し表示の切替"),
#         ]
#
#         shortcuts_text = "\n".join(
#             f"{key_name}： {desc}"
#             for key_name, desc in shortcuts
#         )
#
#         # noinspection PyTypeChecker
#         QMessageBox.information(
#             self,
#             "ショートカットキー一覧",
#             shortcuts_text,
#         )
#
#     def closeEvent(self, evt: QCloseEvent):
#         self._save_w_mark()
#         state.data_manager.save_if_necessary()
#
#     def _save_w_mark(self):
#         if self.__current is None:
#             return
#         with state.data():
#             self.__current.student.mark_scores[self.__current.target_number] \
#                 = self._w_mark.score_value
#             state.commit_data()
