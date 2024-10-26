from application.dependency.external_io import *
from application.dependency.repositories import *
from services.current_project_get import CurrentProjectGetService
from services.global_config import GlobalConfigGetService, GlobalConfigPutService
from services.output_files import OutputFilesCreateFromStorageDiffService
from services.project_create import ProjectCreateService
from services.project_list import ProjectListService
from services.stage import StageListRootSubService, StageListChildSubService, \
    StageGetParentSubService
from services.stage_path import StagePathListService
from services.storage import StorageLoadTestSourceService, \
    StorageCreateService, StorageDeleteService, StorageLoadStudentSourceService, \
    StorageLoadStudentExecutableService, StorageStoreStudentExecutableService, \
    StorageLoadExecuteConfigInputFilesService, StorageWriteStdoutFileService
from services.storage_diff_snapshot import StorageTakeSnapshotService
from services.storage_run_compiler import StorageRunCompilerService
from services.storage_run_executable import StorageRunExecutableService
from services.student_dynamic import StudentDynamicClearService, \
    StudentDynamicSetSourceContentService
from services.student_get import StudentGetService
from services.student_list import StudentListService
from services.student_master_create import StudentMasterCreateService
from services.student_stage_path_result import StudentProgressCheckTimestampQueryService, \
    StudentStagePathResultGetService
from services.student_stage_rollback import StudentStageRollbackService
from services.student_submission import StudentSubmissionExistService, \
    StudentSubmissionExtractService, StudentSubmissionFolderShowService, \
    StudentSubmissionGetChecksumService, StudentSubmissionListSourceRelativePathQueryService, \
    StudentSubmissionGetFileContentQueryService, StudentSubmissionGetSourceContentService
from services.testcase_config import TestCaseConfigListIDSubService, \
    TestCaseConfigGetExecuteConfigMtimeService, TestCaseConfigGetTestConfigMtimeService, \
    TestCaseConfigDeleteService, TestCaseConfigGetExecuteOptionsService, \
    TestCaseConfigGetTestOptionsService


def get_global_config_get_service():
    return GlobalConfigGetService(
        global_config_repo=get_global_config_repository(),
    )


def get_global_config_put_service():
    return GlobalConfigPutService(
        global_config_repo=get_global_config_repository(),
    )


def get_project_list_service():
    return ProjectListService(
        project_repo=get_project_repository(),
    )


def get_project_create_service():
    return ProjectCreateService(
        project_repo=get_project_repository(),
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


def get_student_list_service():
    return StudentListService(
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


def get_stage_list_root_sub_service():
    return StageListRootSubService()


def get_stage_list_child_sub_service():
    return StageListChildSubService(
        testcase_config_list_id_sub_service=get_testcase_config_list_id_sub_service(),
    )


def get_stage_get_parent_sub_service():
    return StageGetParentSubService()


def get_stage_path_list_service():
    return StagePathListService(
        stage_list_root_sub_service=get_stage_list_root_sub_service(),
        stage_list_child_sub_service=get_stage_list_child_sub_service(),
    )


def get_student_stage_path_result_get_service():
    return StudentStagePathResultGetService(
        student_stage_result_repo=get_student_stage_result_repository(),
    )


def get_student_progress_check_timestamp_query_service():
    return StudentProgressCheckTimestampQueryService(
        student_stage_result_path_provider=get_student_stage_result_path_provider(),
        testcase_config_repo=get_testcase_config_repository(),
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
        global_config_repo=get_global_config_repository(),
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


def get_student_stage_rollback_service():
    return StudentStageRollbackService(
        student_stage_result_repo=get_student_stage_result_repository(),
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
def get_output_files_create_from_storage_diff_service():
    return OutputFilesCreateFromStorageDiffService(
        storage_repo=get_storage_repository(),
    )
