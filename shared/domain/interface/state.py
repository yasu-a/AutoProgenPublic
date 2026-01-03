from abc import ABC, abstractmethod

from shared.domain.value.identifier import ProjectID


class ICurrentProjectIDState(ABC):
    """
    現在開かれているプロジェクトIDを管理するインターフェース
    """

    @abstractmethod
    def get(self) -> ProjectID | None:
        """現在のプロジェクトIDを取得"""
        raise NotImplementedError()

    @abstractmethod
    def update(self, project_id: ProjectID) -> None:
        """現在のプロジェクトIDを更新"""
        raise NotImplementedError()


class IDebugModeState(ABC):
    """
    現在アプリがデバッグモードで開かれているかどうかを管理するinterface
    """

    @abstractmethod
    def get(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def update(self, is_debug_mode: bool) -> None:
        raise NotImplementedError()
