from tests.helpers.archive_assertions import assert_archive_initialization_matches
from tests.helpers.archive_expected import get_expected_master, get_expected_submission_structures


def test_project_initialize_from_report_test_1_archive(
        initialized_project_from_archive,
):
    archive_name = "report-test-1"

    project_container = initialized_project_from_archive(
        archive_name=archive_name,
        project_name="archive_init_report_test_1",
        target_number=2,
    )

    assert_archive_initialization_matches(
        project_container=project_container,
        expected_master=get_expected_master(archive_name),
        expected_submission_structures=get_expected_submission_structures(archive_name),
    )
