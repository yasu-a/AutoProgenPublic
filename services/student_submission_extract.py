import io
from pathlib import Path
from typing import Iterable

from domain.errors import ManabaReportArchiveIOError, ServiceError
from domain.models.values import StudentID
from files.core.current_project import CurrentProjectCoreIO
from files.external.report_archive import ManabaReportArchiveIO
from files.path_providers.current_project import ReportSubmissionPathProvider
from files.repositories.student import StudentRepository


class StudentSubmissionExtractServiceError(ServiceError):
    def __init__(self, reason: str) -> None:
        self.reason = reason


class StudentSubmissionExtractService:
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
            manaba_report_archive_io: ManabaReportArchiveIO,
            current_project_core_io: CurrentProjectCoreIO,
            report_submission_path_provider: ReportSubmissionPathProvider,
    ):
        self._student_repo = student_repo
        self._manaba_report_archive_io = manaba_report_archive_io
        self._current_project_core_io = current_project_core_io
        self._report_submission_path_provider = report_submission_path_provider

    def execute(self):
        if not self._student_repo.exists():
            raise StudentSubmissionExtractServiceError("生徒マスタが存在しません")

        # 生徒マスタを読み込んで生徒ID→提出フォルダ名のマッピングを作る
        student_master = self._student_repo.list()
        student_id_to_submission_folder_name_mapping: dict[StudentID, str] = {}
        for student in student_master:
            if student.submission_folder_name is not None:
                student_id_to_submission_folder_name_mapping[student.student_id] \
                    = student.submission_folder_name

        # 生徒の提出物を展開する
        try:
            self._manaba_report_archive_io.validate_archive_contents(
                student_submission_folder_names=set(
                    student_id_to_submission_folder_name_mapping.values()
                ),
            )

            for student_id, student_submission_folder_name in \
                    student_id_to_submission_folder_name_mapping.items():
                # 生徒の展開先のフォルダのフルパス
                extract_base_folder_fullpath = (
                    self._report_submission_path_provider.student_submission_folder_fullpath(
                        student_id=student_id,
                    )
                )
                # 展開先のフォルダが存在しなかったらフォルダを生成
                extract_base_folder_fullpath.mkdir(parents=True, exist_ok=False)
                # 生徒のアーカイブ内のファイルの相対パスとファイルポインタのイテラブルを取得
                it: Iterable[tuple[Path, io.BufferedReader]] = (
                    self._manaba_report_archive_io.iter_student_submission_archive_contents(
                        student_id=student_id,
                        student_submission_folder_name=student_submission_folder_name,
                    )
                )
                # それぞれのファイルを展開する
                for content_relative_path, fp in it:
                    # パスにスペースが含まれているとこの先のos.makedirsで失敗するので取り除く
                    content_relative_path = Path(*map(str.strip, content_relative_path.parts))
                    # コピー先のファイルパス
                    dst_file_fullpath = extract_base_folder_fullpath / content_relative_path
                    dst_file_fullpath = dst_file_fullpath.resolve()
                    assert dst_file_fullpath.parent.is_relative_to(
                        extract_base_folder_fullpath
                    ), dst_file_fullpath
                    # 親フォルダを生成
                    dst_file_fullpath.parent.mkdir(parents=True, exist_ok=True)
                    self._current_project_core_io.write_file_content_bytes(
                        file_fullpath=dst_file_fullpath,
                        content_bytes=fp.read(),
                    )
        except ManabaReportArchiveIOError as e:
            raise StudentSubmissionExtractServiceError(
                reason=f"ZIPアーカイブの展開中にエラーが発生しました。\n{e.reason}",
            )
