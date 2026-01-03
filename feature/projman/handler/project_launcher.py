from feature.projman.handler.interface import IProjectLauncherHandler, IProjectLauncherView
from feature.projman.usecase.interface import IProjectListRecentSummaryUseCase
from shared.handler.interface import INavigator


class ProjectLauncherHandler(IProjectLauncherHandler):
    """
    ProjectLauncherDialog専任のHandler
    責務: 初期表示時のタブ制御、設定画面への遷移
    """

    def __init__(
            self,
            *,
            view: IProjectLauncherView,
            navigator: INavigator,
            project_list_usecase: IProjectListRecentSummaryUseCase,
    ):
        self._view = view
        self._navigator = navigator
        self._project_list_usecase = project_list_usecase

    def on_view_initialized(self) -> None:
        """
        初期化時の処理
        プロジェクトが一つもなければ「新規作成」タブ、あれば「一覧」タブを表示
        """
        projects = self._project_list_usecase.execute()
        if projects:
            self._view.switch_to_list_tab()
        else:
            self._view.switch_to_create_tab()

    def on_setting_requested(self) -> None:
        """設定ダイアログを開く"""
        self._navigator.open_setting_dialog(self._view.get_parent_widget())
