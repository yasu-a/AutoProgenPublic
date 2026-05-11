from functools import cached_property
from pathlib import Path

from domain.model.value import ProjectID
from infra.io.compile_tool import CompileToolIO
from infra.io.executable import ExecutableIO
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.io.files.project import ProjectCoreIO
from infra.io.project_database import ProjectDatabaseIO
from infra.io.report_archive import ManabaReportArchiveIO
from infra.io.student_folder_show_in_explorer import StudentFolderShowInExplorerIO
from infra.path_provider.current_project import TestCaseConfigPathProvider, DynamicPathProvider, DatabasePathProvider, \
    StoragePathProvider, ProjectStaticPathProvider, StudentSubmissionPathProvider
from infra.path_provider.project import ProjectPathProvider
from infra.repository.current_project import CurrentProjectRepository
from infra.repository.global_settings import GlobalSettingsRepository
from infra.repository.project import ProjectRepository
from infra.repository.storage import StorageRepository
from infra.repository.student import StudentRepository
from infra.repository.student_dynamic import StudentExecutableRepository, StudentSourceRepository
from infra.repository.student_mark import StudentMarkRepository
from infra.repository.student_stage_path_result import StudentStagePathResultRepository
from infra.repository.test_source import TestSourceRepository
from infra.repository.testcase_config import TestCaseConfigRepository
from infra.task.manager import TaskManager
from service.current_project import CurrentProjectGetService, CurrentProjectSetInitializedService
from service.match import MatchGetBestService
from service.stage_path import StagePathListSubService, StagePathGetByTestCaseIDService
from service.storage import StorageCreateService, StorageLoadStudentSourceService, StorageStoreStudentExecutableService, \
    StorageDeleteService, StorageLoadStudentExecutableService, StorageLoadExecuteConfigInputFilesService, \
    StorageTakeSnapshotService, StorageCreateOutputFileCollectionFromDiffService, StorageWriteStdoutFileService, \
    StorageLoadTestSourceService
from service.storage_run_compiler import StorageRunCompilerService
from service.storage_run_executable import StorageRunExecutableService
from service.student_master_create import StudentMasterCreateService
from service.student import StudentListSubService, StudentGetService
from service.student_dynamic import StudentDynamicGetSourceContentService, StudentDynamicClearService, \
    StudentDynamicSetSourceContentService
from service.student_mark import StudentMarkGetSubService, StudentMarkPutService, StudentMarkListService, \
    StudentMarkCheckTimestampQueryService
from service.student_stage_path_result import StudentStageResultCheckTimestampQueryService, \
    StudentStagePathResultGetService, StudentStagePathResultCheckRollbackService, StudentStageResultClearService, \
    StudentPutStageResultService, StudentGetStageResultService
from service.student_submission import StudentSubmissionExistService, StudentSubmissionGetSourceContentService, \
    StudentSubmissionListSourceRelativePathQueryService, StudentSubmissionGetFileContentQueryService, \
    StudentSubmissionGetChecksumService, StudentSubmissionExtractService
from service.testcase_config import TestCaseConfigCopyService, TestCaseConfigGetExecuteConfigMtimeService, \
    TestCaseConfigGetTestConfigMtimeService
from usecase.current_project import CurrentProjectSummaryGetUseCase, CurrentProjectInitializeStaticUseCase
from usecase.student import StudentListIDUseCase
from usecase.student_dynamic import StudentDynamicTakeDiffSnapshotUseCase
from usecase.student_mark import StudentMarkGetUseCase, StudentMarkListUseCase, StudentMarkPutUseCase
from usecase.student_mark_view_data import StudentMarkViewDataGetTestResultUseCase, \
    StudentMarkViewDataGetMarkSummaryUseCase
from usecase.student_run_build import StudentRunBuildStageUseCase
from usecase.student_run_compile import StudentRunCompileStageUseCase
from usecase.student_run_execute import StudentRunExecuteStageUseCase
from usecase.student_run_next_stage import StudentRunNextStageUseCase
from usecase.student_run_test import StudentRunTestStageUseCase
from usecase.student_source_code import StudentSourceCodeGetUseCase
from usecase.student_stage_result import StudentStageResultClearUseCase
from usecase.student_submission_folder_show import StudentSubmissionFolderShowUseCase
from usecase.student_table_cell_data import StudentTableGetStudentIDCellDataUseCase, \
    StudentTableGetStudentNameCellDataUseCase, StudentTableGetStudentStageStateCellDataUseCase, \
    StudentTableGetStudentErrorCellDataUseCase
