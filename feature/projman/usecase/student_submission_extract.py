from pathlib import PurePosixPath
from typing import Iterable, IO

from feature.projman.usecase.interface import IStudentSubmissionExtractUseCase
from shared.domain.error import ManabaReportArchiveIOError, StudentSubmissionServiceError
from shared.domain.value.identifier import StudentID
from shared.infra.system.current_project_core_io import CurrentProjectCoreIO
from shared.infra.system.report_archive import ManabaReportArchiveIO
from shared.infra.path_provider.current_project import StudentSubmissionPathProvider
from shared.infra.repository.student import StudentRepository
from util.app_logging import create_logger


class StudentSubmissionExtractUseCase(IStudentSubmissionExtractUseCase):
    _logger = create_logger()

    def __init__(
            self,
            *,
            student_repo: StudentRepository,
            manaba_report_archive_io: ManabaReportArchiveIO,
            current_project_core_io: CurrentProjectCoreIO,
            student_submission_path_provider: StudentSubmissionPathProvider,
    ):
        self._student_repo = student_repo
        self._manaba_report_archive_io = manaba_report_archive_io
        self._current_project_core_io = current_project_core_io
        self._student_submission_path_provider = student_submission_path_provider

    def execute(self):
        if not self._student_repo.exists_any():
            raise StudentSubmissionServiceError("生徒マスタが作成されていません")

        # 生徒マスタを読み込んで生徒ID→提出フォルダ名のマッピングを作る
        student_master = self._student_repo.list()
        student_id_to_submission_folder_name_mapping: dict[StudentID, str] = {}
        for StudentEntity in student_master:
            if StudentEntity.submission_folder_name is not None:
                student_id_to_submission_folder_name_mapping[StudentEntity.student_id] \
                    = StudentEntity.submission_folder_name

        # 生徒の提出物を展開する
        try:
            self._manaba_report_archive_io.validate_master_excel_exists()
            self._manaba_report_archive_io.validate_archive_contents(
                student_submission_folder_names=set(
                    student_id_to_submission_folder_name_mapping.values()
                ),
            )

            for student_id, student_submission_folder_name in \
                    student_id_to_submission_folder_name_mapping.items():
                # 生徒の展開先のフォルダのフルパス
                extract_base_folder_fullpath = (
                    self._student_submission_path_provider.student_submission_folder_fullpath(
                        student_id=student_id,
                    )
                )
                # 展開先のフォルダが存在しなかったらフォルダを生成
                extract_base_folder_fullpath.mkdir(parents=True, exist_ok=False)
                # 生徒のアーカイブ内のファイルの相対パスとファイルポインタのイテラブルを取得
                it: Iterable[tuple[PurePosixPath, IO[bytes]]] = (
                    self._manaba_report_archive_io.iter_student_submission_archive_contents(
                        student_id=student_id,
                        student_submission_folder_name=student_submission_folder_name,
                    )
                )
                # それぞれのファイルを展開する
                for content_relative_path, fp in it:
                    self._logger.info(f"Extracting {student_id} {content_relative_path!s}")
                    # パスにスペースが含まれているとこの先のos.makedirsで失敗するので取り除く
                    content_relative_path = PurePosixPath(
                        *map(str.strip, content_relative_path.parts)
                    )
                    # コピー先のファイルパス
                    dst_file_fullpath = extract_base_folder_fullpath / content_relative_path
                    dst_file_fullpath = dst_file_fullpath.resolve()
                    assert dst_file_fullpath.parent.is_relative_to(
                        extract_base_folder_fullpath
                    ), (dst_file_fullpath, extract_base_folder_fullpath)
                    # 親フォルダを生成
                    dst_file_fullpath.parent.mkdir(parents=True, exist_ok=True)
                    self._current_project_core_io.write_file_content_bytes(
                        file_fullpath=dst_file_fullpath,
                        content_bytes=fp.read(),
                    )
        except ManabaReportArchiveIOError as e:
            raise StudentSubmissionServiceError(
                reason=f"提出アーカイブの展開中にエラーが発生しました。\n{e.reason}",
            )
