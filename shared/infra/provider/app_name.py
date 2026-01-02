from shared.domain.interface.repository import IAppNameProvider


class StaticAppNameProvider(IAppNameProvider):
    """静的アプリケーション名プロバイダー"""

    def provide(self) -> str:
        """アプリケーション名を提供"""
        return "プロ言採点"
