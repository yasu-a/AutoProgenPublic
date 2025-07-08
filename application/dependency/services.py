from application.dependency.external_io import *
from application.dependency.external_io import get_student_folder_show_in_explorer_io
from application.dependency.repositories import *
from services.app_version import AppVersionGetService
from services.current_project import CurrentProjectGetService, CurrentProjectSetInitializedService
from services.global_settings import GlobalSettingsGetService, GlobalSettingsPutService
from services.match import MatchGetBestService
from services.project import ProjectCreateService, ProjectBaseFolderShowService, \
    ProjectFolderShowService, ProjectDeleteService, ProjectGetSizeQueryService, \
    ProjectUpdateTimestampService, ProjectGetConfigStateQueryService, ProjectListIDQueryService, \
    ProjectGetService
from services.stage_path import StagePathListSubService, StagePathGetByTestCaseIDService
from services.storage import StorageLoadTestSourceService, \
    StorageCreateService, StorageDeleteService, StorageLoadStudentSourceService, \
    StorageLoadStudentExecutableService, StorageStoreStudentExecutableService, \
    StorageLoadExecuteConfigInputFilesService, StorageWriteStdoutFileService, \
    StorageCreateOutputFileMappingFromDiffService, StorageTakeSnapshotService
from services.storage_run_compiler import StorageRunCompilerService
from services.storage_run_executable import StorageRunExecutableService
from services.student import StudentGetService, StudentListSubService
from services.student_dynamic import StudentDynamicClearService, \
    StudentDynamicSetSourceContentService
from services.student_mark import StudentMarkGetSubService, StudentMarkPutService, \
    StudentMarkCheckTimestampQueryService, StudentMarkListService
from services.student_master_create import StudentMasterCreateService
from services.student_source_code import StudentSourceCodeGetQueryService
from services.student_stage_path_result import StudentStagePathResultGetService, \
    StudentStagePathResultCheckRollbackService
from services.student_stage_result import StudentStageResultCheckTimestampQueryService, \
    StudentStageResultRollbackService, StudentStageResultClearService
from services.student_submission import StudentSubmissionExistService, \
    StudentSubmissionExtractService, StudentSubmissionFolderShowService, \
    StudentSubmissionGetChecksumService, StudentSubmissionListSourceRelativePathQueryService, \
    StudentSubmissionGetFileContentQueryService, StudentSubmissionGetSourceContentService
from services.testcase_config import TestCaseConfigListIDSubService, \
    TestCaseConfigGetExecuteConfigMtimeService, TestCaseConfigGetTestConfigMtimeService, \
    TestCaseConfigDeleteService, TestCaseConfigGetExecuteOptionsService, \
    TestCaseConfigGetTestOptionsService, TestCaseConfigGetService, TestCaseConfigPutService, \
    TestCaseConfigCopyService


def get_global_settings_get_service():
    return GlobalSettingsGetService(
        global_settings_repo=get_global_settings_repository(),
    )


def get_global_settings_put_service():
    return GlobalSettingsPutService(
        global_settings_repo=get_global_settings_repository(),
    )


# AppVersionGetService
def get_app_version_get_service():
    return AppVersionGetService(
        app_version_repo=get_app_version_repository(),
    )


# ProjectGetConfigStateQueryService
def get_project_get_config_state_query_service():
    return ProjectGetConfigStateQueryService(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
        app_version_get_service=get_app_version_get_service(),
    )


# ProjectListIDQueryService
def get_project_list_id_query_service():
    return ProjectListIDQueryService(
        project_list_path_provider=get_project_list_path_provider(),
    )


def get_project_get_service():
    return ProjectGetService(
        project_repo=get_project_repository(),
    )


def get_project_create_service():
    return ProjectCreateService(
        project_repo=get_project_repository(),
        app_version_get_service=get_app_version_get_service(),
    )


# ProjectUpdateTimestampService
def get_project_update_timestamp_service():
    return ProjectUpdateTimestampService(
        project_repo=get_project_repository(),
    )


# ProjectDeleteService
def get_project_delete_service():
    return ProjectDeleteService(
        project_repo=get_project_repository(),
    )


# ProjectGetSizeQueryService
def get_project_get_size_query_service():
    return ProjectGetSizeQueryService(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
    )


# ProjectBaseFolderShowService
def get_project_base_folder_show_service():
    return ProjectBaseFolderShowService(
        project_folder_show_in_explorer_io=get_project_folder_show_in_explorer_io(),
    )


