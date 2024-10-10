from typing import Callable

from services.student_master_create import StudentMasterCreateService
from services.student_submission_extract import StudentSubmissionExtractService


class ProjectStaticInitializeUseCase:
    # プロジェクトの静的データを初期化するユースケース

    def __init__(
            self,
            *,
            student_master_create_service: StudentMasterCreateService,
            student_submission_extract_service: StudentSubmissionExtractService,
    ):
        self._student_master_create_service = student_master_create_service
        self._student_submission_extract_service = student_submission_extract_service

    def execute(self, callback: Callable[[str], None]) -> None:
        callback("生徒マスタを生成しています")
        self._student_master_create_service.execute()
        callback("生徒の提出ファイルを展開しています")
        self._student_submission_extract_service.execute()
