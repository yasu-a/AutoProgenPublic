from app.di.gateway import get_student_submission_get_checksum_gateway
from app.di.repository import *
from app.di.system import *
from shared.domain.service.match import MatchGetBestService
from shared.domain.service.stage_path import StagePathListSubService, \
    StagePathGetByTestCaseIDService
from shared.domain.service.storage import StorageLoadTestSourceService, \
    StorageCreateService, StorageDeleteService, StorageLoadStudentSourceService, \
    StorageLoadStudentExecutableService, StorageStoreStudentExecutableService, \
    StorageLoadExecuteConfigInputFilesService, StorageWriteStdoutFileService, \
    StorageCreateOutputFileCollectionFromDiffService, StorageTakeSnapshotService
from shared.domain.service.storage_run_compiler import StorageRunCompilerService
from shared.domain.service.storage_run_executable import StorageRunExecutableService
from shared.domain.service.student_dynamic import StudentDynamicClearService, \
    StudentDynamicSetSourceContentService
from shared.domain.service.student_mark_get import StudentMarkEntityGetSubService
from shared.domain.service.student_mark_list import StudentMarkEntityListService
from shared.domain.service.student_stage_path_result import \
    StudentStagePathResultEntityCheckRollbackService, \
    StudentStagePathResultEntityRollbackService, StudentStagePathResultEntityClearService, \
    StudentPutStagePathResultEntityService, \
    StudentGetStagePathResultEntityService, StudentStagePathResultEntityCheckTimestampQueryService


def get_stage_path_list_sub_service():
    return StagePathListSubService(
        testcase_config_repo=get_testcase_config_repository(),
    )


# StagePathGetByTestCaseIDService
def get_stage_path_get_by_testcase_id_service():
    return StagePathGetByTestCaseIDService(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
    )


# StudentStagePathResultEntityCheckRollbackService
def get_student_stage_path_result_check_rollback_service():
    return StudentStagePathResultEntityCheckRollbackService(
        student_submission_get_checksum_gateway=get_student_submission_get_checksum_gateway(),
        testcase_config_repo=get_testcase_config_repository(),
    )


def get_student_stage_path_result_entity_check_timestamp_query_service():
    return StudentStagePathResultEntityCheckTimestampQueryService(
        student_stage_path_result_repo=get_student_stage_path_result_repository(),
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
        setting_repo=get_setting_repository(),
        storage_repo=get_storage_repository(),
    )


def get_storage_load_student_source_service():
    return StorageLoadStudentSourceService(
        student_source_repo=get_student_source_repository(),
        storage_repo=get_storage_repository(),
    )


def get_storage_load_student_executable_service():
    return StorageLoadStudentExecutableService(
        student_executable_repo=get_student_executable_repository(),
        storage_repo=get_storage_repository(),
    )


def get_storage_store_student_executable_service():
    return StorageStoreStudentExecutableService(
        student_executable_repo=get_student_executable_repository(),
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


def get_student_stage_path_result_entity_rollback_service():
    return StudentStagePathResultEntityRollbackService(
        student_stage_path_result_repo=get_student_stage_path_result_repository(),
    )


# StudentStageResultClearService
def get_student_stage_path_result_entity_clear_service():
    return StudentStagePathResultEntityClearService(
        stage_path_list_sub_service=get_stage_path_list_sub_service(),
        student_stage_path_result_repo=get_student_stage_path_result_repository(),
    )


# StudentPutStagePathResultEntityService
def get_student_put_stage_path_result_entity_service():
    return StudentPutStagePathResultEntityService(
        student_stage_path_result_repo=get_student_stage_path_result_repository(),

    )


# StudentGetStagePathResultEntityService
def get_student_get_stage_path_result_entity_service():
    return StudentGetStagePathResultEntityService(
        student_stage_path_result_repo=get_student_stage_path_result_repository(),
    )


# TestCaseConfigCopyService
def get_testcase_config_copy_service():
    from shared.domain.service.testcase_config_copy import TestCaseConfigCopyService
    return TestCaseConfigCopyService(
        testcase_config_repo=get_testcase_config_repository(),
    )


def get_student_dynamic_clear_service():
    return StudentDynamicClearService(
        student_source_repo=get_student_source_repository(),
        student_execute_repo=get_student_executable_repository(),
    )


def get_student_dynamic_set_source_content_service():
    return StudentDynamicSetSourceContentService(
        student_source_repo=get_student_source_repository(),
    )


# StorageRunExecutableService
def get_storage_run_executable_service():
    return StorageRunExecutableService(
        storage_repo=get_storage_repository(),
        executable_io=get_executable_io(),
    )


# OutputFilesCreateFromStorageDiffService
def get_storage_create_output_file_mapping_from_diff_service():
    return StorageCreateOutputFileCollectionFromDiffService(
        storage_repo=get_storage_repository(),
    )


# StudentMarkEntityGetSubService
def get_student_mark_get_sub_service():
    return StudentMarkEntityGetSubService(
        student_mark_repo=get_student_mark_repository(),
    )


# StudentMarkEntityListService
def get_student_mark_list_service():
    return StudentMarkEntityListService(
        student_repo=get_student_repository(),
        student_mark_get_sub_service=get_student_mark_get_sub_service(),
    )


def get_match_get_best_service():
    return MatchGetBestService()


# ExcelScoreUpdatePlanningService
def get_excel_score_update_planning_service():
    from feature.export.domain.service.excel_score_update_planning import ExcelScoreUpdatePlanningService
    return ExcelScoreUpdatePlanningService()
