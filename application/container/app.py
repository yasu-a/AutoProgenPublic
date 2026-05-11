from functools import cached_property

from application.container.project import ProjectContainer
from domain.model.value import ProjectID
from infra.io.files.global_ import GlobalCoreIO
from infra.io.files.project import ProjectCoreIO
from infra.io.project_base_folder_show_in_explorer import ProjectFolderShowInExplorerIO
from infra.io.resource_usage import ResourceUsageIO
from infra.path_layout import AppPathConfig, AppPathLayout
from infra.repository.app_version import AppVersionRepository
from infra.repository.global_settings import GlobalSettingsRepository
from infra.repository.project import ProjectRepository
from infra.repository.test_source import TestSourceRepository
from service.match import MatchGetBestService
from service.project import ProjectListIDQueryService, ProjectGetConfigStateQueryService, ProjectUpdateTimestampService, \
    ProjectGetSizeQueryService
from usecase.app_version import AppVersionGetTextUseCase, AppVersionCheckIsStableUseCase
from usecase.compiler import CompilerSearchUseCase
from usecase.global_settings import GlobalSettingsGetUseCase, GlobalSettingsPutUseCase
from usecase.project import ProjectCreateUseCase, ProjectOpenUseCase, ProjectListRecentSummaryUseCase, \
    ProjectCheckExistByNameUseCase, ProjectBaseFolderShowUseCase, ProjectFolderShowUseCase, ProjectDeleteUseCase, \
    ProjectGetSizeQueryUseCase
from usecase.manaba_report_archive import ManabaReportArchiveValidateMasterExcelExistsUseCase
from usecase.resource_usage import ResourceUsageGetUseCase
from usecase.score_excel import ScoreExcelListWorksheetStatsUseCase, ScoreExcelHasDataUseCase, ScoreExcelApplyUseCase
from usecase.test_test_stage import TestTestStageUseCase


class AppContainer:
    def create_project_container(self, project_id: ProjectID) -> "ProjectContainer":
        return ProjectContainer(
            project_id=project_id,
            match_get_best_service=self.match_get_best_service,
            project_repository=self.project_repository,
            global_settings_repository=self.global_settings_repository,
            test_source_repository=self.test_source_repository,
            project_path_layout=self.project_repository.create_project_path_layout(project_id),
            project_core_io=self.project_core_io,
        )

    @cached_property
    def match_get_best_service(self):
        return MatchGetBestService()

    @cached_property
    def app_path_config(self):
        return AppPathConfig.production()

    @cached_property
    def app_path_layout(self):
        return AppPathLayout(config=self.app_path_config)

    @cached_property
    def global_core_io(self):
        return GlobalCoreIO()

    @cached_property
    def project_core_io(self):
        return ProjectCoreIO(
            project_store_dir=self.app_path_config.project_store_dir,
        )

    @cached_property
    def app_version_repository(self):
        return AppVersionRepository(
            app_path_layout=self.app_path_layout,
            global_core_io=self.global_core_io,
        )

    @cached_property
    def project_repository(self):
        return ProjectRepository(
            project_store_dir=self.app_path_config.project_store_dir,
            project_core_io=self.project_core_io,
        )

    @cached_property
    def test_source_repository(self):
        return TestSourceRepository(
            app_path_layout=self.app_path_layout,
            global_core_io=self.global_core_io,
        )

    @cached_property
    def global_settings_repository(self):
        return GlobalSettingsRepository(
            app_path_layout=self.app_path_layout,
            global_core_io=self.global_core_io,
        )

    @cached_property
    def project_list_id_query_service(self):
        return ProjectListIDQueryService(
            project_repo=self.project_repository,
        )

    @cached_property
    def project_get_config_state_query_service(self):
        return ProjectGetConfigStateQueryService(
            project_repo=self.project_repository,
            project_core_io=self.project_core_io,
            app_version_repo=self.app_version_repository,
        )

    @cached_property
    def project_update_timestamp_service(self):
        return ProjectUpdateTimestampService(
            project_repo=self.project_repository,
        )

    @cached_property
    def project_get_size_query_service(self):
        return ProjectGetSizeQueryService(
            project_repo=self.project_repository,
            project_core_io=self.project_core_io,
        )

    @cached_property
    def project_folder_show_in_explorer_io(self):
        return ProjectFolderShowInExplorerIO(
            project_store_dir=self.app_path_config.project_store_dir,
        )

    @cached_property
    def resource_usage_io(self):
        return ResourceUsageIO()

    @cached_property
    def app_version_get_text_usecase(self):
        return AppVersionGetTextUseCase(
            app_version_repo=self.app_version_repository,
        )

    @cached_property
    def app_version_check_is_stable_usecase(self):
        return AppVersionCheckIsStableUseCase(
            app_version_repo=self.app_version_repository,
        )

    @cached_property
    def global_settings_get_usecase(self):
        return GlobalSettingsGetUseCase(
            global_settings_repo=self.global_settings_repository,
        )

    @cached_property
    def global_settings_put_usecase(self):
        return GlobalSettingsPutUseCase(
            global_settings_repo=self.global_settings_repository,
        )

    @cached_property
    def resource_usage_get_usecase(self):
        return ResourceUsageGetUseCase(
            resource_usage_io=self.resource_usage_io,
        )

    @cached_property
    def compiler_search_usecase(self):
        return CompilerSearchUseCase()

    @cached_property
    def test_test_stage_usecase(self):
        return TestTestStageUseCase(
            match_get_best_service=self.match_get_best_service,
        )

    @cached_property
    def project_create_usecase(self):
        return ProjectCreateUseCase(
            project_repo=self.project_repository,
            app_version_repo=self.app_version_repository,
        )

    @cached_property
    def project_open_usecase(self):
        return ProjectOpenUseCase(
            project_update_timestamp_service=self.project_update_timestamp_service,
        )

    @cached_property
    def project_list_recent_summary_usecase(self):
        return ProjectListRecentSummaryUseCase(
            project_list_id_query_service=self.project_list_id_query_service,
            project_get_config_state_query_service=self.project_get_config_state_query_service,
            project_repo=self.project_repository,
        )

    @cached_property
    def project_check_exist_by_name_usecase(self):
        return ProjectCheckExistByNameUseCase(
            project_list_id_query_service=self.project_list_id_query_service,
        )

    @cached_property
    def project_base_folder_show_usecase(self):
        return ProjectBaseFolderShowUseCase(
            project_folder_show_in_explorer_io=self.project_folder_show_in_explorer_io,
        )

    @cached_property
    def project_folder_show_usecase(self):
        return ProjectFolderShowUseCase(
            project_folder_show_in_explorer_io=self.project_folder_show_in_explorer_io,
        )

    @cached_property
    def project_delete_usecase(self):
        return ProjectDeleteUseCase(
            project_repo=self.project_repository,
        )

    @cached_property
    def project_get_size_query_usecase(self):
        return ProjectGetSizeQueryUseCase(
            project_get_size_query_service=self.project_get_size_query_service,
        )

    @cached_property
    def manaba_report_archive_validate_master_excel_exists_usecase(self):
        return ManabaReportArchiveValidateMasterExcelExistsUseCase()

    @cached_property
    def score_excel_list_worksheet_stats_usecase(self):
        return ScoreExcelListWorksheetStatsUseCase()

    @cached_property
    def score_excel_has_data_usecase(self):
        return ScoreExcelHasDataUseCase()

    @cached_property
    def score_excel_apply_usecase(self):
        return ScoreExcelApplyUseCase()
