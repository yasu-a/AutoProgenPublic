from pathlib import PurePosixPath

from domain.model.value import StudentID
from tests.helpers.archive_expected import get_expected_master, get_expected_submission_structures


def _run_report_test_1_initialization(
        run_project_initialize_from_archive,
):
    return run_project_initialize_from_archive(
        archive_name="report-test-1",
        project_name="archive_init_report_test_1_full_validation",
        target_number=2,
    )


def test_project_initialize_from_report_test_1_archive_validates_student_master(
        run_project_initialize_from_archive,
):
    run = _run_report_test_1_initialization(
        run_project_initialize_from_archive=run_project_initialize_from_archive,
    )
    assert not run.result.has_error, run.result.message

    project_container = run.project_container
    expected_master = get_expected_master("report-test-1")

    actual_students = project_container.student_repository.list()
    actual_ids = {str(student.student_id) for student in actual_students}
    assert actual_ids == expected_master.student_ids

    for expected in expected_master.students:
        student = project_container.student_repository.get(StudentID(expected.student_id))
        assert str(student.student_id) == expected.student_id
        assert student.name == expected.name
        assert student.name_en == expected.name_en
        assert student.email_address == expected.email_address
        assert student.submitted_at == expected.submitted_at
        assert student.num_submissions == expected.num_submissions
        assert student.submission_folder_name == expected.submission_folder_name


def test_project_initialize_from_report_test_1_archive_validates_extracted_submissions(
        run_project_initialize_from_archive,
):
    run = _run_report_test_1_initialization(
        run_project_initialize_from_archive=run_project_initialize_from_archive,
    )
    assert not run.result.has_error, run.result.message

    project_container = run.project_container
    expected_structures = get_expected_submission_structures("report-test-1")
    expected_by_student_id = {
        expected.student_id: expected
        for expected in expected_structures
    }

    for student_id_text in expected_by_student_id:
        expected = expected_by_student_id[student_id_text]
        student_id = StudentID(student_id_text)
        submission_dir = project_container.project_path_layout.student_submission_dir(student_id)
        assert submission_dir.is_dir()

        actual_file_structure_set = set(
            PurePosixPath(path.as_posix())
            for path in project_container.current_project_core_io.walk_files(
                folder_fullpath=submission_dir,
                return_absolute=False,
            )
        )
        expected_file_structure_set = set(expected.expected_files)

        actual_folder_structure_set = {
            PurePosixPath(path.relative_to(submission_dir).as_posix())
            for path in submission_dir.rglob("*")
            if path.is_dir()
        }
        expected_folder_structure_set = set(expected.expected_dirs)

        assert actual_file_structure_set == expected_file_structure_set
        assert actual_folder_structure_set == expected_folder_structure_set
