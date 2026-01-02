from feature.projman.handler.interface import IProjectOpenDialogView, IProjectOpenDialogHandler
from feature.projman.usecase.interface import IProjectListRecentSummaryUseCase
from shared.handler.interface import INavigator


class ProjectLauncherHandler(IProjectOpenDialogHandler):
    """
    Container Window専任のHandler
    責務: ウィンドウ表示時の初期タブ決定のみ
    """

    def __init__(
            self,
            *,
            view: IProjectOpenDialogView,
            navigator: INavigator,
            project_list_usecase: IProjectListRecentSummaryUseCase,
    ):
        self._view = view
        self._navigator = navigator
        self._project_list_usecase = project_list_usecase

    def on_view_initialized(self) -> None:
        """プロジェクト存在チェック → タブ切り替え"""
        projects = self._project_list_usecase.execute()
        if projects:  # プロジェクトあり
            self._view.switch_to_list_tab()
        else:  # プロジェクトなし
            self._view.switch_to_create_tab()
        # 注意: ここでは子Viewのロード処理は呼ばない（独立性の原則）

    def on_setting_requested(self) -> None:
        """設定ダイアログを表示"""
        self._navigator.open_setting_dialog(self._view.get_parent_widget())
