from functools import cached_property
from pathlib import Path

from application.dependency.repository import create_current_project_repository, create_student_repository, \
    create_student_stage_path_result_repository, create_testcase_config_repository, create_storage_repository, \
    create_student_executable_repository, create_student_source_repository, create_student_mark_repository
from application.dependency.usecase import create_current_project_summary_get_usecase, \
    create_current_project_initialize_static_usecase, \
    create_student_table_get_student_id_cell_data_usecase, \
    create_student_table_get_student_name_cell_data_usecase, \
    create_student_table_get_student_stage_state_cell_data_usecase, \
    create_student_table_get_student_error_cell_data_usecase, \
    create_student_submission_folder_show_usecase, create_student_run_next_stage_usecase, \
    create_student_stage_result_clear_usecase, \
    create_student_mark_view_data_get_test_result_usecase, \
    create_student_mark_view_data_get_mark_summary_usecase, \
    create_student_source_code_get_usecase
from domain.model.value import ProjectID
from service.student import StudentListSubService
from service.student_mark import StudentMarkGetSubService, StudentMarkPutService, StudentMarkListService, \
    StudentMarkCheckTimestampQueryService
from service.student_stage_path_result import StudentStageResultCheckTimestampQueryService
from usecase.student import StudentListIDUseCase
from usecase.student_dynamic import StudentDynamicTakeDiffSnapshotUseCase
from usecase.student_mark import StudentMarkGetUseCase, StudentMarkListUseCase, StudentMarkPutUseCase
from usecase.testcase_config import TestCaseDeleteUseCase, TestCaseGetUseCase, TestCaseListIDUseCase, \
    TestCasePutUseCase
from usecase.testcase_list_edit import TestCaseListSummaryUseCase, TestCaseCreateNewNameUseCase, TestCaseCreateUseCase, \
    TestCaseCopyUseCase
from service.testcase_config import TestCaseConfigCopyService


class ProjectContainer:
    def __init__(self, *, project_id: ProjectID) -> None:
        self._project_id = project_id

    @property
    def project_id(self) -> ProjectID:
        return self._project_id

    @cached_property
    def current_project_repository(self):
        return create_current_project_repository(self._project_id)

    @cached_property
    def student_repository(self):
        return create_student_repository(self._project_id)

    @cached_property
    def student_stage_path_result_repository(self):
        return create_student_stage_path_result_repository(self._project_id)

    @cached_property
    def testcase_config_repository(self):
        return create_testcase_config_repository(self._project_id)

    @cached_property
    def storage_repository(self):
        return create_storage_repository(self._project_id)

    @cached_property
    def student_executable_repository(self):
        return create_student_executable_repository(self._project_id)

    @cached_property
    def student_source_repository(self):
        return create_student_source_repository(self._project_id)

    @cached_property
    def student_mark_repository(self):
        return create_student_mark_repository(self._project_id)

    @cached_property
    def current_project_summary_get_usecase(self):
        return create_current_project_summary_get_usecase(self._project_id)

    def create_current_project_initialize_static_usecase(self, *, manaba_report_archive_fullpath: Path):
        return create_current_project_initialize_static_usecase(
            project_id=self._project_id,
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        )

    @cached_property
    def student_list_id_usecase(self):
        return StudentListIDUseCase(
            student_list_sub_service=StudentListSubService(
                student_repo=self.student_repository,
            ),
        )

    @cached_property
    def student_table_get_student_id_cell_data_usecase(self):
        return create_student_table_get_student_id_cell_data_usecase(self._project_id)

    @cached_property
    def student_table_get_student_name_cell_data_usecase(self):
        return create_student_table_get_student_name_cell_data_usecase(self._project_id)

    @cached_property
    def student_table_get_student_stage_state_cell_data_usecase(self):
        return create_student_table_get_student_stage_state_cell_data_usecase(self._project_id)

    @cached_property
    def student_table_get_student_error_cell_data_usecase(self):
        return create_student_table_get_student_error_cell_data_usecase(self._project_id)

    @cached_property
    def student_dynamic_take_diff_snapshot_usecase(self):
        return StudentDynamicTakeDiffSnapshotUseCase(
            student_stage_result_check_timestamp_query_service=StudentStageResultCheckTimestampQueryService(
                student_stage_path_result_repo=self.student_stage_path_result_repository,
            ),
            student_mark_check_timestamp_query_service=StudentMarkCheckTimestampQueryService(
                student_mark_repo=self.student_mark_repository,
            ),
        )

    @cached_property
    def student_mark_get_usecase(self):
        return StudentMarkGetUseCase(
            student_mark_get_sub_service=StudentMarkGetSubService(
                student_mark_repo=self.student_mark_repository,
            ),
        )

    @cached_property
    def student_mark_list_usecase(self):
        return StudentMarkListUseCase(
            student_mark_list_service=StudentMarkListService(
                student_list_sub_service=StudentListSubService(
                    student_repo=self.student_repository,
                ),
                student_mark_get_sub_service=StudentMarkGetSubService(
                    student_mark_repo=self.student_mark_repository,
                ),
            ),
        )

    @cached_property
    def testcase_config_list_id_usecase(self):
        return TestCaseListIDUseCase(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def student_mark_view_data_get_test_result_usecase(self):
        return create_student_mark_view_data_get_test_result_usecase(self._project_id)

    @cached_property
    def student_mark_view_data_get_mark_summary_usecase(self):
        return create_student_mark_view_data_get_mark_summary_usecase(self._project_id)

    @cached_property
    def student_source_code_get_usecase(self):
        return create_student_source_code_get_usecase(self._project_id)

    @cached_property
    def student_mark_put_usecase(self):
        return StudentMarkPutUseCase(
            student_mark_put_service=StudentMarkPutService(
                student_mark_repo=self.student_mark_repository,
            ),
        )

    @cached_property
    def student_submission_folder_show_usecase(self):
        return create_student_submission_folder_show_usecase(self._project_id)

    @cached_property
    def student_run_next_stage_usecase(self):
        return create_student_run_next_stage_usecase(self._project_id)

    @cached_property
    def student_stage_result_clear_usecase(self):
        return create_student_stage_result_clear_usecase(self._project_id)

    @cached_property
    def testcase_list_summary_usecase(self):
        return TestCaseListSummaryUseCase(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def testcase_create_new_name_usecase(self):
        return TestCaseCreateNewNameUseCase(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def testcase_create_usecase(self):
        return TestCaseCreateUseCase(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def testcase_copy_usecase(self):
        return TestCaseCopyUseCase(
            testcase_config_copy_service=TestCaseConfigCopyService(
                testcase_config_repo=self.testcase_config_repository,
            ),
        )

    @cached_property
    def testcase_delete_usecase(self):
        return TestCaseDeleteUseCase(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def testcase_get_usecase(self):
        return TestCaseGetUseCase(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def testcase_put_usecase(self):
        return TestCasePutUseCase(
            testcase_config_repo=self.testcase_config_repository,
        )
