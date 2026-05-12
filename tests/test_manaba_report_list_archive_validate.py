from pathlib import PurePosixPath

import pytest

from domain.error import ManabaReportListArchiveValidateServiceError
from domain.model.manaba_report_archive import ManabaSubmissionFolderPath
from domain.model.manaba_report_list import ManabaReportList, ManabaReportListRow
from domain.model.value import StudentID
from service.manaba_report_list_archive_validate import ManabaReportListArchiveValidateService


class _ArchiveStub:
    def __init__(self, folder_paths: set[ManabaSubmissionFolderPath]):
        self._folder_paths = folder_paths

    def get_submission_folder_paths(self) -> set[ManabaSubmissionFolderPath]:
        return self._folder_paths


def test_manaba_report_list_archive_validate_success():
    report_list = ManabaReportList(
        rows=(
            ManabaReportListRow(
                student_id=StudentID("21D5109047B"),
                name="A",
                name_en="A",
                email_address="a@example.com",
                is_submitted=True,
                submitted_at_text="2026-01-01 00:00:00",
                num_submissions_text="1",
                submission_folder_path=PurePosixPath("21D5109047B@21D5109047B"),
            ),
        ),
    )
    archive = _ArchiveStub(
        {
            ManabaSubmissionFolderPath(PurePosixPath("21D5109047B@21D5109047B")),
        }
    )

    ManabaReportListArchiveValidateService().execute(
        report_list=report_list,
        archive=archive,
    )


def test_manaba_report_list_archive_validate_detects_extra_folder():
    report_list = ManabaReportList(rows=tuple())
    archive = _ArchiveStub(
        {
            ManabaSubmissionFolderPath(PurePosixPath("extra@extra")),
        }
    )

    with pytest.raises(ManabaReportListArchiveValidateServiceError) as exc_info:
        ManabaReportListArchiveValidateService().execute(
            report_list=report_list,
            archive=archive,
        )
    e = exc_info.value
    assert "存在しないはずの提出フォルダ" in e.reason
    assert "extra@extra" in e.reason


def test_manaba_report_list_archive_validate_detects_extra_row():
    report_list = ManabaReportList(
        rows=(
            ManabaReportListRow(
                student_id=StudentID("21D5109047B"),
                name="A",
                name_en="A",
                email_address="a@example.com",
                is_submitted=True,
                submitted_at_text="2026-01-01 00:00:00",
                num_submissions_text="1",
                submission_folder_path=PurePosixPath("extra@extra"),
            ),
        ),
    )
    archive = _ArchiveStub(set())

    with pytest.raises(ManabaReportListArchiveValidateServiceError) as exc_info:
        ManabaReportListArchiveValidateService().execute(
            report_list=report_list,
            archive=archive,
        )
    e = exc_info.value
    assert "提出フォルダが存在しません" in e.reason
    assert "extra@extra" in e.reason
