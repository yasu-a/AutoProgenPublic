from application.dependency.external_io import *
from application.dependency.repository import *
from application.state.current_project import require_current_project_id
from domain.model.value import ProjectID
from service.current_project import CurrentProjectGetService, CurrentProjectSetInitializedService
from service.match import MatchGetBestService
from service.project import ProjectGetSizeQueryService, ProjectUpdateTimestampService, \
    ProjectGetConfigStateQueryService, ProjectListIDQueryService
from service.stage_path import StagePathListSubService, StagePathGetByTestCaseIDService
from service.storage import StorageLoadTestSourceService, \
    StorageCreateService, StorageDeleteService, StorageLoadStudentSourceService, \
    StorageLoadStudentExecutableService, StorageStoreStudentExecutableService, \
    StorageLoadExecuteConfigInputFilesService, StorageWriteStdoutFileService, \
    StorageCreateOutputFileCollectionFromDiffService, StorageTakeSnapshotService
from service.storage_run_compiler import StorageRunCompilerService
from service.storage_run_executable import StorageRunExecutableService
from service.student import StudentGetService, StudentListSubService
from service.student_dynamic import StudentDynamicClearService, \
    StudentDynamicSetSourceContentService, StudentDynamicGetSourceContentService
from service.student_mark import StudentMarkGetSubService, StudentMarkPutService, \
    StudentMarkCheckTimestampQueryService, StudentMarkListService
from service.student_master_create import StudentMasterCreateService
from service.student_stage_path_result import StudentStagePathResultGetService, \
    StudentStagePathResultCheckRollbackService, StudentStageResultCheckTimestampQueryService, \
    StudentStageResultClearService, StudentPutStageResultService, \
    StudentGetStageResultService
from service.student_submission import StudentSubmissionExistService, \
    StudentSubmissionExtractService, \
    StudentSubmissionGetChecksumService, StudentSubmissionListSourceRelativePathQueryService, \
    StudentSubmissionGetFileContentQueryService, StudentSubmissionGetSourceContentService
from service.testcase_config import TestCaseConfigListIDSubService, \
    TestCaseConfigGetExecuteConfigMtimeService, TestCaseConfigGetTestConfigMtimeService, \
    TestCaseConfigCopyService


# ProjectGetConfigStateQueryService
def get_project_get_config_state_query_service():
    return ProjectGetConfigStateQueryService(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
        app_version_repo=get_app_version_repository(),
    )


# ProjectListIDQueryService
def get_project_list_id_query_service():
    return ProjectListIDQueryService(
        project_list_path_provider=get_project_list_path_provider(),
    )


# ProjectUpdateTimestampService
def get_project_update_timestamp_service():
    return ProjectUpdateTimestampService(
        project_repo=get_project_repository(),
    )


# ProjectGetSizeQueryService
def get_project_get_size_query_service():
    return ProjectGetSizeQueryService(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
    )


