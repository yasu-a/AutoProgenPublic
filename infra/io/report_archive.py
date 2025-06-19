import io
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterable, ContextManager, Generator, IO

from domain.errors import ManabaReportArchiveIOError
from domain.models.values import StudentID
from utils.app_logging import create_logger


class ManabaReportArchiveIO:
    _logger = create_logger()

    def __init__(self, *, manaba_report_archive_fullpath: Path):
        self._archive_fullpath = manaba_report_archive_fullpath

    _MASTER_EXCEL_FILENAME = "reportlist.xlsx"

    def _get_master_excel_relative_path(self) -> PurePosixPath:
        # マスタexcelがあるフォルダ
        with zipfile.ZipFile(self._archive_fullpath, "r") as zf:
            for info in zf.infolist():
                # ディレクトリは飛ばす
                if info.is_dir():
                    continue

                # ファイル名がマスターexcelのファイル名と一致
                path = PurePosixPath(info.filename)
                if path.name == self._MASTER_EXCEL_FILENAME:
                    return path
        raise ManabaReportArchiveIOError(
            reason=f"提出アーカイブに生徒マスタExcelファイル\"{self._MASTER_EXCEL_FILENAME}\"が存在しません",
        )

    def _get_master_excel_folder_relative_path(self) -> PurePosixPath:
        return self._get_master_excel_relative_path().parent

    @contextmanager
    def open_master_excel(self) -> Generator[IO[bytes], None, None]:
        with zipfile.ZipFile(self._archive_fullpath, "r") as zf:
            with zf.open(str(self._get_master_excel_relative_path()), "r") as f:
                yield f

    def validate_master_excel_exists(self) -> bool:
        try:
            self._get_master_excel_relative_path()
        except ManabaReportArchiveIOError:
            return False
        else:
            return True

    def validate_archive_contents(
            self,
            student_submission_folder_names: set[str],
    ) -> None:
        master_excel_folder_relative_path = self._get_master_excel_folder_relative_path()

        with zipfile.ZipFile(self._archive_fullpath, "r") as f:
            path_it = (PurePosixPath(name) for name in f.namelist())
            student_submission_folder_names_in_archive: set[str] = set()
            for path in path_it:
                # マスタexcelがあるフォルダから調べる
                if not path.is_relative_to(master_excel_folder_relative_path):
                    continue
                relative_path = path.relative_to(master_excel_folder_relative_path)
                # マスタexcelの名前と一致するファイルは飛ばす
                if relative_path.name == self._MASTER_EXCEL_FILENAME:
                    continue
                # "." はとばす
                if len(relative_path.parts) == 0:
                    continue
                student_submission_folder_names_in_archive.add(relative_path.parts[0])

            set_expected = student_submission_folder_names
            set_actual = student_submission_folder_names_in_archive
            if set_expected - set_actual:
                raise ManabaReportArchiveIOError(
                    reason=f"提出アーカイブの提出フォルダに次の学生の提出フォルダが存在しません。\n"
                           f"{', '.join(set_expected - set_actual)}"
                )
            if set_actual - set_expected:
                raise ManabaReportArchiveIOError(
                    reason=f"提出アーカイブの提出フォルダに存在しないはずの提出フォルダが存在します。\n"
                           f"{', '.join(set_actual - set_expected)}"
                )

    @classmethod
    def _iter_archive_contents(cls, zf_path: PurePosixPath, zf: zipfile.ZipFile) \
            -> Iterable[tuple[PurePosixPath, IO[bytes]]]:
        for info in zf.infolist():
            if info.is_dir():
                continue
            with zf.open(info.filename, "r") as f:
                path = zf_path.parent / zf_path.name / PurePosixPath(info.filename)
                assert not path.is_absolute(), path
                yield path, f

    def iter_student_submission_archive_contents(
            self,
            *,
            student_id: StudentID,
            student_submission_folder_name: str,
    ) -> Iterable[tuple[PurePosixPath, io.BufferedReader]]:  # [^]
        # ^ relative path in student folder in archive and fp

        self._logger.info(f"iter_student_submission_archive_contents\n"
                          f" - {student_id!s} {student_submission_folder_name}")

        master_excel_folder_relative_path = self._get_master_excel_folder_relative_path()
        student_submission_folder_relative_path \
            = master_excel_folder_relative_path / student_submission_folder_name

        try:
            with zipfile.ZipFile(self._archive_fullpath, "r") as zf:
                for info in zf.infolist():
                    # フォルダは飛ばす
                    if info.is_dir():
                        continue
                    path = PurePosixPath(info.filename)
                    # 生徒のフォルダだけ見る
                    if not path.is_relative_to(student_submission_folder_relative_path):
                        continue
                    relative_path = path.relative_to(student_submission_folder_relative_path)
                    # ファイルを開く
                    with zf.open(info.filename, "r") as f:
                        if zipfile.is_zipfile(f):
                            # zipファイル
                            with zipfile.ZipFile(f) as zf_inner:
                                for path_inner, f_inner in self._iter_archive_contents(
                                        path,
                                        zf_inner,
                                ):
                                    relative_path_inner = path_inner.relative_to(
                                        student_submission_folder_relative_path,
                                    )
                                    yield relative_path_inner, f_inner
                        else:
                            yield relative_path, f
        except zipfile.BadZipFile:
            self._logger.exception(f"BadZipFile: {student_id!s} {student_submission_folder_name}")
            raise ManabaReportArchiveIOError(
                reason=f"提出アーカイブが破損しています",
            )
