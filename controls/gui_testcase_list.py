# from dataclasses import dataclass
# from typing import TYPE_CHECKING, Generic, TypeVar
#
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# from PyQt5.QtWidgets import *
#
# import application.dependency
# import state
# from controls.gui_testcase_content import TestCaseContentEditDialog
# from files.testcase import TestCaseConfigError
# from icons import icon
#
# if TYPE_CHECKING:
#     from files.testcase import TestCaseIO
#
#
# @dataclass(slots=True, frozen=True)
# class _ListItem:
#     i_row: int
#
#     def get_target_number(self) -> int:
#         raise NotImplementedError()
#
#
# @dataclass(slots=True, frozen=True)
# class _ListItemTarget(_ListItem):
#     target_number: int
#     error: TestCaseConfigError | None
#
#     def get_target_number(self) -> int:
#         return self.target_number
#
#     @property
#     def success(self) -> bool:
#         return self.error is None
#
#     @property
#     def error_text(self) -> str | None:
#         if self.error is None:
#             return None
#         else:
#             lines = [self.error.reason]
#             if self.error.target_index is not None:
#                 lines.append(f" - 対象：設問{self.error.target_index:02}")
#             if self.error.testcase_index is not None:
#                 lines.append(f" - 対象：テストケース{self.error.testcase_index}")
#             return "\n".join(lines)
#
#
# @dataclass(slots=True, frozen=True)
# class _ListItemTestCase(_ListItem):
#     parent_target_item: _ListItemTarget
#     testcase_number: int
#     has_input: bool
#     has_output: bool
#
#     def get_target_number(self) -> int:
#         return self.parent_target_item.target_number
#
#
# T = TypeVar("T", bound=_ListItem)
#
#
# class ListItemWidget(QFrame, Generic[T]):
#     control_triggered = pyqtSignal(str, int)  # type: ignore # name and i_row
#
#     def __init__(
#             self,
#             item: T,
#             parent: QObject = None,
#             show_buttons_on_hovering=False,
#             name_emitted_on_double_click=None,
#     ):
#         super().__init__(parent)
#         self._item = item
#         self.__show_buttons_on_hovering = show_buttons_on_hovering
#         self.__name_emitted_on_double_click = name_emitted_on_double_click
#         self._init_ui()
#
#     def _add_button(
#             self,
#             *,
#             name,
#             layout=None,
#             icon_name=None,
#             object_name_base=None,
#             tooltip=None,
#     ):
#         layout = layout or self.layout()
#         icon_name = icon_name or name
#         object_name_base = object_name_base or name
#
#         b = QPushButton(self)
#         b.setIcon(icon(icon_name))
#         b.setObjectName(f"{object_name_base} {self._item.i_row}")
#         b.setFixedSize(QSize(25, 25))
#         b.clicked.connect(self.__on_ctrl_clicked)  # type: ignore
#         if tooltip:
#             b.setToolTip(tooltip)
#         layout.addWidget(b)
#
#     def __on_ctrl_clicked(self):
#         button = self.sender()
#         control_name, i_row_str = button.objectName().split()
#         self.control_triggered.emit(control_name, int(i_row_str))
#
#     def _init_ui(self):
#         pass
#
#     def set_control_button_visibility(self, v: bool):
#         for button in self.findChildren(QPushButton):
#             button.setVisible(v)
#
#     def showEvent(self, evt):
#         if self.__show_buttons_on_hovering:
#             self.set_control_button_visibility(False)
#
#     def enterEvent(self, evt):
#         if self.__show_buttons_on_hovering:
#             self.set_control_button_visibility(True)
#
#     def leaveEvent(self, evt):
#         if self.__show_buttons_on_hovering:
#             self.set_control_button_visibility(False)
#
#     def mouseDoubleClickEvent(self, evt):
#         if self.__name_emitted_on_double_click is not None:
#             for button in self.findChildren(QPushButton):
#                 if button.objectName().split()[0] == self.__name_emitted_on_double_click:
#                     button.click()
#
#
# class ListItemTargetSuccessWidget(ListItemWidget[_ListItemTarget]):
#     def __init__(self, item: _ListItemTarget, parent: QObject = None):
#         super().__init__(
#             item,
#             parent,
#             name_emitted_on_double_click="open",
#         )
#
#         assert item.success, item
#
#     def _init_ui(self):
#         super()._init_ui()
#
#         layout = QHBoxLayout()
#         layout.setContentsMargins(3, 3, 3, 3)
#         self.setLayout(layout)
#
#         self._l_title = QLabel(f"設問 {self._item.target_number:02}", self)
#         self._l_title.setMargin(3)
#         self._l_title.setStyleSheet("background-color: #bbff33; font-weight: bold")
#         layout.addWidget(self._l_title)
#
#         layout.addStretch(1)
#
#         self._add_button(name="add", tooltip="設問にテストケースを追加")
#         self._add_button(name="open", tooltip="テストケースの保管フォルダを開く")
#         self._add_button(name="delete", tooltip="設問とテストケースの削除")
#
#
# class ListItemTargetErrorWidget(ListItemWidget[_ListItemTarget]):
#     def __init__(self, item: _ListItemTarget, parent: QObject = None):
#         super().__init__(
#             item,
#             parent,
#             name_emitted_on_double_click="open",
#         )
#
#         assert not item.success, item
#
#     def _init_ui(self):
#         super()._init_ui()
#
#         layout_v = QVBoxLayout()
#         layout_v.setContentsMargins(3, 3, 3, 3)
#         self.setLayout(layout_v)
#
#         if "top":
#             layout_h = QHBoxLayout()
#             layout_v.addLayout(layout_h)
#
#             self._l_title = QLabel(f"設問 {self._item.target_number:02}", self)
#             self._l_title.setMargin(3)
#             self._l_title.setStyleSheet("background-color: #ffaaaa; font-weight: bold")
#             layout_h.addWidget(self._l_title)
#
#             layout_h.addStretch(1)
#
#             self._add_button(name="open", layout=layout_h,
#                              tooltip="テストケースの保管フォルダを開く")
#
#         if "bottom":
#             self._te_detail = QTextEdit(self)
#             self._te_detail.setReadOnly(True)
#             self._te_detail.setText(self._item.error_text)
#             self._te_detail.setFixedHeight(120)
#             layout_v.addWidget(self._te_detail)
#
#
# class ListItemTestCaseWidget(ListItemWidget[_ListItemTestCase]):
#     def __init__(self, item: _ListItemTestCase, parent: QObject = None):
#         super().__init__(
#             item,
#             parent,
#             show_buttons_on_hovering=False,
#             name_emitted_on_double_click="edit",
#         )
#
#     def _init_ui(self):
#         super()._init_ui()
#
#         layout = QHBoxLayout()
#         layout.setContentsMargins(3, 3, 3, 3)
#         self.setLayout(layout)
#
#         self._l_title = QLabel(f" + テストケース {self._item.testcase_number!s:>2}", self)
#         layout.addWidget(self._l_title)
#
#         layout.addStretch(1)
#
#         self._add_button(name="edit", tooltip="テストケースの編集")
#         self._add_button(name="delete", tooltip="テストケースの削除")
#
#
# class _ListItemCollection(list[_ListItem]):
#     @classmethod
#     def create_all_with_testcase_io(cls, testcase_io: "TestCaseIO") -> "_ListItemCollection":
#         target_numbers = testcase_io.list_target_numbers()
#         collection = cls()
#         for target_number in sorted(target_numbers):
#             try:
#                 test_session = testcase_io.validate_and_get_test_session(target_number)
#             except TestCaseConfigError as e:
#                 collection.append(
#                     _ListItemTarget(
#                         i_row=len(collection) - 1,
#                         target_number=target_number,
#                         error=e,
#                     )
#                 )
#             else:
#                 parent_target_item = _ListItemTarget(
#                     i_row=len(collection) - 1,
#                     target_number=target_number,
#                     error=None,
#                 )
#                 collection.append(parent_target_item)
#                 for testcase in sorted(test_session.testcases, key=lambda tc: tc.number):
#                     collection.append(
#                         _ListItemTestCase(
#                             i_row=len(collection) - 1,
#                             parent_target_item=parent_target_item,
#                             testcase_number=testcase.number,
#                             has_input=testcase.has_input(),
#                             has_output=testcase.has_output(),
#                         )
#                     )
#         return collection
#
#     @classmethod
#     def create_empty(cls) -> "_ListItemCollection":
#         return cls()
#
#     def apply_to_list_widget(self, w: QListWidget, trigger_signal):
#         n_items = len(self)
#         while w.count() > n_items:
#             w.takeItem(w.count() - 1)
#         while w.count() < n_items:
#             w.addItem(QListWidgetItem(w))
#
#         for i in range(n_items):
#             item = self[i]
#             if isinstance(item, _ListItemTarget):
#                 if item.success:
#                     item_w = ListItemTargetSuccessWidget(item, w)  # type: ignore
#                 else:
#                     item_w = ListItemTargetErrorWidget(item, w)  # type: ignore
#             elif isinstance(item, _ListItemTestCase):
#                 item_w = ListItemTestCaseWidget(item, w)  # type: ignore
#             else:
#                 assert False, item
#             item_w.control_triggered.connect(trigger_signal)
#             w.item(i).setSizeHint(item_w.sizeHint())
#             w.setItemWidget(w.item(i), item_w)
#
#
# class TestCaseListWidget(QListWidget):
#     control_triggered = pyqtSignal(str, int)  # type: ignore
#
#     def __init__(self, parent: QObject = None):
#         super().__init__(parent)
#
#         self.__error = None
#         self.__item_collection: _ListItemCollection = _ListItemCollection.create_empty()
#         self.__revision_id_on_last_update: int | None = None
#
#     def get_list_item(self, item_object_id: int) -> _ListItem | None:
#         for item in self.__item_collection:
#             if item.i_row == item_object_id:
#                 return item
#         return None
#
#     def update_data(self):
#         testcase_io = application.dependency.get_testcase_io()
#
#         revision_hash = testcase_io.get_revision_hash()
#         if revision_hash == self.__revision_id_on_last_update:
#             return
#         else:
#             self.__revision_id_on_last_update = revision_hash
#
#         self.__item_collection = _ListItemCollection.create_all_with_testcase_io(
#             testcase_io=testcase_io,
#         )
#         self.__item_collection.apply_to_list_widget(self, self.control_triggered)
#
#
# class TestCaseEditWidget(QWidget):
#     def __init__(self, parent: QObject = None):
#         super().__init__(parent)
#
#         self._init_ui()
#         self.__init_signals()
#
#     def _init_ui(self):
#         layout = QVBoxLayout()
#         self.setLayout(layout)
#
#         self._w_testcase_list = TestCaseListWidget(self)  # type: ignore
#         layout.addWidget(self._w_testcase_list)
#
#         b = QPushButton("新しい設問", self)
#         b.setObjectName("add")
#         b.clicked.connect(self.__on_ctrl_on_widget_triggered)  # type: ignore
#         layout.addWidget(b)
#
#         # self._w_ctrl = TestCaseEditControlWidget(self)
#         # layout.addWidget(self._w_ctrl)
#
#     def __init_signals(self):
#         # self._w_ctrl.control_triggered.connect(self.__on_ctrl_triggered)
#         self._w_testcase_list.control_triggered.connect(  # type: ignore
#             self.__on_ctrl_in_list_triggered
#         )
#
#     @pyqtSlot()
#     def __on_ctrl_on_widget_triggered(self):
#         name = self.sender().objectName()
#         if name == "add":
#             testcase_io = application.dependency.get_testcase_io()
#             # noinspection PyTypeChecker
#             i_target, ok = QInputDialog.getInt(
#                 self,
#                 "新しい設問",
#                 "設問番号を入力してください",
#                 value=testcase_io.get_expected_new_target_index(),
#                 min=0,
#                 max=99,
#             )
#             if not ok:
#                 return
#             result = testcase_io.add_target_index(i_target)
#             if not result:
#                 # noinspection PyTypeChecker
#                 QMessageBox.critical(
#                     self,
#                     "新しい設問",
#                     f"設問 {i_target:02} はすでに存在します",
#                 )
#         else:
#             assert False, name
#
#         self.update_data()
#
#     @pyqtSlot(str, int)
#     def __on_ctrl_in_list_triggered(self, name, item_object_id):
#         item = self._w_testcase_list.get_list_item(item_object_id)
#         if item is None:
#             return
#
#         if name == "add":
#             if isinstance(item, _ListItemTarget):
#                 if not item.success:
#                     # noinspection PyTypeChecker
#                     QMessageBox.critical(
#                         self,
#                         "新しいテストケース",
#                         f"設問の構成にエラーがあります。テストケースを追加するにはエラーを解決してください。",
#                     )
#                     return
#             target_number = item.get_target_number()
#             testcase_io = application.dependency.get_testcase_io()
#             i_testcase = testcase_io.get_expected_new_testcase_index(target_number)
#             testcase_io.add_testcase_index(target_number, i_testcase)
#
#         elif name == "open":
#             target_number = item.get_target_number()
#             testcase_io = application.dependency.get_testcase_io()
#             testcase_io.open_target_in_explorer(target_number)
#
#         elif name == "delete":
#             target_number = item.get_target_number()
#             testcase_io = application.dependency.get_testcase_io()
#             if isinstance(item, _ListItemTarget):
#                 # noinspection PyTypeChecker
#                 if QMessageBox.warning(
#                         self,
#                         "設問の削除",
#                         f"設問 {target_number:02} とその全てのテストケースを削除しますか？",
#                         QMessageBox.Yes | QMessageBox.No,
#                         QMessageBox.No,
#                 ) != QMessageBox.Yes:
#                     return
#                 testcase_io.delete_target(target_number)
#             elif isinstance(item, _ListItemTestCase):
#                 # noinspection PyTypeChecker
#                 if QMessageBox.warning(
#                         self,
#                         "テストケースの削除",
#                         f"設問 {target_number:02} のテストケース {item.testcase_number} を削除しますか？",
#                         QMessageBox.Yes | QMessageBox.No,
#                         QMessageBox.No,
#                 ) != QMessageBox.Yes:
#                     return
#                 testcase_io.delete_testcase(target_number, item.testcase_number)
#             else:
#                 assert False, item
#
#         elif name == "edit":
#             assert isinstance(item, _ListItemTestCase), item
#             testcase_io = application.dependency.get_testcase_io()
#             testcase = testcase_io.get_testcase(
#                 target_number=item.get_target_number(),
#                 testcase_number=item.testcase_number,
#             )
#             # noinspection PyTypeChecker
#             dialog = TestCaseContentEditDialog(testcase, self)
#             dialog.move(
#                 QCursor().pos() + QPoint(10, 10)
#             )
#             dialog.exec_()
#             testcase = dialog.get_testcase()
#             testcase_io.set_testcase(
#                 target_number=item.get_target_number(),
#                 testcase_number=item.testcase_number,
#                 testcase=testcase,
#                 context="replace",
#             )
#
#         else:
#             assert False, name
#
#         self.update_data()
#
#     def update_data(self):
#         self._w_testcase_list.update_data()
#
#
# class TestCaseListEditDialog(QDialog):
#     def __init__(self, parent: QObject = None):
#         super().__init__(parent)
#
#         self._init_ui()
#
#         self.__update_timer = QTimer(self)
#         self.__update_timer.setInterval(200)
#         self.__update_timer.timeout.connect(self.__update_timer_timeout)  # type: ignore
#         self.__update_timer.start()
#
#     def _init_ui(self):
#         self.setWindowTitle("テストケースの編集")
#         self.setModal(True)
#         self.resize(400, 700)
#
#         layout = QVBoxLayout()
#         self.setLayout(layout)
#
#         self._w_testcase_edit = TestCaseEditWidget(self)  # type: ignore
#         layout.addWidget(self._w_testcase_edit)
#
#     def __update_timer_timeout(self):
#         self._w_testcase_edit.update_data()
