from feature.about.usecase.interface import IGetAboutInfoUseCase, AboutInfoDto
from shared.domain.interface.repository import IAppNameProvider, IAppVersionProvider


class GetAboutInfoUseCase(IGetAboutInfoUseCase):
    """About画面用の情報を取得するUseCase"""

    def __init__(
            self,
            *,
            name_provider: IAppNameProvider,
            version_provider: IAppVersionProvider,
    ):
        self._name_provider = name_provider
        self._version_provider = version_provider

    def execute(self) -> AboutInfoDto:
        """About情報を取得"""
        app_name = self._name_provider.provide()
        app_version = self._version_provider.provide()
        version_text = str(app_version)

        return AboutInfoDto(
            app_name=app_name,
            version_text=version_text,
            repo_url="https://github.com/yasu-a/AutoProgenPublic",
            icon_credit_url="https://icooon-mono.com",
        )
