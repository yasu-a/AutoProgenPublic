from abc import ABC, abstractmethod

from shared.domain.value.app_version import AppVersion


class IAppNameProvider(ABC):
    """アプリケーション名を提供するインターフェース"""

    @abstractmethod
    def provide(self) -> str:
        """アプリケーション名を提供"""
        raise NotImplementedError()


class IAppVersionProvider(ABC):
    """アプリケーションバージョンを提供するインターフェース"""

    @abstractmethod
    def provide(self) -> AppVersion:
        """アプリケーションバージョンを提供"""
        raise NotImplementedError()
