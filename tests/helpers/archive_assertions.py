from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from domain.model.value import StudentID
from tests.helpers.archive_expected import ExpectedArchiveStudentMaster, ExpectedSubmissionStructure

if TYPE_CHECKING:
    from application.container import ProjectContainer


def assert_project_initialized(project_container: "ProjectContainer") -> None:
    project = project_container.current_project_repository.get()
    assert project.is_initialized


def assert_student_master_matches(
        *,
        project_container: "ProjectContainer",
        expected_master: ExpectedArchiveStudentMaster,
) -> None:
    actual_students = project_container.student_repository.list()

    actual_ids = {
        str(student.student_id)
        for student in actual_students
    }

    assert actual_ids == expected_master.student_ids

    for expected in expected_master.students:
        student = project_container.student_repository.get(
            StudentID(expected.student_id)
        )

        assert str(student.student_id) == expected.student_id
        assert student.name == expected.name
        assert student.name_en == expected.name_en
        assert student.email_address == expected.email_address
        assert student.submitted_at == expected.submitted_at
        assert student.num_submissions == expected.num_submissions
        assert student.submission_folder_name == expected.submission_folder_name

    for non_student_id in expected_master.non_student_ids:
        assert non_student_id not in actual_ids


def assert_submission_folders_match(
        *,
        project_container: "ProjectContainer",
        expected_master: ExpectedArchiveStudentMaster,
) -> None:
    for expected in expected_master.students:
        student_id = StudentID(expected.student_id)
        submission_dir = project_container.project_path_layout.student_submission_dir(
            student_id
        )

        if expected.submission_folder_name is None:
            assert not submission_dir.exists()
        else:
            assert submission_dir.is_dir()
            assert any(path.is_file() for path in submission_dir.rglob("*"))


def assert_submission_structures_match(
        *,
        project_container: "ProjectContainer",
        expected_submission_structures: tuple[ExpectedSubmissionStructure, ...],
) -> None:
    expected_by_student_id = {
        expected.student_id: expected
        for expected in expected_submission_structures
    }

    for student_id_text in expected_by_student_id:
        expected = expected_by_student_id[student_id_text]
        student_id = StudentID(student_id_text)
        submission_dir = project_container.project_path_layout.student_submission_dir(
            student_id
        )
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


def assert_archive_initialization_matches(
        *,
        project_container: "ProjectContainer",
        expected_master: ExpectedArchiveStudentMaster,
        expected_submission_structures: tuple[ExpectedSubmissionStructure, ...] = tuple(),
) -> None:
    assert_project_initialized(project_container)

    assert_student_master_matches(
        project_container=project_container,
        expected_master=expected_master,
    )

    assert_submission_folders_match(
        project_container=project_container,
        expected_master=expected_master,
    )

    assert_submission_structures_match(
        project_container=project_container,
        expected_submission_structures=expected_submission_structures,
    )
