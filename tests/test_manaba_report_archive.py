import io
import zipfile
from pathlib import PurePosixPath

import pytest

from domain.error import ManabaReportArchiveError
from domain.model.manaba_report_archive import ManabaReportArchive, ManabaSubmissionFolderPath


def _zip_bytes(entries: list[tuple[str, bytes]]) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in entries:
            zf.writestr(name, content)
    return bio.getvalue()

# TODO: 2重zipの展開テストを追加

def test_manaba_report_archive_reads_report_list_excel_bytes() -> None:
    archive = ManabaReportArchive(
        archive_bytes=_zip_bytes(
            [
                ("root/reportlist.xlsx", b"excel-bytes"),
                ("root/21D5109047B@21D5109047B/prog01.c", b"int main(){}"),
            ]
        )
    )

    assert archive.read_report_list_excel_bytes() == b"excel-bytes"


def test_manaba_report_archive_raises_when_report_list_not_found() -> None:
    archive = ManabaReportArchive(
        archive_bytes=_zip_bytes(
            [("root/not_reportlist.xlsx", b"x")]
        )
    )

    with pytest.raises(ManabaReportArchiveError) as exc_info:
        archive.read_report_list_excel_bytes()

    assert "reportlist.xlsx" in exc_info.value.reason


def test_manaba_report_archive_lists_submission_folders() -> None:
    archive = ManabaReportArchive(
        archive_bytes=_zip_bytes(
            [
                ("root/reportlist.xlsx", b"x"),
                ("root/21D5109047B@21D5109047B/prog01.c", b"1"),
                ("root/25D5203184K@25D5203184K/prog01.c", b"2"),
            ]
        )
    )

    actual = archive.get_submission_folder_paths()
    expected = {
        ManabaSubmissionFolderPath(PurePosixPath("21D5109047B@21D5109047B")),
        ManabaSubmissionFolderPath(PurePosixPath("25D5203184K@25D5203184K")),
    }
    assert actual == expected


def test_manaba_report_archive_iter_folders_includes_empty_folder() -> None:
    archive = ManabaReportArchive(
        archive_bytes=_zip_bytes(
            [
                ("root/reportlist.xlsx", b"x"),
                ("root/21D5109047B@21D5109047B/empty/", b""),
                ("root/21D5109047B@21D5109047B/src/prog01.c", b"int main(){}"),
            ]
        )
    )
    folder = ManabaSubmissionFolderPath(PurePosixPath("21D5109047B@21D5109047B"))

    folders = set(archive.iter_folders_in_submission_folder(submission_folder_path=folder))
    assert PurePosixPath("empty") in folders
    assert PurePosixPath("src") in folders


def test_manaba_report_archive_iter_files_expands_nested_zip_one_level() -> None:
    inner_zip = _zip_bytes(
        [
            ("prog01.c", b"int main(){return 0;}"),
            ("sub/helper.txt", b"helper"),
        ]
    )
    archive = ManabaReportArchive(
        archive_bytes=_zip_bytes(
            [
                ("root/reportlist.xlsx", b"x"),
                ("root/21D5109047B@21D5109047B/submit.zip", inner_zip),
            ]
        )
    )
    folder = ManabaSubmissionFolderPath(PurePosixPath("21D5109047B@21D5109047B"))

    files = list(archive.iter_files_in_submission_folder(submission_folder_path=folder))
    paths = {f.relative_path for f in files}
    assert PurePosixPath("submit.zip/prog01.c") in paths
    assert PurePosixPath("submit.zip/sub/helper.txt") in paths


def test_manaba_report_archive_raises_on_broken_archive() -> None:
    archive = ManabaReportArchive(archive_bytes=b"not-a-zip")

    with pytest.raises(ManabaReportArchiveError) as exc_info:
        _ = archive.get_submission_folder_paths()

    assert "破損" in exc_info.value.reason


def test_manaba_report_archive_raises_on_broken_nested_zip() -> None:
    archive = ManabaReportArchive(
        archive_bytes=_zip_bytes(
            [
                ("root/reportlist.xlsx", b"x"),
                ("root/21D5109047B@21D5109047B/submit.zip", b"not-a-zip"),
            ]
        )
    )
    folder = ManabaSubmissionFolderPath(PurePosixPath("21D5109047B@21D5109047B"))

    with pytest.raises(ManabaReportArchiveError) as exc_info:
        _ = list(archive.iter_files_in_submission_folder(submission_folder_path=folder))

    assert "破損" in exc_info.value.reason