def get_student_master_create_service(manaba_report_archive_fullpath: Path):
    return create_student_master_create_service(
        project_id=require_current_project_id(),
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


def create_student_master_create_service(project_id: ProjectID, manaba_report_archive_fullpath: Path):
    return StudentMasterCreateService(
        student_repo=create_student_repository(project_id),
        manaba_report_archive_io=get_manaba_report_archive_io(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
    )


def get_student_submission_extract_service(manaba_report_archive_fullpath: Path):
    return create_student_submission_extract_service(
        project_id=require_current_project_id(),
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


def create_student_submission_extract_service(project_id: ProjectID, manaba_report_archive_fullpath: Path):
    return StudentSubmissionExtractService(
        student_repo=create_student_repository(project_id),
        manaba_report_archive_io=get_manaba_report_archive_io(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ),
        current_project_core_io=create_current_project_core_io(project_id),
        student_submission_path_provider=create_student_submission_path_provider(project_id),
    )


def get_current_project_get_service():
    return create_current_project_get_service(require_current_project_id())


def create_current_project_get_service(project_id: ProjectID):
    return CurrentProjectGetService(
        current_project_repo=create_current_project_repository(project_id),
    )


def get_current_project_set_initialized_service():
    return create_current_project_set_initialized_service(require_current_project_id())


def create_current_project_set_initialized_service(project_id: ProjectID):
    return CurrentProjectSetInitializedService(
        current_project_repo=create_current_project_repository(project_id),
    )


def get_student_list_sub_service():
    return create_student_list_sub_service(require_current_project_id())


def create_student_list_sub_service(project_id: ProjectID):
    return StudentListSubService(
        student_repo=create_student_repository(project_id),
    )


def get_student_submission_exist_service():
    return create_student_submission_exist_service(require_current_project_id())


def create_student_submission_exist_service(project_id: ProjectID):
    return StudentSubmissionExistService(
        student_repo=create_student_repository(project_id),
    )


def get_student_get_service():
    return create_student_get_service(require_current_project_id())


def create_student_get_service(project_id: ProjectID):
    return StudentGetService(
        student_repo=create_student_repository(project_id),
    )


def get_testcase_config_list_id_sub_service():
    return create_testcase_config_list_id_sub_service(require_current_project_id())


def create_testcase_config_list_id_sub_service(project_id: ProjectID):
    return TestCaseConfigListIDSubService(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


def get_stage_path_list_sub_service():
    return create_stage_path_list_sub_service(require_current_project_id())


def create_stage_path_list_sub_service(project_id: ProjectID):
    return StagePathListSubService(
        testcase_config_list_id_sub_service=create_testcase_config_list_id_sub_service(project_id),
    )


# StagePathGetByTestCaseIDService
def get_stage_path_get_by_testcase_id_service():
    return create_stage_path_get_by_testcase_id_service(require_current_project_id())


def create_stage_path_get_by_testcase_id_service(project_id: ProjectID):
    return StagePathGetByTestCaseIDService(
        stage_path_list_sub_service=create_stage_path_list_sub_service(project_id),
    )


# StudentStagePathResultGetService
def get_student_stage_path_result_get_service():
    return create_student_stage_path_result_get_service(require_current_project_id())


def create_student_stage_path_result_get_service(project_id: ProjectID):
    return StudentStagePathResultGetService(
        student_stage_path_result_repo=create_student_stage_path_result_repository(project_id),
    )


# StudentStagePathResultCheckRollbackService
def get_student_stage_path_result_check_rollback_service():
    return create_student_stage_path_result_check_rollback_service(require_current_project_id())


def create_student_stage_path_result_check_rollback_service(project_id: ProjectID):
    return StudentStagePathResultCheckRollbackService(
        student_submission_get_checksum_service=create_student_submission_get_checksum_service(project_id),
        testcase_config_get_execute_config_mtime_service=create_testcase_config_get_execute_config_mtime_service(project_id),
        testcase_config_get_test_config_mtime_service=create_testcase_config_get_test_config_mtime_service(project_id),
    )


def get_student_stage_result_check_timestamp_query_service():
    return create_student_stage_result_check_timestamp_query_service(require_current_project_id())


def create_student_stage_result_check_timestamp_query_service(project_id: ProjectID):
    return StudentStageResultCheckTimestampQueryService(
        student_stage_path_result_repo=create_student_stage_path_result_repository(project_id),
    )


def get_storage_create_service():
    return create_storage_create_service(require_current_project_id())


def create_storage_create_service(project_id: ProjectID):
    return StorageCreateService(
        storage_repo=create_storage_repository(project_id),
    )


def get_storage_delete_service():
    return create_storage_delete_service(require_current_project_id())


def create_storage_delete_service(project_id: ProjectID):
    return StorageDeleteService(
        storage_repo=create_storage_repository(project_id),
    )


def get_storage_load_test_source_service():
    return create_storage_load_test_source_service(require_current_project_id())


def create_storage_load_test_source_service(project_id: ProjectID):
    return StorageLoadTestSourceService(
        test_source_repo=get_test_source_repository(),
        storage_repo=create_storage_repository(project_id),
    )


def get_storage_run_compiler_service():
    return create_storage_run_compiler_service(require_current_project_id())


def create_storage_run_compiler_service(project_id: ProjectID):
    return StorageRunCompilerService(
        compile_tool_io=get_compile_tool_io(),
        global_settings_repo=get_global_settings_repository(),
        storage_repo=create_storage_repository(project_id),
    )


def get_storage_load_student_source_service():
    return create_storage_load_student_source_service(require_current_project_id())


def create_storage_load_student_source_service(project_id: ProjectID):
    return StorageLoadStudentSourceService(
        student_source_repo=create_student_source_repository(project_id),
        storage_repo=create_storage_repository(project_id),
    )


def get_storage_load_student_executable_service():
    return create_storage_load_student_executable_service(require_current_project_id())


def create_storage_load_student_executable_service(project_id: ProjectID):
    return StorageLoadStudentExecutableService(
        student_executable_repo=create_student_executable_repository(project_id),
        storage_repo=create_storage_repository(project_id),
    )


def get_storage_store_student_executable_service():
    return create_storage_store_student_executable_service(require_current_project_id())


def create_storage_store_student_executable_service(project_id: ProjectID):
    return StorageStoreStudentExecutableService(
        student_executable_repo=create_student_executable_repository(project_id),
        storage_repo=create_storage_repository(project_id),
    )


def get_storage_load_execute_config_input_files_service():
    return create_storage_load_execute_config_input_files_service(require_current_project_id())


def create_storage_load_execute_config_input_files_service(project_id: ProjectID):
    return StorageLoadExecuteConfigInputFilesService(
        storage_repo=create_storage_repository(project_id),
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


# StorageWriteStdoutFileService
def get_storage_write_stdout_file_service():
    return create_storage_write_stdout_file_service(require_current_project_id())


def create_storage_write_stdout_file_service(project_id: ProjectID):
    return StorageWriteStdoutFileService(
        storage_repo=create_storage_repository(project_id),
    )


def get_storage_take_snapshot_service():
    return create_storage_take_snapshot_service(require_current_project_id())


def create_storage_take_snapshot_service(project_id: ProjectID):
    return StorageTakeSnapshotService(
        storage_repo=create_storage_repository(project_id),
    )


def get_student_submission_get_checksum_service():
    return create_student_submission_get_checksum_service(require_current_project_id())


def create_student_submission_get_checksum_service(project_id: ProjectID):
    return StudentSubmissionGetChecksumService(
        student_submission_path_provider=create_student_submission_path_provider(project_id),
        current_project_core_io=create_current_project_core_io(project_id),
    )


def get_student_submission_list_source_relative_path_query_service():
    return create_student_submission_list_source_relative_path_query_service(require_current_project_id())


def create_student_submission_list_source_relative_path_query_service(project_id: ProjectID):
    return StudentSubmissionListSourceRelativePathQueryService(
        student_submission_path_provider=create_student_submission_path_provider(project_id),
        current_project_core_io=create_current_project_core_io(project_id),
        current_project_repo=create_current_project_repository(project_id),
    )


def get_student_submission_get_file_content_query_service():
    return create_student_submission_get_file_content_query_service(require_current_project_id())


def create_student_submission_get_file_content_query_service(project_id: ProjectID):
    return StudentSubmissionGetFileContentQueryService(
        student_submission_path_provider=create_student_submission_path_provider(project_id),
        current_project_core_io=create_current_project_core_io(project_id),
    )


def get_student_submission_get_source_content_service():
    return create_student_submission_get_source_content_service(require_current_project_id())


def create_student_submission_get_source_content_service(project_id: ProjectID):
    return StudentSubmissionGetSourceContentService(
        student_submission_list_source_relative_path_query_service=create_student_submission_list_source_relative_path_query_service(project_id),
        student_submission_get_file_content_query_service=create_student_submission_get_file_content_query_service(project_id),
        student_repo=create_student_repository(project_id),
    )


# StudentStageResultClearService
def get_student_stage_result_clear_service():
    return create_student_stage_result_clear_service(require_current_project_id())


def create_student_stage_result_clear_service(project_id: ProjectID):
    return StudentStageResultClearService(
        stage_path_list_sub_service=create_stage_path_list_sub_service(project_id),
        student_stage_path_result_repo=create_student_stage_path_result_repository(project_id),
    )


# StudentPutStageResultService
def get_student_put_stage_result_service():
    return create_student_put_stage_result_service(require_current_project_id())


def create_student_put_stage_result_service(project_id: ProjectID):
    return StudentPutStageResultService(
        student_stage_path_result_repo=create_student_stage_path_result_repository(project_id),

    )


# StudentGetStageResultService
def get_student_get_stage_result_service():
    return create_student_get_stage_result_service(require_current_project_id())


def create_student_get_stage_result_service(project_id: ProjectID):
    return StudentGetStageResultService(
        student_stage_path_result_repo=create_student_stage_path_result_repository(project_id),
    )


# TestCaseConfigCopyService
def get_testcase_config_copy_service():
    return create_testcase_config_copy_service(require_current_project_id())


def create_testcase_config_copy_service(project_id: ProjectID):
    return TestCaseConfigCopyService(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


# TestCaseConfigGetExecuteConfigMtimeService
def get_testcase_config_get_execute_config_mtime_service():
    return create_testcase_config_get_execute_config_mtime_service(require_current_project_id())


def create_testcase_config_get_execute_config_mtime_service(project_id: ProjectID):
    return TestCaseConfigGetExecuteConfigMtimeService(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


# TestCaseConfigGetTestConfigMtimeService
def get_testcase_config_get_test_config_mtime_service():
    return create_testcase_config_get_test_config_mtime_service(require_current_project_id())


def create_testcase_config_get_test_config_mtime_service(project_id: ProjectID):
    return TestCaseConfigGetTestConfigMtimeService(
        testcase_config_repo=create_testcase_config_repository(project_id),
    )


def get_student_dynamic_clear_service():
    return create_student_dynamic_clear_service(require_current_project_id())


def create_student_dynamic_clear_service(project_id: ProjectID):
    return StudentDynamicClearService(
        student_source_repo=create_student_source_repository(project_id),
        student_execute_repo=create_student_executable_repository(project_id),
    )


def get_student_dynamic_set_source_content_service():
    return create_student_dynamic_set_source_content_service(require_current_project_id())


def create_student_dynamic_set_source_content_service(project_id: ProjectID):
    return StudentDynamicSetSourceContentService(
        student_source_repo=create_student_source_repository(project_id),
    )


# StudentDynamicGetSourceContentService
def get_student_dynamic_get_source_content_service():
    return create_student_dynamic_get_source_content_service(require_current_project_id())


def create_student_dynamic_get_source_content_service(project_id: ProjectID):
    return StudentDynamicGetSourceContentService(
        student_source_repo=create_student_source_repository(project_id),
    )


# StorageRunExecutableService
def get_storage_run_executable_service():
    return create_storage_run_executable_service(require_current_project_id())


def create_storage_run_executable_service(project_id: ProjectID):
    return StorageRunExecutableService(
        storage_repo=create_storage_repository(project_id),
        executable_io=get_executable_io(),
    )


# OutputFilesCreateFromStorageDiffService
def get_storage_create_output_file_mapping_from_diff_service():
    return create_storage_create_output_file_mapping_from_diff_service(require_current_project_id())


def create_storage_create_output_file_mapping_from_diff_service(project_id: ProjectID):
    return StorageCreateOutputFileCollectionFromDiffService(
        storage_repo=create_storage_repository(project_id),
    )


# StudentMarkGetSubService
def get_student_mark_get_sub_service():
    return create_student_mark_get_sub_service(require_current_project_id())


def create_student_mark_get_sub_service(project_id: ProjectID):
    return StudentMarkGetSubService(
        student_mark_repo=create_student_mark_repository(project_id),
    )


# StudentMarkPutService
def get_student_mark_put_service():
    return create_student_mark_put_service(require_current_project_id())


def create_student_mark_put_service(project_id: ProjectID):
    return StudentMarkPutService(
        student_mark_repo=create_student_mark_repository(project_id),
    )


# StudentMarkCheckTimestampQueryService
def get_student_mark_check_timestamp_query_service():
    return create_student_mark_check_timestamp_query_service(require_current_project_id())


def create_student_mark_check_timestamp_query_service(project_id: ProjectID):
    return StudentMarkCheckTimestampQueryService(
        student_mark_repo=create_student_mark_repository(project_id),
    )


# StudentMarkListService
def get_student_mark_list_service():
    return create_student_mark_list_service(require_current_project_id())


def create_student_mark_list_service(project_id: ProjectID):
    return StudentMarkListService(
        student_list_sub_service=create_student_list_sub_service(project_id),
        student_mark_get_sub_service=create_student_mark_get_sub_service(project_id),
    )


def get_match_get_best_service():
    return MatchGetBestService()
