from app.di.event import get_event_bus
from app.di.gateway import *
from app.di.path_config import get_path_config
from app.di.provider import get_app_name_provider, get_app_version_provider
from app.di.service import *
from app.di.state import get_current_project_id_state
from app.di.system import get_manaba_report_archive_io, get_current_project_core_io
from feature.about.usecase.get_about_info import GetAboutInfoUseCase
from feature.export.usecase.excel.detect_layout import AutoDetectExcelLayoutUseCase
from feature.export.usecase.excel.execute import ExecuteExcelScoreUpdateUseCase
from feature.export.usecase.excel.get_preview import ListExcelWorksheetUseCase, \
    GetExcelSheetPreviewUseCase
from feature.export.usecase.setting import ExportSettingGetUseCase
from feature.export.usecase.simple.execute import ExecuteSimpleScoreExportUseCase
from feature.export.usecase.simple.get_data import GetSimpleScoreExportDataUseCase
from feature.projman.usecase.current_project import CurrentProjectSummaryGetUseCase, \
    CurrentProjectInitializeStaticUseCase
from feature.projman.usecase.project import ProjectCheckExistByNameUseCase, ProjectCreateUseCase, \
    ProjectListRecentSummaryUseCase, ProjectBaseFolderShowUseCase, \
    ProjectFolderShowUseCase, ProjectDeleteUseCase, ProjectGetSizeQueryUseCase, \
    ProjectUpdateLastOpenUseCase
from feature.projman.usecase.student_master_create import StudentMasterCreateUseCase
from feature.projman.usecase.student_submission_extract import StudentSubmissionExtractUseCase
from feature.scoring.usecase.student_mark import StudentMarkGetUseCase, StudentMarkPutUseCase, \
    StudentScoreListUseCase
from feature.scoring.usecase.student_mark_view_data import StudentMarkViewDataGetTestResultUseCase, \
    StudentMarkViewDataGetMarkSummaryUseCase
from feature.scoring.usecase.student_source_code import StudentSourceCodeGetUseCase
from feature.setting.usecase.compiler_search import CompilerSearchUseCase
from feature.setting.usecase.setting import SettingGetUseCase, \
    SettingPutUseCase
from feature.setting.usecase.test_compile_stage import TestCompileStageUseCase
from feature.testcase.usecase.test_test_stage import TestTestStageUseCase
from feature.testcase.usecase.testcase_config import TestCaseConfigGetUseCase, \
    TestCaseConfigPutUseCase, \
    TestCaseConfigListIDUseCase
from feature.testcase.usecase.testcase_list_edit import TestCaseListSummaryUseCase, \
    TestCaseCreateNewNameUseCase, TestCaseCreateUseCase, \
    TestCaseCopyUseCase
from feature.workspace.usecase.resource_usage import ResourceUsageGetUseCase
from feature.workspace.usecase.student import StudentListIDUseCase
from feature.workspace.usecase.student_dynamic import StudentDynamicTakeDiffSnapshotUseCase
from feature.workspace.usecase.student_run_build import StudentRunBuildStageUseCase
from feature.workspace.usecase.student_run_compile import StudentRunCompileStageUseCase
from feature.workspace.usecase.student_run_execute import StudentRunExecuteStageUseCase
from feature.workspace.usecase.student_run_next_stage import StudentRunNextStageUseCase
from feature.workspace.usecase.student_run_test import StudentRunTestStageUseCase
from feature.workspace.usecase.student_stage_result import StudentStageResultClearUseCase
from feature.workspace.usecase.student_submission_folder_show import \
    StudentSubmissionFolderShowUseCase
from feature.workspace.usecase.student_table_cell_data import \
    StudentTableGetStudentIDCellDataUseCase, \
    StudentTableGetStudentNameCellDataUseCase, StudentTableGetStudentStageStateCellDataUseCase, \
    StudentTableGetStudentErrorCellDataUseCase


def get_setting_get_usecase():
    return SettingGetUseCase(
        setting_repo=get_setting_repository(),
    )


def get_setting_put_usecase():
    return SettingPutUseCase(
        setting_repo=get_setting_repository(),
    )


# GetAboutInfoUseCase
def get_about_info_usecase():
    return GetAboutInfoUseCase(
        name_provider=get_app_name_provider(),
        version_provider=get_app_version_provider(),
    )


def get_project_list_recent_summary_usecase():
    return ProjectListRecentSummaryUseCase(
        project_list_gateway=get_project_list_gateway(),
        project_config_state_gateway=get_project_config_state_gateway(),
        project_repo=get_project_repository(),
    )