from usecase.test_compile_stage import TestCompileStageUseCase
from usecase.testcase_config import TestCaseDeleteUseCase, TestCaseGetUseCase, TestCaseListIDUseCase, \
    TestCasePutUseCase
from usecase.testcase_list_edit import TestCaseListSummaryUseCase, TestCaseCreateNewNameUseCase, TestCaseCreateUseCase, \
    TestCaseCopyUseCase


class ProjectContainer:
    def __init__(
            self,
            *,
            project_id: ProjectID,
            match_get_best_service: MatchGetBestService,
            project_repository: ProjectRepository,
            global_settings_repository: GlobalSettingsRepository,
            test_source_repository: TestSourceRepository,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
    ) -> None:
        self._project_id = project_id
        self._match_get_best_service = match_get_best_service
        self._project_repository = project_repository
        self._global_settings_repository = global_settings_repository
        self._test_source_repository = test_source_repository
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io

    @property
    def project_id(self) -> ProjectID:
        return self._project_id

    @cached_property
    def current_project_core_io(self):
        return CurrentProjectCoreIO(
            current_project_id=self._project_id,
            project_core_io=self._project_core_io,
        )

    @cached_property
    def dynamic_path_provider(self):
        return DynamicPathProvider(
            current_project_id=self._project_id,
            project_path_provider=self._project_path_provider,
        )

    @cached_property
    def database_path_provider(self):
        return DatabasePathProvider(
            dynamic_path_provider=self.dynamic_path_provider,
        )

    @cached_property
    def project_database_io(self):
        return ProjectDatabaseIO(
            database_path_provider=self.database_path_provider,
        )

    @cached_property
    def testcase_config_path_provider(self):
        return TestCaseConfigPathProvider(
            current_project_id=self._project_id,
            project_path_provider=self._project_path_provider,
        )

    @cached_property
    def storage_path_provider(self):
        return StoragePathProvider(
            dynamic_path_provider=self.dynamic_path_provider,
        )

    @cached_property
    def project_static_path_provider(self):
        return ProjectStaticPathProvider(
            project_path_provider=self._project_path_provider,
            current_project_id=self._project_id,
        )

    @cached_property
    def student_submission_path_provider(self):
        return StudentSubmissionPathProvider(
            project_static_path_provider=self.project_static_path_provider,
        )

    @cached_property
    def compile_tool_io(self):
        return CompileToolIO()

    @cached_property
    def executable_io(self):
        return ExecutableIO()

    @cached_property
    def current_project_repository(self):
        return CurrentProjectRepository(
            current_project_id=self._project_id,
            project_repo=self._project_repository,
        )

    @cached_property
    def student_repository(self):
        return StudentRepository(
            project_database_io=self.project_database_io,
        )

    @cached_property
    def student_stage_path_result_repository(self):
        return StudentStagePathResultRepository(
            project_database_io=self.project_database_io,
        )

    @cached_property
    def testcase_config_repository(self):
        return TestCaseConfigRepository(
            testcase_config_path_provider=self.testcase_config_path_provider,
            current_project_core_io=self.current_project_core_io,
        )

    @cached_property
    def storage_repository(self):
        return StorageRepository(
            storage_path_provider=self.storage_path_provider,
            current_project_core_io=self.current_project_core_io,
        )

    @cached_property
    def student_executable_repository(self):
        return StudentExecutableRepository(
            project_database_io=self.project_database_io,
        )

    @cached_property
    def student_source_repository(self):
        return StudentSourceRepository(
            project_database_io=self.project_database_io,
        )

    @cached_property
    def student_mark_repository(self):
        return StudentMarkRepository(
            project_database_io=self.project_database_io,
        )

    @cached_property
    def task_manager(self):
        return TaskManager(
            global_settings_repo=self._global_settings_repository,
        )

    @cached_property
    def current_project_get_service(self):
        return CurrentProjectGetService(
            current_project_repo=self.current_project_repository,
        )

    @cached_property
    def current_project_set_initialized_service(self):
        return CurrentProjectSetInitializedService(
            current_project_repo=self.current_project_repository,
        )

    @cached_property
    def student_list_sub_service(self):
        return StudentListSubService(
            student_repo=self.student_repository,
        )

    @cached_property
    def student_submission_exist_service(self):
        return StudentSubmissionExistService(
            student_repo=self.student_repository,
        )

    @cached_property
    def student_get_service(self):
        return StudentGetService(
            student_repo=self.student_repository,
        )

    @cached_property
    def stage_path_list_sub_service(self):
        return StagePathListSubService(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def stage_path_get_by_testcase_id_service(self):
        return StagePathGetByTestCaseIDService(
            stage_path_list_sub_service=self.stage_path_list_sub_service,
        )

    @cached_property
    def student_stage_path_result_get_service(self):
        return StudentStagePathResultGetService(
            student_stage_path_result_repo=self.student_stage_path_result_repository,
        )

    @cached_property
    def student_stage_result_check_timestamp_query_service(self):
        return StudentStageResultCheckTimestampQueryService(
            student_stage_path_result_repo=self.student_stage_path_result_repository,
        )

    @cached_property
    def student_mark_check_timestamp_query_service(self):
        return StudentMarkCheckTimestampQueryService(
            student_mark_repo=self.student_mark_repository,
        )

    @cached_property
    def student_mark_get_sub_service(self):
        return StudentMarkGetSubService(
            student_mark_repo=self.student_mark_repository,
        )

    @cached_property
    def student_mark_list_service(self):
        return StudentMarkListService(
            student_list_sub_service=self.student_list_sub_service,
            student_mark_get_sub_service=self.student_mark_get_sub_service,
        )

    @cached_property
    def student_mark_put_service(self):
        return StudentMarkPutService(
            student_mark_repo=self.student_mark_repository,
        )

    @cached_property
    def student_submission_list_source_relative_path_query_service(self):
        return StudentSubmissionListSourceRelativePathQueryService(
            student_submission_path_provider=self.student_submission_path_provider,
            current_project_core_io=self.current_project_core_io,
            current_project_repo=self.current_project_repository,
        )

    @cached_property
    def student_submission_get_file_content_query_service(self):
        return StudentSubmissionGetFileContentQueryService(
            student_submission_path_provider=self.student_submission_path_provider,
            current_project_core_io=self.current_project_core_io,
        )

    @cached_property
    def student_submission_get_source_content_service(self):
        return StudentSubmissionGetSourceContentService(
            student_submission_list_source_relative_path_query_service=self.student_submission_list_source_relative_path_query_service,
            student_submission_get_file_content_query_service=self.student_submission_get_file_content_query_service,
            student_repo=self.student_repository,
        )

    @cached_property
    def student_dynamic_clear_service(self):
        return StudentDynamicClearService(
            student_source_repo=self.student_source_repository,
            student_execute_repo=self.student_executable_repository,
        )

    @cached_property
    def student_dynamic_set_source_content_service(self):
        return StudentDynamicSetSourceContentService(
            student_source_repo=self.student_source_repository,
        )

    @cached_property
    def student_dynamic_get_source_content_service(self):
        return StudentDynamicGetSourceContentService(
            student_source_repo=self.student_source_repository,
        )

    @cached_property
    def student_submission_get_checksum_service(self):
        return StudentSubmissionGetChecksumService(
            student_submission_path_provider=self.student_submission_path_provider,
            current_project_core_io=self.current_project_core_io,
        )

    @cached_property
    def testcase_config_get_execute_config_mtime_service(self):
        return TestCaseConfigGetExecuteConfigMtimeService(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def testcase_config_get_test_config_mtime_service(self):
        return TestCaseConfigGetTestConfigMtimeService(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def student_stage_path_result_check_rollback_service(self):
        return StudentStagePathResultCheckRollbackService(
            student_submission_get_checksum_service=self.student_submission_get_checksum_service,
            testcase_config_get_execute_config_mtime_service=self.testcase_config_get_execute_config_mtime_service,
            testcase_config_get_test_config_mtime_service=self.testcase_config_get_test_config_mtime_service,
        )

    @cached_property
    def student_put_stage_result_service(self):
        return StudentPutStageResultService(
            student_stage_path_result_repo=self.student_stage_path_result_repository,
        )

    @cached_property
    def student_get_stage_result_service(self):
        return StudentGetStageResultService(
            student_stage_path_result_repo=self.student_stage_path_result_repository,
        )

    @cached_property
    def student_stage_result_clear_service(self):
        return StudentStageResultClearService(
            stage_path_list_sub_service=self.stage_path_list_sub_service,
            student_stage_path_result_repo=self.student_stage_path_result_repository,
        )

    @cached_property
    def storage_create_service(self):
        return StorageCreateService(storage_repo=self.storage_repository)

    @cached_property
    def storage_load_student_source_service(self):
        return StorageLoadStudentSourceService(
            student_source_repo=self.student_source_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_load_test_source_service(self):
        return StorageLoadTestSourceService(
            test_source_repo=self._test_source_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_store_student_executable_service(self):
        return StorageStoreStudentExecutableService(
            student_executable_repo=self.student_executable_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_run_compiler_service(self):
        return StorageRunCompilerService(
            compile_tool_io=self.compile_tool_io,
            global_settings_repo=self._global_settings_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_delete_service(self):
        return StorageDeleteService(storage_repo=self.storage_repository)

    @cached_property
    def storage_load_student_executable_service(self):
        return StorageLoadStudentExecutableService(
            student_executable_repo=self.student_executable_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_load_execute_config_input_files_service(self):
        return StorageLoadExecuteConfigInputFilesService(
            storage_repo=self.storage_repository,
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def storage_take_snapshot_service(self):
        return StorageTakeSnapshotService(
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_run_executable_service(self):
        return StorageRunExecutableService(
            storage_repo=self.storage_repository,
            executable_io=self.executable_io,
        )

    @cached_property
    def storage_create_output_file_collection_from_diff_service(self):
        return StorageCreateOutputFileCollectionFromDiffService(
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_write_stdout_file_service(self):
        return StorageWriteStdoutFileService(
            storage_repo=self.storage_repository,
        )

    @cached_property
    def testcase_config_copy_service(self):
        return TestCaseConfigCopyService(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def student_folder_show_in_explorer_io(self):
        return StudentFolderShowInExplorerIO(
            student_submission_path_provider=self.student_submission_path_provider,
        )

    @cached_property
    def current_project_summary_get_usecase(self):
        return CurrentProjectSummaryGetUseCase(
            current_project_get_service=self.current_project_get_service,
        )

    def create_current_project_initialize_static_usecase(self, *, manaba_report_archive_fullpath: Path):
        manaba_report_archive_io = ManabaReportArchiveIO(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        )
        return CurrentProjectInitializeStaticUseCase(
            student_master_create_service=StudentMasterCreateService(
                student_repo=self.student_repository,
                manaba_report_archive_io=manaba_report_archive_io,
            ),
            student_submission_extract_service=StudentSubmissionExtractService(
                student_repo=self.student_repository,
                manaba_report_archive_io=manaba_report_archive_io,
                current_project_core_io=self.current_project_core_io,
                student_submission_path_provider=self.student_submission_path_provider,
            ),
            current_project_set_initialized_service=self.current_project_set_initialized_service,
        )

    @cached_property
    def student_list_id_usecase(self):
        return StudentListIDUseCase(
            student_list_sub_service=self.student_list_sub_service,
        )

    @cached_property
    def student_table_get_student_id_cell_data_usecase(self):
        return StudentTableGetStudentIDCellDataUseCase(
            student_submission_exist_service=self.student_submission_exist_service,
        )

    @cached_property
    def student_table_get_student_name_cell_data_usecase(self):
        return StudentTableGetStudentNameCellDataUseCase(
            student_get_service=self.student_get_service,
        )

    @cached_property
    def student_table_get_student_stage_state_cell_data_usecase(self):
        return StudentTableGetStudentStageStateCellDataUseCase(
            stage_path_list_sub_service=self.stage_path_list_sub_service,
            student_stage_path_result_get_service=self.student_stage_path_result_get_service,
        )

    @cached_property
    def student_table_get_student_error_cell_data_usecase(self):
        return StudentTableGetStudentErrorCellDataUseCase(
            stage_path_list_sub_service=self.stage_path_list_sub_service,
            student_stage_path_result_get_service=self.student_stage_path_result_get_service,
        )

    @cached_property
    def student_dynamic_take_diff_snapshot_usecase(self):
        return StudentDynamicTakeDiffSnapshotUseCase(
            student_stage_result_check_timestamp_query_service=self.student_stage_result_check_timestamp_query_service,
            student_mark_check_timestamp_query_service=self.student_mark_check_timestamp_query_service,
        )

    @cached_property
    def student_mark_get_usecase(self):
        return StudentMarkGetUseCase(
            student_mark_get_sub_service=self.student_mark_get_sub_service,
        )

    @cached_property
    def student_mark_list_usecase(self):
        return StudentMarkListUseCase(
            student_mark_list_service=self.student_mark_list_service,
        )

    @cached_property
    def testcase_config_list_id_usecase(self):
        return TestCaseListIDUseCase(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def student_mark_view_data_get_test_result_usecase(self):
        return StudentMarkViewDataGetTestResultUseCase(
            stage_path_get_by_testcase_id_service=self.stage_path_get_by_testcase_id_service,
            student_stage_path_result_get_service=self.student_stage_path_result_get_service,
        )

    @cached_property
    def student_mark_view_data_get_mark_summary_usecase(self):
        return StudentMarkViewDataGetMarkSummaryUseCase(
            student_get_service=self.student_get_service,
            student_mark_get_sub_service=self.student_mark_get_sub_service,
            stage_path_list_sub_service=self.stage_path_list_sub_service,
            student_stage_path_result_get_service=self.student_stage_path_result_get_service,
            student_stage_path_result_check_rollback_service=self.student_stage_path_result_check_rollback_service,
        )

    @cached_property
    def student_source_code_get_usecase(self):
        return StudentSourceCodeGetUseCase(
            student_source_code_get_query_service=self.student_dynamic_get_source_content_service,
        )

    @cached_property
    def student_mark_put_usecase(self):
        return StudentMarkPutUseCase(
            student_mark_put_service=self.student_mark_put_service,
        )

    @cached_property
    def student_submission_folder_show_usecase(self):
        return StudentSubmissionFolderShowUseCase(
            student_folder_show_in_explorer_io=self.student_folder_show_in_explorer_io,
        )

    @cached_property
    def student_run_build_stage_usecase(self):
        return StudentRunBuildStageUseCase(
            student_submission_get_source_content_service=self.student_submission_get_source_content_service,
            student_dynamic_clear_service=self.student_dynamic_clear_service,
            student_dynamic_set_source_content_service=self.student_dynamic_set_source_content_service,
            student_submission_get_checksum_service=self.student_submission_get_checksum_service,
            student_put_stage_result_service=self.student_put_stage_result_service,
        )

    @cached_property
    def student_run_compile_stage_usecase(self):
        return StudentRunCompileStageUseCase(
            storage_create_service=self.storage_create_service,
            storage_load_student_source_service=self.storage_load_student_source_service,
            storage_store_student_executable_service=self.storage_store_student_executable_service,
            storage_run_compiler_service=self.storage_run_compiler_service,
            storage_delete_service=self.storage_delete_service,
            student_put_stage_result_service=self.student_put_stage_result_service,
        )

    @cached_property
    def test_compile_stage_usecase(self):
        return TestCompileStageUseCase(
            storage_create_service=self.storage_create_service,
            storage_load_test_source_service=self.storage_load_test_source_service,
            storage_run_compiler_service=self.storage_run_compiler_service,
            storage_delete_service=self.storage_delete_service,
        )

    @cached_property
    def student_run_execute_stage_usecase(self):
        return StudentRunExecuteStageUseCase(
            storage_create_service=self.storage_create_service,
            storage_load_student_executable_service=self.storage_load_student_executable_service,
            storage_load_execute_config_input_files_service=self.storage_load_execute_config_input_files_service,
            storage_take_snapshot_service=self.storage_take_snapshot_service,
            storage_delete_service=self.storage_delete_service,
            student_put_stage_result_service=self.student_put_stage_result_service,
            testcase_config_get_execute_config_mtime_service=self.testcase_config_get_execute_config_mtime_service,
            storage_run_executable_service=self.storage_run_executable_service,
            testcase_config_repo=self.testcase_config_repository,
            storage_create_output_file_mapping_from_diff_service=self.storage_create_output_file_collection_from_diff_service,
            storage_write_stdout_file_service=self.storage_write_stdout_file_service,
        )

    @cached_property
    def student_run_test_stage_usecase(self):
        return StudentRunTestStageUseCase(
            testcase_config_repo=self.testcase_config_repository,
            student_put_stage_result_service=self.student_put_stage_result_service,
            student_get_stage_result_service=self.student_get_stage_result_service,
            testcase_config_get_test_config_mtime_service=self.testcase_config_get_test_config_mtime_service,
            match_get_best_service=self._match_get_best_service,
        )

    @cached_property
    def student_run_next_stage_usecase(self):
        return StudentRunNextStageUseCase(
            stage_path_list_sub_service=self.stage_path_list_sub_service,
            student_stage_path_result_get_service=self.student_stage_path_result_get_service,
            student_stage_path_result_repo=self.student_stage_path_result_repository,
            student_run_build_stage_usecase=self.student_run_build_stage_usecase,
            student_run_compile_stage_usecase=self.student_run_compile_stage_usecase,
            student_run_execute_stage_usecase=self.student_run_execute_stage_usecase,
            student_run_test_stage_usecase=self.student_run_test_stage_usecase,
            student_stage_path_result_check_rollback_service=self.student_stage_path_result_check_rollback_service,
        )

    @cached_property
    def student_stage_result_clear_usecase(self):
        return StudentStageResultClearUseCase(
            student_stage_result_clear_service=self.student_stage_result_clear_service,
        )

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
            testcase_config_copy_service=self.testcase_config_copy_service,
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