# ProjectFolderShowService
def get_project_folder_show_service():
    return ProjectFolderShowService(
        project_folder_show_in_explorer_io=get_project_folder_show_in_explorer_io(),
    )


def get_student_master_create_service(manaba_report_archive_fullpath: Path):
    return StudentMasterCreateService(
        student_repo=get_student_repository(),
        manaba_report_archive_io=get_manaba_report_archive_io(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
    )


def get_student_submission_extract_service(manaba_report_archive_fullpath: Path):
    return StudentSubmissionExtractService(
        student_repo=get_student_repository(),
        manaba_report_archive_io=get_manaba_report_archive_io(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        current_project_core_io=get_current_project_core_io(),
        student_submission_path_provider=get_student_submission_path_provider(),
    )


def get_current_project_get_service():
    return CurrentProjectGetService(
        current_project_repo=get_current_project_repository(),
    )


def get_current_project_set_initialized_service():
    return CurrentProjectSetInitializedService(
        current_project_repo=get_current_project_repository(),
    )


def get_student_list_sub_service():
    return StudentListSubService(
        student_repo=get_student_repository(),
    )


def get_student_submission_folder_show_service():
    return StudentSubmissionFolderShowService(
        student_folder_show_in_explorer_io=get_student_folder_show_in_explorer_io(),
    )


def get_student_submission_exist_service():
    return StudentSubmissionExistService(
        student_repo=get_student_repository(),
    )


def get_student_get_service():
    return StudentGetService(
        student_repo=get_student_repository(),
    )


def get_testcase_config_list_id_sub_service():
    return TestCaseConfigListIDSubService(
        testcase_config_repo=get_testcase_config_repository(),
    )


def get_stage_path_list_sub_service():
    return StagePathListSubService(
        testcase_config_list_id_sub_service=get_testcase_config_list_id_sub_service(),
    )


# StagePathGetByTestCaseIDService
def get_stage_path_get_by_testcase_id_service():
    return StagePathGetByTestCaseIDService(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
    )


# StudentStagePathResultGetService
def get_student_stage_path_result_get_service():
    return StudentStagePathResultGetService(
        student_stage_result_repo=get_student_stage_result_repository(),
    )


# StudentStagePathResultCheckRollbackService
def get_student_stage_path_result_check_rollback_service():
    return StudentStagePathResultCheckRollbackService(
        student_submission_get_checksum_service=get_student_submission_get_checksum_service(),
        testcase_config_get_execute_config_mtime_service=get_testcase_config_get_execute_config_mtime_service(),
        testcase_config_get_test_config_mtime_service=get_testcase_config_get_test_config_mtime_service(),
    )


def get_student_stage_result_check_timestamp_query_service():
    return StudentStageResultCheckTimestampQueryService(
        student_stage_result_path_provider=get_student_stage_result_path_provider(),
        testcase_config_repo=get_testcase_config_repository(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_storage_create_service():
    return StorageCreateService(
        storage_repo=get_storage_repository(),
    )


def get_storage_delete_service():
    return StorageDeleteService(
        storage_repo=get_storage_repository(),
    )


def get_storage_load_test_source_service():
    return StorageLoadTestSourceService(
        test_source_repo=get_test_source_repository(),
        storage_repo=get_storage_repository(),
    )


def get_storage_run_compiler_service():
    return StorageRunCompilerService(
        compile_tool_io=get_compile_tool_io(),
        global_settings_repo=get_global_settings_repository(),
        student_dynamic_repo=get_student_dynamic_repository(),
        storage_repo=get_storage_repository(),
    )


def get_storage_load_student_source_service():
    return StorageLoadStudentSourceService(
        student_dynamic_repository=get_student_dynamic_repository(),
        storage_repo=get_storage_repository(),
    )


def get_storage_load_student_executable_service():
    return StorageLoadStudentExecutableService(
        student_dynamic_repository=get_student_dynamic_repository(),
        storage_repo=get_storage_repository(),
    )


def get_storage_store_student_executable_service():
    return StorageStoreStudentExecutableService(
        student_dynamic_repository=get_student_dynamic_repository(),
        storage_repo=get_storage_repository(),
    )


def get_storage_load_execute_config_input_files_service():
    return StorageLoadExecuteConfigInputFilesService(
        storage_repo=get_storage_repository(),
        testcase_config_repo=get_testcase_config_repository(),
    )


# StorageWriteStdoutFileService
def get_storage_write_stdout_file_service():
    return StorageWriteStdoutFileService(
        storage_repo=get_storage_repository(),
    )


def get_storage_take_snapshot_service():
    return StorageTakeSnapshotService(
        storage_repo=get_storage_repository(),
    )


def get_student_submission_get_checksum_service():
    return StudentSubmissionGetChecksumService(
        student_submission_path_provider=get_student_submission_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_student_submission_list_source_relative_path_query_service():
    return StudentSubmissionListSourceRelativePathQueryService(
        student_submission_path_provider=get_student_submission_path_provider(),
        current_project_core_io=get_current_project_core_io(),
        current_project_repo=get_current_project_repository(),
    )


def get_student_submission_get_file_content_query_service():
    return StudentSubmissionGetFileContentQueryService(
        student_submission_path_provider=get_student_submission_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


def get_student_submission_get_source_content_service():
    return StudentSubmissionGetSourceContentService(
        student_submission_list_source_relative_path_query_service=get_student_submission_list_source_relative_path_query_service(),
        student_submission_get_file_content_query_service=get_student_submission_get_file_content_query_service(),
        student_repo=get_student_repository(),
    )


def get_student_stage_result_rollback_service():
    return StudentStageResultRollbackService(
        student_stage_result_repo=get_student_stage_result_repository(),
    )


# StudentStageResultClearService
def get_student_stage_result_clear_service():
    return StudentStageResultClearService(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_stage_result_repo=get_student_stage_result_repository(),
    )


# TestCaseConfigGetService
def get_testcase_config_get_service():
    return TestCaseConfigGetService(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseConfigPutService
def get_testcase_config_put_service():
    return TestCaseConfigPutService(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseConfigCopyService
def get_testcase_config_copy_service():
    return TestCaseConfigCopyService(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseConfigGetExecuteOptionsService
def get_testcase_config_get_execute_options_service():
    return TestCaseConfigGetExecuteOptionsService(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseConfigGetTestOptionsService
def get_testcase_config_get_test_options_service():
    return TestCaseConfigGetTestOptionsService(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseConfigGetExecuteConfigMtimeService
def get_testcase_config_get_execute_config_mtime_service():
    return TestCaseConfigGetExecuteConfigMtimeService(
        testcase_config_repo=get_testcase_config_repository(),
    )


# TestCaseConfigGetTestConfigMtimeService
def get_testcase_config_get_test_config_mtime_service():
    return TestCaseConfigGetTestConfigMtimeService(
        testcase_config_repo=get_testcase_config_repository(),
    )


def get_testcase_config_delete_service():
    return TestCaseConfigDeleteService(
        testcase_config_repo=get_testcase_config_repository(),
    )


def get_student_dynamic_clear_service():
    return StudentDynamicClearService(
        student_dynamic_repo=get_student_dynamic_repository(),
    )


def get_student_dynamic_set_source_content_service():
    return StudentDynamicSetSourceContentService(
        student_dynamic_repo=get_student_dynamic_repository(),
    )


# StorageRunExecutableService
def get_storage_run_executable_service():
    return StorageRunExecutableService(
        storage_repo=get_storage_repository(),
        executable_io=get_executable_io(),
    )


# OutputFilesCreateFromStorageDiffService
def get_storage_create_output_file_mapping_from_diff_service():
    return StorageCreateOutputFileMappingFromDiffService(
        storage_repo=get_storage_repository(),
    )


# StudentMarkGetSubService
def get_student_mark_get_sub_service():
    return StudentMarkGetSubService(
        student_mark_repo=get_student_mark_repository(),
    )


# StudentMarkPutService
def get_student_mark_put_service():
    return StudentMarkPutService(
        student_mark_repo=get_student_mark_repository(),
    )


# StudentSourceCodeGetQueryService
def get_student_source_code_get_query_service():
    return StudentSourceCodeGetQueryService(
        student_dynamic_repo=get_student_dynamic_repository(),
    )


# StudentMarkCheckTimestampQueryService
def get_student_mark_check_timestamp_query_service():
    return StudentMarkCheckTimestampQueryService(
        student_mark_path_provider=get_student_mark_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )


# StudentMarkListService
def get_student_mark_list_service():
    return StudentMarkListService(
        student_list_sub_service=get_student_list_sub_service(),
        student_mark_get_sub_service=get_student_mark_get_sub_service(),
    )


def get_match_get_best_service():
    return MatchGetBestService()