# ProjectBaseFolderShowUseCase
def get_project_base_folder_show_usecase():
    return ProjectBaseFolderShowUseCase(
        project_file_system_gateway=get_project_file_system_gateway(),
    )


# ProjectFolderShowUseCase
def get_project_folder_show_usecase():
    return ProjectFolderShowUseCase(
        project_file_system_gateway=get_project_file_system_gateway(),
    )


def get_project_create_usecase():
    return ProjectCreateUseCase(
        project_repo=get_project_repository(),
        app_version_provider=get_app_version_provider(),
    )


# ProjectDeleteUseCase
def get_project_delete_usecase():
    return ProjectDeleteUseCase(
        project_repo=get_project_repository(),
    )


# ProjectGetSizeQueryUseCase
def get_project_get_size_query_usecase():
    return ProjectGetSizeQueryUseCase(
        project_file_system_gateway=get_project_file_system_gateway(),
    )


def get_current_project_initialize_static_usecase(manaba_report_archive_fullpath: Path):
    return CurrentProjectInitializeStaticUseCase(
        student_master_create_usecase=StudentMasterCreateUseCase(
            student_repo=get_student_repository(),
            manaba_report_archive_io=get_manaba_report_archive_io(
                manaba_report_archive_fullpath=manaba_report_archive_fullpath,
            ),
        ),
        student_submission_extract_usecase=StudentSubmissionExtractUseCase(
            student_repo=get_student_repository(),
            manaba_report_archive_io=get_manaba_report_archive_io(
                manaba_report_archive_fullpath=manaba_report_archive_fullpath,
            ),
            current_project_core_io=get_current_project_core_io(),
            student_submission_folder_fullpath=get_path_config().student_submission_folder_fullpath,
            current_project_id=get_current_project_id_state().get(),
        ),
        current_project_repo=get_current_project_repository(),
    )


# ProjectUpdateLastOpenedUseCase
def get_project_update_last_opened_usecase():
    return ProjectUpdateLastOpenUseCase(
        project_repo=get_project_repository(),
    )


def get_project_check_exist_by_name_usecase():
    return ProjectCheckExistByNameUseCase(
        project_list_gateway=get_project_list_gateway(),
    )


def get_current_project_summary_get_usecase():
    return CurrentProjectSummaryGetUseCase(
        current_project_repo=get_current_project_repository(),
    )


def get_student_list_id_usecase():
    return StudentListIDUseCase(
        student_repo=get_student_repository(),
    )


def get_student_submission_folder_show_usecase():
    return StudentSubmissionFolderShowUseCase(
        student_submission_folder_show_gateway=get_student_submission_folder_show_gateway(),
    )


def get_student_table_get_student_id_cell_data_usecase():
    return StudentTableGetStudentIDCellDataUseCase(
        student_repo=get_student_repository(),
    )


def get_student_table_get_student_name_cell_data_usecase():
    return StudentTableGetStudentNameCellDataUseCase(
        student_repo=get_student_repository(),
    )


def get_student_table_get_student_stage_state_cell_data_usecase():
    return StudentTableGetStudentStageStateCellDataUseCase(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_get_stage_path_result_map_service=get_student_get_stage_path_result_map_service(),
    )


def get_student_table_get_student_error_cell_data_usecase():
    return StudentTableGetStudentErrorCellDataUseCase(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_get_stage_path_result_map_service=get_student_get_stage_path_result_map_service(),
        student_stage_path_result_analyzer_service=get_student_stage_path_result_analyzer_service(),
    )


def get_compiler_search_usecase():
    from app.di.gateway import get_find_compiler_path_gateway
    return CompilerSearchUseCase(
        find_compiler_path_gateway=get_find_compiler_path_gateway(),
    )


def get_test_compile_stage_usecase():
    return TestCompileStageUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_test_source_service=get_storage_load_test_source_service(),
        storage_run_compiler_service=get_storage_run_compiler_service(),
        storage_delete_service=get_storage_delete_service(),
    )


def get_test_test_stage_usecase():
    return TestTestStageUseCase(
        match_get_best_service=get_match_get_best_service(),
    )


def get_student_run_build_stage_usecase():
    from app.di.gateway import get_current_datetime_gateway
    return StudentRunBuildStageUseCase(
        student_submission_get_source_content_gateway=get_student_submission_get_source_content_gateway(),
        student_dynamic_clear_service=get_student_dynamic_clear_service(),
        student_dynamic_set_source_content_service=get_student_dynamic_set_source_content_service(),
        student_submission_get_checksum_gateway=get_student_submission_get_checksum_gateway(),
        student_put_stage_result_service=get_student_put_stage_path_result_entity_service(),
        current_datetime_gateway=get_current_datetime_gateway(),
    )


