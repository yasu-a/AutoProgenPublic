from pathlib import Path

from domain.error import StudentMasterServiceError, StudentSubmissionServiceError, ManabaReportArchiveError, \
    ReadonlyExcelWorksheetGatewayError, ManabaReportListParserError, ManabaReportListArchiveValidateServiceError
from infra.gateway.manaba_report_archive import ManabaReportArchiveGateway
from infra.gateway.readonly_excel_worksheet import ReadonlyExcelWorksheetGateway
from service.current_project import CurrentProjectGetService, CurrentProjectSetInitializedService
from service.manaba_report_list_archive_validate import ManabaReportListArchiveValidateService
from service.manaba_report_list_parser import ManabaReportListParser
from service.student_master_create import StudentMasterCreateService
from service.student_submission import StudentSubmissionExtractService
from usecase.dto.project import NormalProjectSummary, ProjectInitializeResult
from usecase.progress import ProgressCallback


class CurrentProjectSummaryGetUseCase:
    def __init__(
            self,
            *,
            current_project_get_service: CurrentProjectGetService,
    ):
        self._current_project_get_service = current_project_get_service

    def execute(self) -> NormalProjectSummary:
        project = self._current_project_get_service.execute()
        return NormalProjectSummary(
            project_id=project.project_id,
            target_number=int(project.target_id),
            zip_name=project.zip_name,
            open_at=project.open_at,
        )


class CurrentProjectInitializeStaticUseCase:
    # プロジェクトの静的データを初期化するユースケース

    def __init__(
            self,
            *,
            manaba_report_archive_gateway: ManabaReportArchiveGateway,
            readonly_excel_worksheet_gateway: ReadonlyExcelWorksheetGateway,
            manaba_report_list_parser: ManabaReportListParser,
            manaba_report_list_archive_validate_service: ManabaReportListArchiveValidateService,
            student_master_create_service: StudentMasterCreateService,
            student_submission_extract_service: StudentSubmissionExtractService,
            current_project_set_initialized_service: CurrentProjectSetInitializedService,
    ):
        self._manaba_report_archive_gateway = manaba_report_archive_gateway
        self._readonly_excel_worksheet_gateway = readonly_excel_worksheet_gateway
        self._manaba_report_list_parser = manaba_report_list_parser
        self._manaba_report_list_archive_validate_service = manaba_report_list_archive_validate_service
        self._student_master_create_service = student_master_create_service
        self._student_submission_extract_service = student_submission_extract_service
        self._current_project_set_initialized_service = current_project_set_initialized_service

    def execute(
            self,
            *,
            manaba_report_archive_fullpath: Path,
            progress_callback: ProgressCallback | None = None,
    ) -> ProjectInitializeResult:
        try:
            # 初期化の前半は「入力アーカイブの妥当性検証と中間表現への変換」。
            if progress_callback is not None:
                progress_callback("提出アーカイブを読み込んでいます")
            archive = self._manaba_report_archive_gateway.read_from_path(
                archive_fullpath=manaba_report_archive_fullpath,
            )
            excel_bytes = archive.read_report_list_excel_bytes()

            if progress_callback is not None:
                progress_callback("生徒マスタExcelを読み込んでいます")
            worksheet = self._readonly_excel_worksheet_gateway.read_from_bytes(
                excel_bytes=excel_bytes,
            )
            report_list = self._manaba_report_list_parser.parse_worksheet(
                worksheet=worksheet,
            )
            self._manaba_report_list_archive_validate_service.execute(
                report_list=report_list,
                archive=archive,
            )
        except (
                ManabaReportArchiveError,
                ReadonlyExcelWorksheetGatewayError,
                ManabaReportListParserError,
                ManabaReportListArchiveValidateServiceError,
        ) as e:
            return ProjectInitializeResult.create_error(message=e.reason)

        if progress_callback is not None:
            progress_callback("生徒マスタを生成しています")
        try:
            # 後半は検証済み中間表現を使った永続化・提出物展開。
            self._student_master_create_service.execute(report_list=report_list)
        except StudentMasterServiceError as e:
            return ProjectInitializeResult.create_error(
                message=e.reason,
            )
        if progress_callback is not None:
            progress_callback("生徒の提出ファイルを展開しています")
        try:
            self._student_submission_extract_service.execute(archive=archive)
        except StudentSubmissionServiceError as e:
            return ProjectInitializeResult.create_error(
                message=e.reason,
            )
        if progress_callback is not None:
            progress_callback("初期化を完了しています")
        self._current_project_set_initialized_service.execute()
        return ProjectInitializeResult.create_success()
