from dataclasses import dataclass
from datetime import datetime

from tests.helpers.archive_names import normalize_archive_name


@dataclass(frozen=True)
class ExpectedStudent:
    student_id: str
    name: str
    name_en: str
    email_address: str
    submitted_at: datetime | None
    num_submissions: int
    submission_folder_name: str | None


@dataclass(frozen=True)
class ExpectedArchiveStudentMaster:
    students: tuple[ExpectedStudent, ...]
    non_student_ids: frozenset[str]

    @property
    def student_ids(self) -> set[str]:
        return {
            student.student_id
            for student in self.students
        }


REPORT_TEST_1_EXPECTED_MASTER = ExpectedArchiveStudentMaster(
    students=(
        ExpectedStudent(
            student_id="21D5109047B",
            name="範馬　刃牙",
            name_en="HANMA Baki",
            email_address="a21.4a8d@g.chuo-u.ac.jp",
            submitted_at=datetime(2026, 4, 17, 16, 56, 13),
            num_submissions=1,
            submission_folder_name="21D5109047B@21D5109047B",
        ),
        ExpectedStudent(
            student_id="25D5203184K",
            name="範馬　勇次郎",
            name_en="HANMA Yujiro",
            email_address="a25.kjgl@g.chuo-u.ac.jp",
            submitted_at=datetime(2026, 4, 17, 16, 46, 38),
            num_submissions=1,
            submission_folder_name="25D5203184K@25D5203184K",
        ),
        ExpectedStudent(
            student_id="26HG209871C",
            name="花山　薫",
            name_en="HANAYAMA Kaoru",
            email_address="a26.keu4@g.chuo-u.ac.jp",
            submitted_at=datetime(2026, 4, 17, 17, 5, 1),
            num_submissions=1,
            submission_folder_name="26HG209871C@26HG209871C",
        ),
        ExpectedStudent(
            student_id="26HJ403216F",
            name="烈　海王",
            name_en="RETSU Kaioh",
            email_address="a26.lwpf@g.chuo-u.ac.jp",
            submitted_at=None,
            num_submissions=0,
            submission_folder_name=None,
        ),
        ExpectedStudent(
            student_id="24A0007521M",
            name="愚地　独歩",
            name_en="OROCHI Doppo",
            email_address="a25.le59@g.chuo-u.ac.jp",
            submitted_at=datetime(2026, 4, 17, 17, 0, 55),
            num_submissions=1,
            submission_folder_name="24A0007521M@24A0007521M",
        ),
    ),
    non_student_ids=frozenset(
        {
            "25N5100004E",  # 授業補助者
            "26N5100074F",  # 授業補助者
            "AA1423",       # 担当教員
        }
    ),
)


_EXPECTED_MASTER_BY_ARCHIVE_NAME: dict[str, ExpectedArchiveStudentMaster] = {
    "report-test-1.zip": REPORT_TEST_1_EXPECTED_MASTER,
}


def get_expected_master(archive_name: str) -> ExpectedArchiveStudentMaster:
    normalized_archive_name = normalize_archive_name(archive_name)
    try:
        return _EXPECTED_MASTER_BY_ARCHIVE_NAME[normalized_archive_name]
    except KeyError:
        known_names = ", ".join(sorted(_EXPECTED_MASTER_BY_ARCHIVE_NAME))
        raise AssertionError(
            f"Unknown archive expected data: {normalized_archive_name}\n"
            f"Known archive names: {known_names}"
        ) from None
