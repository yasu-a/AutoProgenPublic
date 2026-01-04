from typing import Callable

from PyQt5.QtWidgets import QMessageBox

from app.di.system import get_task_manager
from app.di.usecase import get_student_table_get_student_id_cell_data_usecase, \
    get_student_list_id_usecase, get_student_table_get_student_name_cell_data_usecase, \
    get_student_table_get_student_stage_state_cell_data_usecase, \
    get_student_table_get_student_error_cell_data_usecase, get_student_mark_get_usecase, \
    get_student_submission_folder_show_usecase
from feature.workspace.handler.interface import IStudentTableView, IStudentTableHandler, \
    StudentTableRowViewModel
from feature.workspace.usecase.interface import StudentIDCellDataDto, StudentStageStateCellDataDto
from shared.domain.interface.event import IEventBus
from shared.domain.model.stage import Stage
from shared.domain.model.student_result import StudentStageStatusFlag
from shared.domain.value.event import StudentUpdateEvent
from shared.domain.value.identifier import StudentID
from shared.handler.interface import INavigator
from util.app_logging import create_logger


class CachedRowCollection:
    def __init__(self):
        self._rows: list[StudentTableRowViewModel] = []
        self._student_id_to_index: dict[StudentID, int] = {}  # 更新を高速化するためのLUT

    def initialize(self, initial_collection: list[StudentTableRowViewModel]):
        self._rows: list[StudentTableRowViewModel] = initial_collection
        self._student_id_to_index = {
            row.student_id: index
            for index, row in enumerate(initial_collection)
        }

    def update(self, row: StudentTableRowViewModel) -> None:
        row_index = self._student_id_to_index.get(row.student_id)
        self._rows[row_index] = row


class StudentTableHandler(IStudentTableHandler):
    _logger = create_logger()

    def __init__(
            self,
            *,
            view: IStudentTableView | None,
            navigator: INavigator,
            event_bus: IEventBus,
    ):
        self._view: IStudentTableView | None = view
        self._navigator = navigator
        self._event_bus: IEventBus = event_bus

        self._row_collection = CachedRowCollection()

    def on_view_initialized(self) -> None:
        self._initial_update()

        # StudentEventをサブスクライブ
        self._event_bus.subscribe(StudentUpdateEvent, self._student_event_callback)

    def on_view_closed(self) -> None:
        # StudentEventのサブスクライブを解除
        self._event_bus.unsubscribe(StudentUpdateEvent, self._student_event_callback)

    def _student_event_callback(self, event: StudentUpdateEvent):
        self._logger.debug(f"Student event received: {event}")
        self._secondary_update(event.student_id)

    def on_student_id_clicked(self, student_id: StudentID):
        """学籍番号クリック時：提出フォルダを開く"""
        get_student_submission_folder_show_usecase().execute(
            student_id=student_id,
        )

    def on_sore_clicked(self, student_id: StudentID):
        """点数クリック時：採点画面へ遷移"""
        # タスクが実行中かチェック
        if not get_task_manager().is_empty():
            QMessageBox.warning(
                self._view.get_parent_widget(),
                "採点",
                "タスクが終了するまでは採点できません"
            )
            return

        # 採点ダイアログを表示（指定された生徒）
        self._navigator.open_scoring_dialog_with_student(self._view.get_parent_widget(), student_id)

    def _get_latest_student_row(self, student_id: StudentID) -> StudentTableRowViewModel:
        # TODO: inject dependencies
        dto: StudentIDCellDataDto \
            = get_student_table_get_student_id_cell_data_usecase().execute(student_id)
        name = get_student_table_get_student_name_cell_data_usecase().execute(
            student_id).student_name

        status: dict[Stage, list[str]] = {}

        def status_to_text(s_lst: list[StudentStageStatusFlag]) -> list[str]:
            return [
                {
                    StudentStageStatusFlag.UNFINISHED: "―",
                    StudentStageStatusFlag.FINISHED_SUCCESS: "✔",
                    StudentStageStatusFlag.FINISHED_FAILURE: "⚠",
                }[s]
                for s in s_lst
            ]

        for stage_type in (Stage.BUILD, Stage.COMPILE, Stage.EXECUTE, Stage.TEST):
            result: StudentStageStateCellDataDto \
                = get_student_table_get_student_stage_state_cell_data_usecase() \
                .execute(student_id, stage_type)

            if stage_type in (Stage.BUILD, Stage.COMPILE):
                # v 従来は全部一致していなかったら「？マーク表示」だった？
                status[stage_type] = status_to_text([list(result.states.values())[0]])
            else:
                status[stage_type] = status_to_text(list(result.states.values()))

        error_entries \
            = get_student_table_get_student_error_cell_data_usecase() \
            .execute(student_id).aggregate_text_entries()
        if len(error_entries) == 0:
            error_summary_text = None
            error_detailed_text = None
        elif len(error_entries) == 1:
            error_summary_text = error_entries[0].summary_text
            error_detailed_text = error_entries[0].detailed_text
        else:
            error_summary_text = error_entries[0].summary_text \
                                 + f"（他 {len(error_entries) - 1} 件のエラー）"
            error_detailed_text = "\n".join(
                f"◆ {entry.detailed_text}" for entry in error_entries
            )

        score = get_student_mark_get_usecase().execute(student_id)
        if score.is_marked:
            score_text = str(score.score)
        else:
            score_text = "未採点"

        row = StudentTableRowViewModel(
            student_id=student_id,
            has_submission=dto.is_submission_folder_link_alive,
            name=name,
            build_stage_status=status[Stage.BUILD][0],
            compile_stage_status=status[Stage.COMPILE][0],
            execute_stage_status_lst=status[Stage.EXECUTE],
            test_stage_status_lst=status[Stage.TEST],
            error_summary=error_summary_text,
            error_detailed_text=error_detailed_text,
            score=score_text,
        )
        return row

    def _load_initial_rows(self, progress_callback: Callable[[str], None]) \
            -> list[StudentTableRowViewModel]:
        rows: list[StudentTableRowViewModel] = []

        for student_id in get_student_list_id_usecase().execute():
            progress_callback(f"データをロードしています・・・: {student_id!s}")

            row = self._get_latest_student_row(student_id)

            rows.append(row)

        return rows

    def _initial_update(self):
        rows = self._navigator.run_blocking_task(
            parent=self._view.get_parent_widget(),
            title="プロジェクトを開く",
            initial_message="データをロードしています・・・",
            task_func=self._load_initial_rows,
        )

        self._row_collection.initialize(rows)
        self._view.update_table_data(rows)

    def _secondary_update(self, student_id: StudentID):
        row = self._get_latest_student_row(student_id)
        self._row_collection.update(row)
        self._view.update_table_data([row])
