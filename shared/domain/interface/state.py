from abc import ABC, abstractmethod

from shared.domain.value.identifier import ProjectID


class ICurrentProjectIDState(ABC):
    """
    State: 要素数1のリポジトリのようなもの
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
