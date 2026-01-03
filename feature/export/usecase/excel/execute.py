from pathlib import Path

from feature.export.domain.interface.gateway import (
    IExcelBackupGateway,
    ExcelBackupGatewayError,
)
from feature.export.domain.interface.service import (
    StudentScoreDataDto,
    IExcelScoreUpdatePlanningService,
    ExcelScoreUpdatePlanningError,
)
from feature.export.domain.value import ExcelColumnMapping, ExcelRowRange
from feature.export.usecase.interface import (
    IExecuteExcelScoreUpdateUseCase,
    IExportSettingGetUseCase,
    ExecuteExcelScoreUpdateError,
)
from shared.domain.interface.gateway import IExcelGateway, ExcelGatewayError
from shared.domain.service.student_mark_get import StudentMarkEntityGetSubService
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student import StudentRepository


class ExecuteExcelScoreUpdateUseCase(IExecuteExcelScoreUpdateUseCase):
    def __init__(
            self,
            *,
            excel_gateway: IExcelGateway,
            excel_backup_gateway: IExcelBackupGateway,
            student_repo: StudentRepository,
            student_mark_get_sub_service: StudentMarkEntityGetSubService,
            export_setting_get_usecase: IExportSettingGetUseCase,
            excel_score_update_planning_service: IExcelScoreUpdatePlanningService,
    ):
        self._excel_gateway = excel_gateway
        self._excel_backup_gateway = excel_backup_gateway
        self._student_repo = student_repo
        self._student_mark_get_sub_service = student_mark_get_sub_service
        self._export_setting_get_usecase = export_setting_get_usecase
        self._excel_score_update_planning_service = excel_score_update_planning_service

    def execute(
            self,
            *,
            excel_path: Path,
            sheet_name: str,
            mapping: ExcelColumnMapping,
            row_range: ExcelRowRange,
    ) -> Path | None:
        """Excelの点数を更新"""
        # 設定確認
        setting = self._export_setting_get_usecase.execute()
        do_backup = setting.backup_before_export

        # バックアップ作成
        backup_path = None
        if do_backup:
            try:
                backup_path = self._excel_backup_gateway.create_backup(
                    excel_path)
            except ExcelBackupGatewayError as e:
                raise ExecuteExcelScoreUpdateError(
                    f"バックアップの作成に失敗しました: {e}") from e

        # 採点データ取得 -> Map化
        students = self._student_repo.list()
        student_score_map: dict[StudentID, StudentScoreDataDto] = {}
        for student in students:
            student_mark = self._student_mark_get_sub_service.execute(
                student.student_id)
            student_score_map[student.student_id] = StudentScoreDataDto(
                name=student.name,
                score=student_mark.score if student_mark.is_marked else None,
            )

        # Excelから現在のデータを読み取り
        try:
            excel_cell_table = self._excel_gateway.get_sheet_cells(
                excel_path, sheet_name)
        except ExcelGatewayError as e:
            raise ExecuteExcelScoreUpdateError(
                f"Excelファイルの読み込みに失敗しました: {e}") from e

        # ドメインサービスで更新計画を計算
        try:
            update_values = self._excel_score_update_planning_service.execute(
                excel_cell_table=excel_cell_table,
                student_score_map=student_score_map,
                column_mapping=mapping,
                row_range=row_range,
            )
        except ExcelScoreUpdatePlanningError as e:
            raise ExecuteExcelScoreUpdateError(f"更新計画の計算に失敗しました: {e}") from e

        # セルを更新（Noneの場合は空文字列に変換）
        if update_values:
            # Noneを空文字列に変換（未採点の場合は空欄にする）
            values_to_write: dict[tuple[int, int], int | str] = {}
            for key, value in update_values.items():
                values_to_write[key] = value if value is not None else ""

            try:
                self._excel_gateway.update_sheet_cells(
                    excel_path=excel_path,
                    sheet_name=sheet_name,
                    values=values_to_write,
                )
            except ExcelGatewayError as e:
                raise ExecuteExcelScoreUpdateError(
                    f"Excelファイルの更新に失敗しました: {e}") from e

        return backup_path
