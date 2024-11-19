import io
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from domain.errors import ManabaReportArchiveIOError
from domain.models.values import StudentID
from utils.app_logging import create_logger


class ManabaReportArchiveIO:
    _logger = create_logger()

    def __init__(self, *, manaba_report_archive_fullpath: Path):
        self._archive_fullpath = manaba_report_archive_fullpath

    @contextmanager
    def open_master_excel(self) -> io.BufferedReader:
        with zipfile.ZipFile(self._archive_fullpath, "r") as zf:
            with zf.open("reportlist.xlsx", "r") as f:
                yield f

    def validate_archive_contents(
            self,
            student_submission_folder_names: set[str],
    ) -> None:
        with zipfile.ZipFile(self._archive_fullpath, "r") as f:
            path_it = (Path(name) for name in f.namelist())
            student_submission_folder_names_in_archive: set[str] = set()
            for path in path_it:
                if path == Path("reportlist.xlsx"):
                    continue
                if len(path.parts) > 0:
                    student_submission_folder_names_in_archive.add(path.parts[0])
                else:
                    raise ManabaReportArchiveIOError(
                        reason=f"ZIPファイルに不明なファイルが存在します: {path!s}"
                    )

            set_expected = student_submission_folder_names
            set_actual = student_submission_folder_names_in_archive
            if set_expected - set_actual:
                raise ManabaReportArchiveIOError(
                    reason=f"ZIPファイルの提出フォルダに次の学生の提出フォルダが存在しません。\n"
                           f"{', '.join(set_expected - set_actual)}"
                )
            if set_actual - set_expected:
                raise ManabaReportArchiveIOError(
                    reason=f"ZIPファイルの提出フォルダに予期しない学生の提出フォルダが存在します。\n"
                           f"{', '.join(set_actual - set_expected)}"
                )

    @classmethod
    def _iter_archive_contents(cls, zf_path: Path, zf: zipfile.ZipFile) \
            -> Iterable[tuple[Path, io.BufferedReader]]:
        for info in zf.infolist():
            if info.is_dir():
                continue
            with zf.open(info.filename, "r") as f:
                path = zf_path.parent / zf_path.stem / Path(info.filename)
                assert not path.is_absolute(), path
                yield path, f

    def iter_student_submission_archive_contents(
            self,
            *,
            student_id: StudentID,
            student_submission_folder_name: str,
    ) -> Iterable[tuple[Path, io.BufferedReader]]:  # relative path in archive and fp
        self._logger.debug(f"iter_student_submission_archive_contents\n"
                           f" - {student_id!s} {student_submission_folder_name}")
        # FIXME: manabaのアーカイブがBadZipFileエラーになる（manabaのせい）
        # FIXME: アーカイブを展開して圧縮しなおすとなおるので圧縮しなおしたアーカイブを開けるように対応（暫定対応済み）
        with zipfile.ZipFile(self._archive_fullpath, "r") as zf:
            for name in zf.namelist():
                path = Path(name)
                if len(path.parts) == 0:
                    continue
                if not path.is_relative_to(student_submission_folder_name):
                    continue
                assert len(path.parts) > 0 and path.parts[0] == student_submission_folder_name, path

                child_path = Path(*path.parts[1:])  # remove submission folder part itself
                if len(child_path.parts) == 0:
                    continue
                with zf.open(name, "r") as f:
                    if zipfile.is_zipfile(f):
                        with zipfile.ZipFile(f) as zf_inner:
                            yield from self._iter_archive_contents(
                                child_path.parent / child_path.stem,
                                zf_inner,
                            )
                    else:
                        assert not child_path.is_absolute(), child_path
                        assert child_path.parts[0] == student_submission_folder_name, child_path
                        yield child_path, f
