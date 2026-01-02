from feature.projman.handler.interface import IProjectOpenDialogView, IProjectOpenDialogHandler
from feature.projman.usecase.interface import IProjectListRecentSummaryUseCase


class ProjectOpenDialogHandler(IProjectOpenDialogHandler):
    """
    Container Dialog専任のHandler
    責務: ダイアログ表示時の初期タブ決定のみ
    """

    def __init__(
            self,
            *,
            view: IProjectOpenDialogView,
            project_list_usecase: IProjectListRecentSummaryUseCase,
    ):
        self._view = view
        self._project_list_usecase = project_list_usecase

    def on_view_initialized(self) -> None:
        """プロジェクト存在チェック → タブ切り替え"""
        projects = self._project_list_usecase.execute()
        if projects:  # プロジェクトあり
            self._view.switch_to_list_tab()
        else:  # プロジェクトなし
            self._view.switch_to_create_tab()
        # 注意: ここでは子Viewのロード処理は呼ばない（独立性の原則）