# StudentRunCompileStageUseCase
def get_student_run_compile_stage_usecase():
    from app.di.gateway import get_current_datetime_gateway
    return StudentRunCompileStageUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_student_source_service=get_storage_load_student_source_service(),
        storage_store_student_executable_service=get_storage_store_student_executable_service(),
        storage_run_compiler_service=get_storage_run_compiler_service(),
        storage_delete_service=get_storage_delete_service(),
        student_put_stage_result_service=get_student_put_stage_path_result_entity_service(),
        current_datetime_gateway=get_current_datetime_gateway(),
    )


# StudentRunExecuteStageUseCase
def get_student_run_execute_stage_usecase():
    from app.di.gateway import get_current_datetime_gateway
    return StudentRunExecuteStageUseCase(
        storage_create_service=get_storage_create_service(),
        storage_load_student_executable_service=get_storage_load_student_executable_service(),
        storage_load_execute_config_input_files_service=get_storage_load_execute_config_input_files_service(),
        storage_take_snapshot_service=get_storage_take_snapshot_service(),
        storage_delete_service=get_storage_delete_service(),
        testcase_config_repo=get_testcase_config_repository(),
        storage_run_executable_service=get_storage_run_executable_service(),
        storage_create_output_file_mapping_from_diff_service=get_storage_create_output_file_mapping_from_diff_service(),
        storage_write_stdout_file_service=get_storage_write_stdout_file_service(),
        student_put_stage_result_service=get_student_put_stage_path_result_entity_service(),
        current_datetime_gateway=get_current_datetime_gateway(),
    )


# StudentRunTestUseCase
def get_student_run_test_stage_usecase():
    from app.di.gateway import get_current_datetime_gateway
    return StudentRunTestStageUseCase(
        testcase_config_repo=get_testcase_config_repository(),
        match_get_best_service=get_match_get_best_service(),
        student_put_stage_result_service=get_student_put_stage_path_result_entity_service(),
        student_get_stage_result_map_service=get_student_get_stage_path_result_map_service(),
        current_datetime_gateway=get_current_datetime_gateway(),
    )


def get_student_run_next_stage_usecase():
    return StudentRunNextStageUseCase(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_get_stage_path_result_map_service=get_student_get_stage_path_result_map_service(),
        student_stage_result_rollback_service=get_student_stage_path_result_entity_rollback_service(),
        student_run_build_stage_usecase=get_student_run_build_stage_usecase(),
        student_run_compile_stage_usecase=get_student_run_compile_stage_usecase(),
        student_run_execute_stage_usecase=get_student_run_execute_stage_usecase(),
        student_run_test_stage_usecase=get_student_run_test_stage_usecase(),
        student_stage_path_result_check_rollback_service=get_student_stage_path_result_check_rollback_service(),
        student_stage_path_result_analyzer_service=get_student_stage_path_result_analyzer_service(),
        event_bus=get_event_bus(),
    )


