from functools import cached_property

from application.dependency.usecase import create_current_project_summary_get_usecase, \
    create_student_list_id_usecase, create_student_table_get_student_id_cell_data_usecase, \
    create_student_table_get_student_name_cell_data_usecase, \
    create_student_table_get_student_stage_state_cell_data_usecase, \
    create_student_table_get_student_error_cell_data_usecase, \
    create_student_dynamic_take_diff_snapshot_usecase, create_student_mark_get_usecase, \
    create_student_submission_folder_show_usecase, create_student_run_next_stage_usecase, \
    create_student_stage_result_clear_usecase, create_testcase_config_list_id_usecase, \
    create_student_mark_view_data_get_test_result_usecase, \
    create_student_mark_view_data_get_mark_summary_usecase, \
    create_student_source_code_get_usecase, create_student_mark_put_usecase
from domain.model.value import ProjectID


class ProjectContainer:
    def __init__(self, *, project_id: ProjectID) -> None:
        self._project_id = project_id

    @property
    def project_id(self) -> ProjectID:
        return self._project_id

    @cached_property
    def current_project_summary_get_usecase(self):
        return create_current_project_summary_get_usecase(self._project_id)

    @cached_property
    def student_list_id_usecase(self):
        return create_student_list_id_usecase(self._project_id)

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
        return create_student_dynamic_take_diff_snapshot_usecase(self._project_id)

    @cached_property
    def student_mark_get_usecase(self):
        return create_student_mark_get_usecase(self._project_id)

    @cached_property
    def testcase_config_list_id_usecase(self):
        return create_testcase_config_list_id_usecase(self._project_id)

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
        return create_student_mark_put_usecase(self._project_id)

    @cached_property
    def student_submission_folder_show_usecase(self):
        return create_student_submission_folder_show_usecase(self._project_id)

    @cached_property
    def student_run_next_stage_usecase(self):
        return create_student_run_next_stage_usecase(self._project_id)

    @cached_property
    def student_stage_result_clear_usecase(self):
        return create_student_stage_result_clear_usecase(self._project_id)
