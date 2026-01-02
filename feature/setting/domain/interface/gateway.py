from abc import ABC, abstractmethod
from pathlib import Path


class IFindCompilerPathGateway(ABC):
    @abstractmethod
    def reset(self) -> None:
        """検索をリセットして最初から検索できるようにする"""
        raise NotImplementedError()

    @abstractmethod
    def search_next(self) -> list[Path]:
        """
        次の100個くらいのファイルを調べて、見つかったらそのリストを返す
        見つからなかったら空のリストを返す
        """
        raise NotImplementedError()

    @abstractmethod
    def has_next(self) -> bool:
        """まだ検索すべきファイルがあるかどうか"""
        raise NotImplementedError()

    @abstractmethod
    def get_current_dir(self) -> Path | None:
        """現在調べているディレクトリを取得（進捗コールバック用）"""
        raise NotImplementedError()

