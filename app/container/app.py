from functools import cached_property
from pathlib import Path

from feature.export.domain.interface.gateway import ISimpleScoreExportGateway, IExcelBackupGateway
from feature.export.domain.interface.service import IExcelScoreUpdatePlanningService
from feature.projman.domain.interface.gateway import (
    IProjectListGateway,
    IProjectConfigStateGateway,
    IProjectFileSystemGateway,
    IStudentSubmissionListSourceRelativePathGateway,
    IStudentSubmissionGetFileContentGateway,
)
from feature.setting.domain.interface.gateway import IFindCompilerPathGateway
from shared.domain.interface.event import IEventBus
from shared.domain.interface.gateway import (
    IStudentSubmissionGetSourceContentGateway,
    IStudentSubmissionGetChecksumGateway,
    IStudentSubmissionFolderShowGateway,
    ICurrentDatetimeGateway,
    IResourceUsageGateway,
    IFolderShowInExplorerGateway,
    IExcelGateway,
    IDatabaseInitializeGateway, IProjectDeleteGateway,
)
from shared.domain.interface.path_manager import IAppPathManager, IProjectPathManager, \
    IProjectPathManagerFactory
from shared.domain.interface.repository import IAppNameProvider, IAppVersionProvider, \
    ICurrentProjectRepository, IProjectRepository, \
    ISettingRepository, IStorageRepository, IStudentExecutableRepository, IStudentRepository, \
    IStudentScoreRepository, IStudentSourceRepository, IStudentStageResultRepository, \
    ITestCaseRepository, ITestSourceRepository
from shared.domain.interface.service import IMatchGetBestService, IStagePathGetByTestCaseIDService, IStagePathListSubService, IStorageCreateOutputFileCollectionFromDiffService, IStorageCreateService, IStorageDeleteService, IStorageLoadExecuteConfigInputFilesService, IStorageLoadStudentExecutableService, IStorageLoadStudentSourceService, IStorageLoadTestSourceService, IStorageRunCompilerService, IStorageRunExecutableService, IStorageStoreStudentExecutableService, IStorageTakeSnapshotService, IStorageWriteStdoutFileService, IStudentDynamicClearService, IStudentDynamicSetSourceContentService, IStudentGetStagePathResultMapService, IStudentMarkEntityGetSubService, IStudentMarkEntityListService, IStudentPutStagePathResultEntityService, IStudentStagePathResultAnalyzerService, IStudentStagePathResultEntityCheckRollbackService, IStudentStagePathResultEntityCheckTimestampQueryService, IStudentStagePathResultEntityClearService, IStudentStagePathResultEntityRollbackService, ITestCaseConfigCopyService
from shared.domain.interface.state import ICurrentProjectIDState, IDebugModeState
from shared.domain.interface.system import IGlobalCoreIO, IProjectCoreIO, IManabaReportArchiveIO
from shared.domain.interface.system import (
    ITaskManager,
)
from shared.handler.interface import INavigator


