from feature.about.handler.interface import IAboutDialogHandler, IAboutDialogView
from feature.about.usecase.get_about_info import GetAboutInfoUseCase


class AboutDialogHandler(IAboutDialogHandler):
    """
    AboutDialog専任のHandler
    責務: AboutDialogの初期化処理（AboutInfoを取得してViewに設定）
    """

    def __init__(
            self,
            *,
            view: IAboutDialogView | None,
            get_about_info_usecase: GetAboutInfoUseCase,
    ):
        self._view: IAboutDialogView | None = view
        self._get_about_info_usecase = get_about_info_usecase

    def set_view(self, view: IAboutDialogView) -> None:
        self._view = view

    # ===== IAboutDialogHandler実装 =====
    def on_view_initialized(self) -> None:
        """View初期化時に呼ばれる"""
        # AboutInfoを取得してViewに設定
        about_info = self._get_about_info_usecase.execute()
        self._view.set_about_info(about_info)
