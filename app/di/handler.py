from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.handler.interface import INavigator

import app.di.usecase as di_usecase
from feature.about.handler.about_dialog import AboutDialogHandler
from feature.export.handler.score_export_dialog import ScoreExportDialogHandler
from feature.projman.handler.launcher_handler import ProjectLauncherHandler
from feature.projman.handler.project_create import ProjectCreateHandler
from feature.projman.handler.project_list import ProjectListHandler
from feature.setting.handler.compiler_search_handler import CompilerSearchHandler
from feature.setting.handler.settings_edit import SettingEditHandler
from feature.workspace.handler.workspace_window_handler import WorkspaceWindowHandler


def get_project_launcher_handler(
    *,
    view,
    navigator: "INavigator",
) -> ProjectLauncherHandler:
    """ProjectLauncherHandlerを生成"""
    return ProjectLauncherHandler(
        view=view,
        navigator=navigator,
        project_list_usecase=di_usecase.get_project_list_recent_summary_usecase(),
    )


def get_project_create_handler(
    *,
    view,
    navigator: "INavigator",
) -> ProjectCreateHandler:
    """ProjectCreateHandlerを生成"""
    return ProjectCreateHandler(
        view=view,
        navigator=navigator,
        project_check_exist_usecase=di_usecase.get_project_check_exist_by_name_usecase(),
        project_create_usecase=di_usecase.get_project_create_usecase(),
    )


def get_project_list_handler(
    *,
    view,
    navigator: "INavigator",
) -> ProjectListHandler:
    """ProjectListHandlerを生成"""
    return ProjectListHandler(
        view=view,
        navigator=navigator,
        project_list_usecase=di_usecase.get_project_list_recent_summary_usecase(),
        project_update_last_opened_usecase=di_usecase.get_project_update_last_opened_usecase(),
        project_folder_show_usecase=di_usecase.get_project_folder_show_usecase(),
        project_delete_usecase=di_usecase.get_project_delete_usecase(),
        project_base_folder_show_usecase=di_usecase.get_project_base_folder_show_usecase(),
        project_get_size_usecase=di_usecase.get_project_get_size_query_usecase(),
    )


def get_workspace_window_handler(
    *,
    view,
    navigator: "INavigator",
) -> WorkspaceWindowHandler:
    """WorkspaceWindowHandlerを生成"""
    return WorkspaceWindowHandler(
        view=view,
        navigator=navigator,
    )


def get_compiler_search_handler() -> CompilerSearchHandler:
    """CompilerSearchHandlerを生成"""
    return CompilerSearchHandler(
        view=None,  # Dialog内で生成されるViewが設定される
        compiler_search_usecase=di_usecase.get_compiler_search_usecase(),
    )


def get_setting_edit_handler(
    *,
    navigator: "INavigator",
) -> SettingEditHandler:
    """SettingEditHandlerを生成"""
    return SettingEditHandler(
        view=None,  # Dialog内で生成されるViewが設定される
        navigator=navigator,
        setting_get_usecase=di_usecase.get_setting_get_usecase(),
        setting_put_usecase=di_usecase.get_setting_put_usecase(),
        test_compile_stage_usecase=di_usecase.get_test_compile_stage_usecase(),
        compiler_search_usecase=di_usecase.get_compiler_search_usecase(),
    )


def get_about_dialog_handler() -> AboutDialogHandler:
    """AboutDialogHandlerを生成"""
    return AboutDialogHandler(
        view=None,  # Dialog内で生成されるViewが設定される
        get_about_info_usecase=di_usecase.get_about_info_usecase(),
    )


def get_score_export_dialog_handler(
    *,
    target_id,
) -> ScoreExportDialogHandler:
    """ScoreExportDialogHandlerを生成"""
    return ScoreExportDialogHandler(
        view=None,  # Dialog内で生成されるViewが設定される
        score_export_usecase=di_usecase.get_score_export_usecase(),
        student_list_id_usecase=di_usecase.get_student_list_id_usecase(),
        student_mark_list_usecase=di_usecase.get_student_mark_list_usecase(),
        setting_get_usecase=di_usecase.get_setting_get_usecase(),
        target_id=target_id,
    )