class AppContainer:
    def __init__(
            self,
    ):
        pass

    # app

    @cached_property
    def app_path_manager(self) -> IAppPathManager:
        from shared.infra.path_manager import AppPathManager
        return AppPathManager()

    @cached_property
    def project_path_manager_factory(self) -> IProjectPathManagerFactory:
        from shared.infra.path_manager import ProjectPathManagerFactory
        return ProjectPathManagerFactory(
            app_path_manager=self.app_path_manager,
        )

    @cached_property
    def current_project_id_state(self) -> ICurrentProjectIDState:
        from shared.infra.state.current_project_id_state import CurrentProjectIDState
        return CurrentProjectIDState()

    @cached_property
    def debug_mode_state(self) -> IDebugModeState:
        from shared.infra.state.debug_mode import DebugModeState
        return DebugModeState()

    @cached_property
    def app_name_provider(self) -> IAppNameProvider:
        from shared.infra.provider.app_name import StaticAppNameProvider
        return StaticAppNameProvider()

    @cached_property
    def app_version_provider(self) -> IAppVersionProvider:
        from shared.infra.provider.app_version import JsonAppVersionProvider
        return JsonAppVersionProvider(
            app_version_json_fullpath=self.app_path_manager.get_app_version_json_path(),
            global_core_io=self.global_core_io,
        )

    @cached_property
    def global_core_io(self) -> IGlobalCoreIO:
        from shared.infra.system.global_core_io import GlobalCoreIO
        return GlobalCoreIO()

    @cached_property
    def manaba_report_archive_io(self) -> IManabaReportArchiveIO:
        from shared.infra.system.report_archive import ManabaReportArchiveIO
        return ManabaReportArchiveIO()

    @cached_property
    def project_core_io_factory(self):
        from shared.infra.system.project_core_io import ProjectCoreIOFactory
        return ProjectCoreIOFactory(
            app_path_manager_factory=self.app_path_manager,
        )

    @cached_property
    def compile_tool_io(self):
        from shared.infra.system.compile_tool import CompileToolIO
        return CompileToolIO()

    @cached_property
    def setting_repository(self) -> ISettingRepository:
        from shared.infra.repository.setting import SettingRepository
        return SettingRepository(
            setting_json_path=self.app_path_manager.get_setting_json_path(),
            global_core_io=self.global_core_io,
        )

    @cached_property
    def test_source_repository(self) -> ITestSourceRepository:
        from shared.infra.repository.test_source import TestSourceRepository
        return TestSourceRepository(
            test_source_file_fullpath=self.app_path_manager.get_test_source_c_path(),
            global_core_io=self.global_core_io,
        )

    @cached_property
    def navigator(self) -> INavigator:
        from app.navigator import Navigator
        return Navigator()

    @cached_property
    def event_bus(self) -> IEventBus:
        from shared.infra.event import QtEventBus
        return QtEventBus()

    @cached_property
    def current_datetime_gateway(self) -> ICurrentDatetimeGateway:
        from shared.infra.gateway.current_datetime import CurrentDatetimeGateway
        return CurrentDatetimeGateway()

    @cached_property
    def resource_usage_gateway(self) -> IResourceUsageGateway:
        from shared.infra.gateway.resource_usage import ResourceUsageGateway
        return ResourceUsageGateway()

    @cached_property
    def folder_show_in_explorer_gateway(self) -> IFolderShowInExplorerGateway:
        from shared.infra.gateway.folder_show_in_explorer import FolderShowInExplorerGateway
        return FolderShowInExplorerGateway()

    @cached_property
    def project_delete_gateway(self) -> IProjectDeleteGateway:
        from shared.infra.gateway.project_delete import ProjectDeleteGateway
        return ProjectDeleteGateway(
            app_path_manager=self.app_path_manager,
            project_core_io_factory=self.project_core_io_factory,
        )

    # feature/about

    # feature/export

    @cached_property
    def json_score_export_gateway(self) -> ISimpleScoreExportGateway:
        from feature.export.infra.gateway.json_export import JsonScoreExportGateway
        return JsonScoreExportGateway()

    @cached_property
    def csv_score_export_gateway(self) -> ISimpleScoreExportGateway:
        from feature.export.infra.gateway.csv_export import CsvScoreExportGateway
        return CsvScoreExportGateway()

    @cached_property
    def excel_gateway(self) -> IExcelGateway:
        from shared.infra.gateway.excel_gateway import ExcelGateway
        return ExcelGateway()

    @cached_property
    def excel_backup_gateway(self) -> IExcelBackupGateway:
        from feature.export.infra.gateway.excel_backup import ExcelBackupGateway
        return ExcelBackupGateway()

    # feature/projman

    @cached_property
    def project_list_gateway(self) -> IProjectListGateway:
        from feature.projman.infra.gateway.project import ProjectListGateway
        return ProjectListGateway(
            project_list_dir=self.app_path_manager.get_project_list_dir(),
        )

    @cached_property
    def project_config_state_gateway(self) -> IProjectConfigStateGateway:
        from feature.projman.infra.gateway.project import ProjectConfigStateGateway
        return ProjectConfigStateGateway(
            project_path_manager_factory=self.project_path_manager_factory,
            project_core_io_factory=self.project_core_io_factory,
            app_version_provider=self.app_version_provider,
        )

    # feature/scoring

    # feature/setting

    @cached_property
    def find_compiler_path_gateway(self) -> IFindCompilerPathGateway:
        from feature.setting.infra.gateway.compiler_location import VSFindCompilerPathGateway
        return VSFindCompilerPathGateway(
            start_locations=self.app_path_manager.get_vs_compiler_search_start_locations(),
        )

    # feature/testcase

    # feature/workspace