# TestCaseListSummaryUseCase
def get_testcase_list_summary_usecase():
    return TestCaseListSummaryUseCase(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseCreateNewNameUseCase
def get_testcase_create_new_name_usecase():
    return TestCaseCreateNewNameUseCase(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseCreateUseCase
def get_testcase_create_usecase():
    from app.di.gateway import get_current_datetime_gateway
    return TestCaseCreateUseCase(
        testcase_config_repo=get_testcase_config_repository(),
        current_datetime_gateway=get_current_datetime_gateway(),
    )


# TestCaseCopyUseCase
def get_testcase_copy_usecase():
    return TestCaseCopyUseCase(
        testcase_config_copy_service=get_testcase_config_copy_service(),
    )


# StudentStageResultTakeDiffSnapshotUseCase
def get_student_dynamic_take_diff_snapshot_usecase():
    return StudentDynamicTakeDiffSnapshotUseCase(
        student_stage_result_check_timestamp_query_service=get_student_stage_path_result_entity_check_timestamp_query_service(),
        student_mark_repo=get_student_mark_repository(),
    )


# StudentStageResultClearUseCase
def get_student_stage_result_clear_usecase():
    return StudentStageResultClearUseCase(
        student_stage_result_clear_service=get_student_stage_path_result_entity_clear_service(),
        event_bus=get_event_bus(),
    )


# TestCaseConfigGetUseCase
def get_testcase_config_get_usecase():
    return TestCaseConfigGetUseCase(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseConfigPutUseCase
def get_testcase_config_put_usecase():
    return TestCaseConfigPutUseCase(
        testcase_config_repo=get_testcase_config_repository(),
    )


def get_testcase_config_list_id_usecase():
    return TestCaseConfigListIDUseCase(
        testcase_config_repo=get_testcase_config_repository(),
    )


# StudentMarkViewDataGetTestResultUseCase
def get_student_mark_view_data_get_test_result_usecase():
    return StudentMarkViewDataGetTestResultUseCase(
        stage_path_get_by_testcase_id_service=get_stage_path_get_by_testcase_id_service(),
        student_get_stage_path_result_map_service=get_student_get_stage_path_result_map_service(),
        student_stage_path_result_analyzer_service=get_student_stage_path_result_analyzer_service(),
    )
    
# StudentMarkViewDataGetMarkSummaryUseCase
def get_student_mark_view_data_get_mark_summary_usecase():
    return StudentMarkViewDataGetMarkSummaryUseCase(
        student_repo=get_student_repository(),
        student_mark_get_sub_service=get_student_mark_get_sub_service(),
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_get_stage_path_result_map_service=get_student_get_stage_path_result_map_service(),
        student_stage_path_result_check_rollback_service=get_student_stage_path_result_check_rollback_service(),
    )


# StudentSourceCodeGetUseCase
def get_student_source_code_get_usecase():
    return StudentSourceCodeGetUseCase(
        student_source_repo=get_student_source_repository(),
    )


# StudentMarkGetUseCase
def get_student_mark_get_usecase():
    return StudentMarkGetUseCase(
        student_mark_get_sub_service=get_student_mark_get_sub_service(),
    )


# StudentMarkPutUseCase
def get_student_mark_put_usecase():
    return StudentMarkPutUseCase(
        student_mark_repo=get_student_mark_repository(),
        event_bus=get_event_bus(),
    )


# StudentScoreListUseCase
def get_student_score_list_usecase():
    return StudentScoreListUseCase(
        student_mark_list_service=get_student_mark_list_service(),
    )


# GetSimpleScoreExportDataUseCase
def get_simple_score_export_data_usecase():
    from app.di.repository import get_student_repository
    from app.di.service import get_student_mark_get_sub_service
    return GetSimpleScoreExportDataUseCase(
        student_repo=get_student_repository(),
        student_mark_get_sub_service=get_student_mark_get_sub_service(),
    )


# ExecuteSimpleScoreExportUseCase
def get_execute_simple_score_export_usecase():
    from app.di.gateway import get_json_score_export_gateway, get_csv_score_export_gateway
    return ExecuteSimpleScoreExportUseCase(
        json_export_gateway=get_json_score_export_gateway(),
        csv_export_gateway=get_csv_score_export_gateway(),
    )


# ListExcelWorksheetUseCase
def get_list_excel_worksheet_usecase():
    from app.di.gateway import get_excel_gateway
    return ListExcelWorksheetUseCase(
        excel_gateway=get_excel_gateway(),
    )


# GetExcelSheetPreviewUseCase
def get_excel_sheet_preview_usecase():
    from app.di.gateway import get_excel_gateway
    return GetExcelSheetPreviewUseCase(
        excel_gateway=get_excel_gateway(),
    )


# AutoDetectExcelLayoutUseCase
def get_auto_detect_excel_layout_usecase():
    from feature.export.domain.service.excel_layout_detection import ExcelLayoutDetectionService
    return AutoDetectExcelLayoutUseCase(
        excel_layout_detection_service=ExcelLayoutDetectionService(),
    )


# ExecuteExcelScoreUpdateUseCase
def get_execute_excel_score_update_usecase():
    from app.di.gateway import get_excel_gateway, get_excel_backup_gateway
    from app.di.repository import get_student_repository
    from app.di.service import (
        get_student_mark_get_sub_service,
        get_excel_score_update_planning_service,
    )
    return ExecuteExcelScoreUpdateUseCase(
        excel_gateway=get_excel_gateway(),
        excel_backup_gateway=get_excel_backup_gateway(),
        student_repo=get_student_repository(),
        student_mark_get_sub_service=get_student_mark_get_sub_service(),
        export_setting_get_usecase=get_export_setting_get_usecase(),
        excel_score_update_planning_service=get_excel_score_update_planning_service(),
    )


# ExportSettingGetUseCase
def get_export_setting_get_usecase():
    from app.di.repository import get_setting_repository
    return ExportSettingGetUseCase(
        setting_repo=get_setting_repository(),
    )


# ResourceUsageGetUseCase
def get_resource_usage_get_usecase():
    return ResourceUsageGetUseCase(
        resource_usage_gateway=get_resource_usage_gateway(),
    )
