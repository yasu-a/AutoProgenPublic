import io
import zipfile
from pathlib import PurePosixPath
from typing import NamedTuple, Iterable

from domain.error import ManabaReportArchiveError


class ManabaSubmissionFolderPath(NamedTuple):
    # reportlist 基準の提出フォルダ相対パス。
    value: PurePosixPath


class ManabaSubmissionFile(NamedTuple):
    # 提出フォルダ基準の相対パス。
    relative_path: PurePosixPath
    # ファイル本体バイト列。
    content_bytes: bytes

    def __repr__(self) -> str:
        return (f"ManabaSubmissionFile({self.relative_path}, "
                f"content_bytes=<{len(self.content_bytes)} bytes>)")


class ManabaReportArchive:
    # reportlist の固定ファイル名。
    _REPORT_LIST_EXCEL_FILENAME = "reportlist.xlsx"

    def __init__(self, *, archive_bytes: bytes) -> None:
        # ZIP全体を bytes で保持し、必要時に遅延で読み出す。
        self._archive_bytes = archive_bytes

    def _open_zip(self) -> zipfile.ZipFile:
        # archive bytes を毎回 ZipFile として開くことで、上位層は Path/IO を持たずに済む。
        try:
            return zipfile.ZipFile(io.BytesIO(self._archive_bytes), "r")
        except zipfile.BadZipFile:
            raise ManabaReportArchiveError(reason="提出アーカイブが破損しています")

    def _find_report_list_excel_in_archive(self) -> PurePosixPath:  # ZIPルートからの相対パスを返す
        # reportlist.xlsx の探索基準は「ファイル名一致」で、配置階層は固定しない。
        with self._open_zip() as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                path = PurePosixPath(info.filename)
                if path.name == self._REPORT_LIST_EXCEL_FILENAME:
                    return path
        raise ManabaReportArchiveError(
            reason=f"提出アーカイブに生徒マスタExcelファイル\"{self._REPORT_LIST_EXCEL_FILENAME}\"が存在しません",
        )

    def get_report_list_excel_directory_relative_path(self) -> PurePosixPath:
        # 提出フォルダ探索の基準となる親フォルダを返す。
        return self._find_report_list_excel_in_archive().parent

    def read_report_list_excel_bytes(self) -> bytes:
        # reportlist.xlsx の内容を bytes で返す。
        report_list_path = self._find_report_list_excel_in_archive()
        try:
            with self._open_zip() as zf:
                return zf.read(str(report_list_path))
        except KeyError:
            raise ManabaReportArchiveError(
                reason=f"提出アーカイブに生徒マスタExcelファイル\"{self._REPORT_LIST_EXCEL_FILENAME}\"が存在しません",
            )

    def get_submission_folder_paths(self) -> set[ManabaSubmissionFolderPath]:
        # reportlist.xlsx と同じ親フォルダ配下の 1 階層目を提出フォルダ集合とみなす。
        base = self.get_report_list_excel_directory_relative_path()
        result: set[ManabaSubmissionFolderPath] = set()
        with self._open_zip() as zf:
            for info in zf.infolist():
                path = PurePosixPath(info.filename)
                if not path.is_relative_to(base):
                    continue
                rel = path.relative_to(base)
                if len(rel.parts) == 0:
                    continue
                if rel.name == self._REPORT_LIST_EXCEL_FILENAME:
                    continue
                result.add(ManabaSubmissionFolderPath(PurePosixPath(rel.parts[0])))
        return result

    @classmethod
    def _iter_inner_archive_files(
            cls,
            *,
            outer_zip_entry_path: PurePosixPath,
            zip_bytes: bytes,
    ) -> Iterable[ManabaSubmissionFile]:
        # 既存互換として、入れ子 ZIP は 1 段だけ展開する。
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf_inner:
                for info in zf_inner.infolist():
                    if info.is_dir():
                        continue
                    inner_rel = outer_zip_entry_path / PurePosixPath(info.filename)
                    yield ManabaSubmissionFile(
                        relative_path=inner_rel,
                        content_bytes=zf_inner.read(info.filename),
                    )
        except zipfile.BadZipFile:
            raise ManabaReportArchiveError(
                reason=f"提出アーカイブ内のZIPファイルが破損しています: {outer_zip_entry_path!s}",
            )

    @classmethod
    def _iter_parent_dirs(
            cls,
            *,
            relative_path: PurePosixPath,
    ) -> Iterable[PurePosixPath]:
        # a/b/c.txt -> a, a/b を順に返す。
        if len(relative_path.parts) <= 1:
            return
        for i in range(1, len(relative_path.parts)):
            yield PurePosixPath(*relative_path.parts[:i])

    @classmethod
    def _iter_inner_archive_folders(
            cls,
            *,
            outer_zip_entry_path: PurePosixPath,
            zip_bytes: bytes,
    ) -> Iterable[PurePosixPath]:
        # 入れ子 ZIP も仮想フォルダとして展開先のフォルダ構造へ反映する。
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf_inner:
                yielded: set[PurePosixPath] = set()
                for info in zf_inner.infolist():
                    inner_path = PurePosixPath(info.filename)
                    if info.is_dir():
                        rel_dir = outer_zip_entry_path / inner_path
                        rel_dir = PurePosixPath(*rel_dir.parts)
                        if len(rel_dir.parts) == 0 or rel_dir in yielded:
                            continue
                        yielded.add(rel_dir)
                        yield rel_dir
                        continue

                    rel_file = outer_zip_entry_path / inner_path
                    for rel_dir in cls._iter_parent_dirs(relative_path=rel_file):
                        if rel_dir in yielded:
                            continue
                        yielded.add(rel_dir)
                        yield rel_dir
        except zipfile.BadZipFile:
            raise ManabaReportArchiveError(
                reason=f"提出アーカイブ内のZIPファイルが破損しています: {outer_zip_entry_path!s}",
            )

    def iter_folders_in_submission_folder(
            self,
            *,
            submission_folder_path: ManabaSubmissionFolderPath,
    ) -> Iterable[PurePosixPath]:
        # 指定提出フォルダ配下のフォルダを列挙する（空フォルダを含む）。
        base = self.get_report_list_excel_directory_relative_path() / submission_folder_path.value
        yielded: set[PurePosixPath] = set()

        with self._open_zip() as zf:
            for info in zf.infolist():
                path = PurePosixPath(info.filename)
                if not path.is_relative_to(base):
                    continue
                rel = path.relative_to(base)
                if len(rel.parts) == 0:
                    continue

                if info.is_dir():
                    if rel not in yielded:
                        yielded.add(rel)
                        yield rel
                    continue

                for rel_dir in self._iter_parent_dirs(relative_path=rel):
                    if rel_dir in yielded:
                        continue
                    yielded.add(rel_dir)
                    yield rel_dir

                content_bytes = zf.read(info.filename)
                if zipfile.is_zipfile(io.BytesIO(content_bytes)):
                    # 入れ子 ZIP 名を仮想フォルダとして扱う。
                    if rel not in yielded:
                        yielded.add(rel)
                        yield rel
                    for inner_dir in self._iter_inner_archive_folders(
                            outer_zip_entry_path=rel,
                            zip_bytes=content_bytes,
                    ):
                        if inner_dir in yielded:
                            continue
                        yielded.add(inner_dir)
                        yield inner_dir

    def iter_files_in_submission_folder(
            self,
            *,
            submission_folder_path: ManabaSubmissionFolderPath,
    ) -> Iterable[ManabaSubmissionFile]:
        # 指定提出フォルダ配下のファイルを列挙する。
        base = self.get_report_list_excel_directory_relative_path() / submission_folder_path.value
        with self._open_zip() as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                path = PurePosixPath(info.filename)
                if not path.is_relative_to(base):
                    continue
                rel = path.relative_to(base)
                content_bytes = zf.read(info.filename)
                if zipfile.is_zipfile(io.BytesIO(content_bytes)):
                    # submit.zip/prog01.c のように ZIP 名を仮想フォルダとして相対パスに残す。
                    yield from self._iter_inner_archive_files(
                        outer_zip_entry_path=rel,
                        zip_bytes=content_bytes,
                    )
                    continue
                yield ManabaSubmissionFile(
                    relative_path=rel,
                    content_bytes=content_bytes,
                )