class ProjectContainer:
    def __init__(
            self,
            app_container: AppContainer,
            project_base_dir: Path,
    ) -> None:
        self._app_container = app_container
        self._project_base_dir = project_base_dir

    # app

    @cached_property
    def project_path_manager(self) -> IProjectPathManager:
        from shared.infra.path_manager import ProjectPathManager
        return ProjectPathManager(
            project_base_dir=self._project_base_dir,
        )

    @cached_property
    def project_core_io(self) -> IProjectCoreIO:
        from shared.infra.system.project_core_io import ProjectCoreIO
        return ProjectCoreIO(
            project_dir=self.project_path_manager.get_base_dir(),
        )

    @cached_property
    def task_manager(self) -> ITaskManager:
        from shared.infra.system.task_manager import TaskManager
        return TaskManager(
            max_workers=self._app_container.project_config_state_gateway.get().max_workers,
        )

    @cached_property
    def database_initialize_gateway(self) -> IDatabaseInitializeGateway:
        from shared.infra.gateway.database_initialize_gateway import DatabaseInitializeGateway
        return DatabaseInitializeGateway(
            db_path=self.project_path_manager.get_database_path(),
        )

    @cached_property
    def project_repository(self) -> IProjectRepository:
        from shared.infra.repository.project import ProjectRepository
        return ProjectRepository(
            project_folder_fullpath=self.app_path_manager.get_project_dir(),
            project_config_json_fullpath=self.app_path_manager.get_project_config_json(),
            project_core_io_factory=self.project_core_io_factory,
        )

    @cached_property
    def current_project_repository(self) -> ICurrentProjectRepository:
        # TODO: 廃止予定
        from shared.infra.repository.current_project import CurrentProjectRepository
        return CurrentProjectRepository(
            current_project_id=self.current_project_id_state.get(),
            project_repository=self.project_repository,
        )

    @cached_property
    def student_repository(self) -> IStudentRepository:
        from shared.infra.repository.student import StudentRepository
        return StudentRepository(
            db_path=self.project_path_manager.get_database_path(),
        )

    @cached_property
    def student_stage_result_repository(self) -> IStudentStageResultRepository:
        from shared.infra.repository.student_stage_path_result import StudentStageResultRepository
        return StudentStageResultRepository(
            db_path=self.project_path_manager.get_database_path(),
        )

    @cached_property
    def testcase_config_repository(self) -> ITestCaseRepository:
        from shared.infra.repository.testcase import TestCaseRepository
        return TestCaseRepository(
            db_path=self.project_path_manager.get_database_path(),
        )

    @cached_property
    def storage_repository(self) -> IStorageRepository:
        from shared.infra.repository.storage import StorageRepository
        return StorageRepository(
            project_path_manager=self.project_path_manager,
            current_project_core_io=self.project_core_io,
        )

    @cached_property
    def student_executable_repository(self) -> IStudentExecutableRepository:
        from shared.infra.repository.student_dynamic import StudentExecutableRepository
        return StudentExecutableRepository(
            db_path=self.project_path_manager.get_database_path(),
        )

    @cached_property
    def student_source_repository(self) -> IStudentSourceRepository:
        from shared.infra.repository.student_dynamic import StudentSourceRepository
        return StudentSourceRepository(
            db_path=self.project_path_manager.get_database_path(),
        )

    @cached_property
    def student_score_repository(self) -> IStudentScoreRepository:
        from shared.infra.repository.student_mark import StudentScoreRepository
        return StudentScoreRepository(
            db_path=self.project_path_manager.get_database_path(),
        )

    @cached_property
    def stage_path_list_sub_service(self) -> IStagePathListSubService:
        from shared.domain.service.stage_path import StagePathListSubService
        return StagePathListSubService(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def stage_path_get_by_testcase_id_service(self) -> IStagePathGetByTestCaseIDService:
        from shared.domain.service.stage_path import StagePathGetByTestCaseIDService
        return StagePathGetByTestCaseIDService(
            stage_path_list_sub_service=self.stage_path_list_sub_service,
        )

    @cached_property
    def student_stage_path_result_entity_check_rollback_service(self) -> IStudentStagePathResultEntityCheckRollbackService:
        from shared.domain.service.student_stage_path_result import StudentStagePathResultEntityCheckRollbackService
        return StudentStagePathResultEntityCheckRollbackService(
            student_submission_get_checksum_gateway=self.student_submission_get_checksum_gateway,
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def student_stage_path_result_entity_check_timestamp_query_service(self) -> IStudentStagePathResultEntityCheckTimestampQueryService:
        from shared.domain.service.student_stage_path_result import StudentStagePathResultEntityCheckTimestampQueryService
        return StudentStagePathResultEntityCheckTimestampQueryService(
            student_stage_result_repo=self.student_stage_result_repository,
        )

    @cached_property
    def storage_create_service(self) -> IStorageCreateService:
        from shared.domain.service.storage import StorageCreateService
        return StorageCreateService(
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_delete_service(self) -> IStorageDeleteService:
        from shared.domain.service.storage import StorageDeleteService
        return StorageDeleteService(
            storage_repo=self.storage_repository,
        )
    
    @cached_property
    def storage_load_test_source_service(self) -> IStorageLoadTestSourceService:
        from shared.domain.service.storage import StorageLoadTestSourceService
        return StorageLoadTestSourceService(
            test_source_repo=self.test_source_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_run_compiler_service(self) -> IStorageRunCompilerService:
        from shared.domain.service.storage import StorageRunCompilerService
        return StorageRunCompilerService(
            compile_tool_io=self.compile_tool_io,
            setting_repo=self.setting_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_load_student_source_service(self) -> IStorageLoadStudentSourceService:
        from shared.domain.service.storage import StorageLoadStudentSourceService
        return StorageLoadStudentSourceService(
            student_source_repo=self.student_source_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_load_student_executable_service(self) -> IStorageLoadStudentExecutableService:
        from shared.domain.service.storage import StorageLoadStudentExecutableService
        return StorageLoadStudentExecutableService(
            student_executable_repo=self.student_executable_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_store_student_executable_service(self) -> IStorageStoreStudentExecutableService:
        from shared.domain.service.storage import StorageStoreStudentExecutableService
        return StorageStoreStudentExecutableService(
            student_executable_repo=self.student_executable_repository,
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_load_execute_config_input_files_service(self) -> IStorageLoadExecuteConfigInputFilesService:
        from shared.domain.service.storage import StorageLoadExecuteConfigInputFilesService
        return StorageLoadExecuteConfigInputFilesService(
            storage_repo=self.storage_repository,
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def storage_write_stdout_file_service(self) -> IStorageWriteStdoutFileService:
        from shared.domain.service.storage import StorageWriteStdoutFileService
        return StorageWriteStdoutFileService(
            storage_repo=self.storage_repository,
        )

    @cached_property
    def storage_take_snapshot_service(self) -> IStorageTakeSnapshotService:
        from shared.domain.service.storage import StorageTakeSnapshotService
        return StorageTakeSnapshotService(
            storage_repo=self.storage_repository,
        )

    @cached_property
    def student_stage_path_result_entity_rollback_service(self) -> IStudentStagePathResultEntityRollbackService:
        from shared.domain.service.student_stage_path_result import StudentStagePathResultEntityRollbackService
        return StudentStagePathResultEntityRollbackService(
            student_stage_result_repo=self.student_stage_result_repository,
        )

    @cached_property
    def student_stage_path_result_entity_clear_service(self) -> IStudentStagePathResultEntityClearService:
        from shared.domain.service.student_stage_path_result import StudentStagePathResultEntityClearService
        return StudentStagePathResultEntityClearService(
            stage_path_list_sub_service=self.stage_path_list_sub_service,
            student_stage_result_repo=self.student_stage_result_repository,
        )

    @cached_property
    def student_put_stage_path_result_entity_service(self) -> IStudentPutStagePathResultEntityService:
        from shared.domain.service.student_stage_path_result import StudentPutStagePathResultEntityService
        return StudentPutStagePathResultEntityService(
            student_stage_result_repo=self.student_stage_result_repository,
        )

    @cached_property
    def student_get_stage_path_result_map_service(self) -> IStudentGetStagePathResultMapService:
        from shared.domain.service.student_stage_path_result import StudentGetStagePathResultMapService
        return StudentGetStagePathResultMapService(
            student_stage_result_repo=self.student_stage_result_repository,
        )

    @cached_property
    def student_stage_path_result_analyzer_service(self) -> IStudentStagePathResultAnalyzerService:
        from shared.domain.service.student_stage_result_analyzer import StudentStageResultAnalyzerService
        return StudentStageResultAnalyzerService()

    @cached_property
    def testcase_config_copy_service(self) -> ITestCaseConfigCopyService:
        from shared.domain.service.testcase_config_copy import TestCaseConfigCopyService
        return TestCaseConfigCopyService(
            testcase_config_repo=self.testcase_config_repository,
        )

    @cached_property
    def student_dynamic_clear_service(self) -> IStudentDynamicClearService:
        from shared.domain.service.student_dynamic import StudentDynamicClearService
        return StudentDynamicClearService(
            student_source_repo=self.student_source_repository,
            student_execute_repo=self.student_executable_repository,
        )

    @cached_property
    def student_dynamic_set_source_content_service(self) -> IStudentDynamicSetSourceContentService:
        from shared.domain.service.student_dynamic import StudentDynamicSetSourceContentService
        return StudentDynamicSetSourceContentService(
            student_source_repo=self.student_source_repository,
        )

    @cached_property
    def storage_run_executable_service(self) -> IStorageRunExecutableService:
        from shared.domain.service.storage_run_executable import StorageRunExecutableService
        return StorageRunExecutableService(
            storage_repo=self.storage_repository,
            executable_io=self.executable_io,
        )

    @cached_property
    def storage_create_output_file_mapping_from_diff_service(self) -> IStorageCreateOutputFileCollectionFromDiffService:
        from shared.domain.service.storage import StorageCreateOutputFileCollectionFromDiffService
        return StorageCreateOutputFileCollectionFromDiffService(
            storage_repo=self.storage_repository,
        )

    @cached_property
    def student_mark_get_sub_service(self) -> IStudentMarkEntityGetSubService:
        from shared.domain.service.student_mark_get import StudentMarkEntityGetSubService
        return StudentMarkEntityGetSubService(
            student_mark_repo=self.student_mark_repository,
        )

    @cached_property
    def student_mark_list_service(self) -> IStudentMarkEntityListService:
        from shared.domain.service.student_mark_list import StudentMarkEntityListService
        return StudentMarkEntityListService(
            student_repo=self.student_repository,
            student_mark_get_sub_service=self.student_mark_get_sub_service,
        )

    @cached_property
    def match_get_best_service(self) -> IMatchGetBestService:
        from shared.domain.service.match import MatchGetBestService
        return MatchGetBestService()

    @cached_property
    def excel_score_update_planning_service(self) -> IExcelScoreUpdatePlanningService:
        from feature.export.domain.service.excel_score_update_planning import ExcelScoreUpdatePlanningService
        return ExcelScoreUpdatePlanningService()

    # feature/about

    # feature/export

    # feature/projman

    @cached_property
    def project_file_system_gateway(self) -> IProjectFileSystemGateway:
        from feature.projman.infra.gateway.project import ProjectFileSystemGateway
        return ProjectFileSystemGateway(
            project_folder_fullpath=self._project_path_config.project_folder_fullpath,
            project_list_folder_fullpath=self._project_path_config.project_list_folder_fullpath,
            project_core_io=self.project_core_io,
            folder_show_in_explorer_gateway=self.folder_show_in_explorer_gateway,
        )

    @cached_property
    def student_submission_list_source_relative_path_gateway(
            self) -> IStudentSubmissionListSourceRelativePathGateway:
        from feature.projman.infra.gateway.student_submission import \
            StudentSubmissionListSourceRelativePathGateway
        return StudentSubmissionListSourceRelativePathGateway(
            student_submission_folder_fullpath=lambda
                s_id: self._project_path_config.student_submission_folder_fullpath(
                s_id),
            current_project_core_io=self.project_core_io,
            current_project_repo=self.current_project_repo,
        )

    @cached_property
    def student_submission_get_file_content_gateway(
            self) -> IStudentSubmissionGetFileContentGateway:
        from feature.projman.infra.gateway.student_submission import \
            StudentSubmissionGetFileContentGateway
        return StudentSubmissionGetFileContentGateway(
            student_submission_folder_fullpath=lambda
                s_id: self._project_path_config.student_submission_folder_fullpath(
                s_id),
            current_project_core_io=self.project_core_io,
        )

    @cached_property
    def student_submission_get_source_content_gateway(
            self) -> IStudentSubmissionGetSourceContentGateway:
        from shared.infra.gateway.student_submission import StudentSubmissionGetSourceContentGateway
        return StudentSubmissionGetSourceContentGateway(
            student_submission_list_source_relative_path_gateway=self.student_submission_list_source_relative_path_gateway,
            student_submission_get_file_content_gateway=self.student_submission_get_file_content_gateway,
            student_repo=self.student_repo,
        )

    @cached_property
    def student_submission_get_checksum_gateway(self) -> IStudentSubmissionGetChecksumGateway:
        from shared.infra.gateway.student_submission import StudentSubmissionGetChecksumGateway
        return StudentSubmissionGetChecksumGateway(
            student_submission_folder_fullpath=lambda
                s_id: self._project_path_config.student_submission_folder_fullpath(
                s_id),
            current_project_core_io=self.project_core_io,
        )

    @cached_property
    def student_submission_folder_show_gateway(self) -> IStudentSubmissionFolderShowGateway:
        from shared.infra.gateway.student_submission import StudentSubmissionFolderShowGateway
        return StudentSubmissionFolderShowGateway(
            student_submission_folder_fullpath=lambda
                s_id: self._project_path_config.student_submission_folder_fullpath(
                s_id),
            folder_show_in_explorer_gateway=self.folder_show_in_explorer_gateway,
        )

    # feature/scoring

    # feature/setting

    # feature/testcase

    # feature/workspace
