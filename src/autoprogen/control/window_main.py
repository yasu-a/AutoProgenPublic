from typing import Callable

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from autoprogen.control.dialog_progress import AbstractProgressDialog
from autoprogen.control.coordinator_student_error_detail import (
    StudentErrorDetailCoordinator,
)
from autoprogen.control.qt_student_change_bridge import QtStudentChangeBridge
from autoprogen.control.task.clean_all_stage import CleanAllStagesStudentTask
from autoprogen.control.task.run_stage import RunStagesStudentTask
from autoprogen.control.widget_status_process_resource_usage import ProcessResourceUsageStatusBarWidget
from autoprogen.control.widget_status_task_state import TaskStateStatusBarWidget
from autoprogen.control.widget_status_unstable_version_notif import UnstableVersionNotificationStatusBarWidget
from autoprogen.control.widget_student_table import StudentTableWidget
from autoprogen.control.widget_toolbar import ToolBar
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.task.task import AbstractStudentTask
from autoprogen.usecase.main_window import MainWindowFacade
from autoprogen.util.app_logging import create_logger

from autoprogen.control.interface_navigator import INavigator


class MainWindow(QMainWindow):
    _logger = create_logger()

    def __init__(
            self,
            parent: QObject = None,
            *,
            navigator: INavigator,
            main_window_facade: MainWindowFacade,
            student_error_detail_coordinator: StudentErrorDetailCoordinator,
    ) -> None:
        """画面遷移、メイン画面操作、エラー詳細の調整役を受け取る。"""
        super().__init__(parent)
        self._navigator = navigator
        self._facade = main_window_facade
        self._student_error_detail_coordinator = student_error_detail_coordinator
        self._student_error_detail_coordinator.testcase_list_changed.connect(
            self.load_student_table,
        )
        self._task_manager = main_window_facade.task_manager
        self._table_loading = False
        self._student_change_bridge = QtStudentChangeBridge(
            self,
            student_ids=[],
            student_change_event_bus=self._facade.student_change_event_bus,
        )

        self._init_ui()
        self._init_signals()
        QTimer.singleShot(0, self.load_student_table)

    def load_student_table(self) -> None:
        """進捗ダイアログを表示しながら学生テーブルを全件ロードする。"""
        if self._table_loading:
            return
        self._table_loading = True
        try:
            rows = AbstractProgressDialog.run_blocking_task(
                parent=self,
                title="学生テーブルの読み込み",
                initial_message="学生の表示データを読み込み中...",
                task_func=self._facade.load_student_table,
            )
            if rows is None:
                raise RuntimeError("学生テーブルの読み込み結果がありません")
            self._w_student_table.apply_loaded_rows(rows)
            self._student_change_bridge.set_student_ids(
                [row.student_id for row in rows],
            )
        except Exception as error:
            self._logger.exception("Student table loading failed")
            QMessageBox.critical(self, "学生テーブルの読み込み", str(error))
        finally:
            self._table_loading = False

    def _init_ui(self) -> None:
        """学生テーブルとエラー詳細Dockを含むメイン画面を構築する。"""
        project_summary = self._facade.get_project_summary()

        # noinspection PyUnresolvedReferences
        self.setWindowTitle(
            f"{project_summary.project_name} 設問{project_summary.target_number}"
        )
        self.resize(1500, 800)

        # ツールバー
        self._tool_bar = ToolBar(self)
        # noinspection PyUnresolvedReferences
        self.addToolBar(self._tool_bar)

        # 生徒のテーブル
        # noinspection PyTypeChecker
        self._w_student_table = StudentTableWidget(
            self,
        )
        # noinspection PyUnresolvedReferences
        self.setCentralWidget(self._w_student_table)

        # エラー詳細は表を操作したまま確認できる下部ドックとして配置する。
        self._student_error_dock = QDockWidget("エラーの詳細", self)
        self._student_error_dock.setObjectName("studentErrorDetailDock")
        self._student_error_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self._student_error_dock.setFeatures(QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._student_error_dock)
        self._student_error_dock.hide()

        # ステータスバー
        #  - タスクモニタ
        # noinspection PyTypeChecker
        self._sb_task_state = TaskStateStatusBarWidget(
            self,
            task_manager=self._task_manager,
        )
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_task_state)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(QLabel(self), 1)
        #  - テスト版通知
        # noinspection PyTypeChecker
        self._sb_unstable_version_notif = UnstableVersionNotificationStatusBarWidget(
            self,
        )
        self._sb_unstable_version_notif.set_data(
            self._facade.is_app_version_stable(),
        )
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_unstable_version_notif)
        #  - リソースモニタ
        # noinspection PyTypeChecker
        self._sb_process_resource_usage = ProcessResourceUsageStatusBarWidget(
            self,
        )
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_process_resource_usage)
        self._resource_usage_timer = QTimer(self)
        self._resource_usage_timer.setInterval(1000)

    def _init_signals(self) -> None:
        """メイン画面の操作要求を各処理へ接続する。"""
        self._tool_bar.triggered.connect(self.__tool_bar_triggered)
        self._w_student_table.student_id_cell_triggered.connect(
            self.__w_student_table_student_id_cell_triggered
        )
        self._w_student_table.mark_result_cell_triggered.connect(
            self.__w_student_table_mark_result_cell_triggered
        )
        self._w_student_table.error_cell_triggered.connect(
            self.__w_student_table_error_cell_triggered
        )
        self._resource_usage_timer.timeout.connect(
            self.__update_resource_usage
        )
        self._student_change_bridge.student_changed.connect(
            self.__student_modification_observed,
        )
        self._task_manager.busy_changed.connect(self._on_task_busy_changed)
        # 画面を開く前にタスクが登録されていても実際の状態に揃える。
        self._on_task_busy_changed(not self._task_manager.is_empty())
        self._resource_usage_timer.start()

    @pyqtSlot(bool)
    def _on_task_busy_changed(self, _is_busy: bool) -> None:
        """タスクの実行状態に応じてUIを更新する。"""
        # 受信した時点の最新状態を使いたいから受け取った状態は使用しない
        del _is_busy
        is_busy = not self._task_manager.is_empty()

        self._tool_bar.update_button_state(is_task_alive=is_busy)
        self._w_student_table.setEnabled(not is_busy)
        self._student_error_dock.setEnabled(not is_busy)

        if is_busy:
            self._student_error_dock.hide()

    @pyqtSlot(StudentID)
    def __student_modification_observed(self, student_id: StudentID) -> None:
        """変更通知を受けた学生一人を再取得し、テーブル表示へ反映する。"""
        try:
            row = self._facade.load_student_table_row(student_id)
            self._w_student_table.replace_loaded_row(row)
        except Exception:
            self._logger.exception(
                "学生行の再読み込みに失敗しました: %s",
                student_id,
            )

    @pyqtSlot()
    def __update_resource_usage(self) -> None:
        """最新のリソース使用量を取得してステータス表示へ反映する。"""
        self._sb_process_resource_usage.set_data(
            self._facade.get_resource_usage(),
        )

    @pyqtSlot(StudentID)
    def __w_student_table_student_id_cell_triggered(
            self,
            student_id: StudentID,
    ) -> None:
        """学籍番号セルの学生の展開済み提出フォルダを開く。"""
        if not self._task_manager.is_empty():
            return
        self._facade.open_student_submission_folder(student_id)

    @pyqtSlot(StudentID)
    def __w_student_table_mark_result_cell_triggered(
            self,
            student_id: StudentID,
    ) -> None:
        """点数セルの学生だけを対象とした採点画面を開く。"""
        if not self._task_manager.is_empty():
            # noinspection PyTypeChecker
            QMessageBox.warning(
                self,
                "採点",
                "実行が完了するまでは採点できません"
            )
            return

        self._navigator.open_scoring_dialog_for_student(self, student_id)

    @pyqtSlot(StudentID)
    def __w_student_table_error_cell_triggered(
            self,
            student_id: StudentID,
    ) -> None:
        """エラーセルの学生の詳細を下部Dockへ表示する。"""
        if not self._task_manager.is_empty():
            return
        self.__show_student_error_detail(student_id)

    def __show_student_error_detail(
            self,
            student_id: StudentID,
    ) -> None:
        """指定学生のエラー詳細を表示し、対象がなければDockを閉じる。"""
        if not self._task_manager.is_empty():
            return
        detail_widget = self._student_error_detail_coordinator.create_widget(
            self._student_error_dock,
            student_id,
        )
        if detail_widget is None:
            self._student_error_dock.hide()
            return

        previous_widget = self._student_error_dock.widget()
        self._student_error_dock.setWidget(detail_widget)
        if previous_widget is not None:
            previous_widget.deleteLater()
        student_name = self._facade.get_student_name(student_id)
        self._student_error_dock.setWindowTitle(
            f"エラーの詳細 - {student_id} {student_name}"
        )
        self._student_error_dock.show()
        self._student_error_dock.raise_()

    def __perform_stop_tasks(self) -> None:
        """実行中の学生タスクがあれば停止処理を行う。"""
        if not self._task_manager.is_empty():
            AbstractProgressDialog.run_blocking_task(
                parent=self,
                title="タスクの停止",
                initial_message="停止処理を開始します...",
                task_func=self._task_manager.terminate,
            )

    def __enqueue_student_tasks_if_not_run(
            self,
            task_factory: Callable[[StudentID], AbstractStudentTask],
    ) -> None:
        """タスク停止中の場合だけ全学生分のタスクを登録する。"""
        if not self._task_manager.is_empty():
            return
        for student_id in self._facade.list_student_ids():
            self._task_manager.enqueue(task_factory(student_id))

    def __tool_bar_triggered(self, name: str) -> None:
        """ツールバーから要求されたメイン画面操作を実行する。"""
        if name == "run":
            self.__enqueue_student_tasks_if_not_run(
                lambda student_id: RunStagesStudentTask(
                    parent=self,
                    student_id=student_id,
                    main_window_facade=self._facade,
                ),
            )
        elif name == "stop":
            self.__perform_stop_tasks()
        elif name == "clear":
            self.__enqueue_student_tasks_if_not_run(
                lambda student_id: CleanAllStagesStudentTask(
                    parent=self,
                    student_id=student_id,
                    main_window_facade=self._facade,
                ),
            )
        elif name == "edit-settings":
            # noinspection PyTypeChecker
            self._navigator.open_setting_dialog(self)
        elif name == "edit-project-settings":
            # noinspection PyTypeChecker
            self._navigator.open_project_settings_dialog(self)
        elif name == "edit-testcases":
            # noinspection PyTypeChecker
            if self._navigator.open_testcase_list_edit_dialog(self):
                self.load_student_table()
        elif name == "mark":
            # noinspection PyTypeChecker
            self._navigator.open_scoring_dialog(self)
        elif name == "export-scores":
            # noinspection PyTypeChecker
            self._navigator.open_score_export_dialog(self)
        elif name == "about":
            # noinspection PyTypeChecker
            self._navigator.open_about_dialog(self)
        else:
            assert False, name

    def closeEvent(self, evt, **kwargs) -> None:
        """購読を解除してランチャー画面への遷移を予約する。"""
        self._student_change_bridge.stop()
        evt.accept()
        # noinspection PyTypeChecker
        QTimer.singleShot(
            0,
            lambda: self._navigator.transition_from_workspace_to_launcher(
                self),
        )
