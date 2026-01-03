from abc import ABC, abstractmethod
from dataclasses import dataclass


# DTOはinterfaceの直上に定義
@dataclass(frozen=True)
class AboutInfoDto:
    """About情報取得UseCaseの結果を表すDTO"""
    app_name: str
    version_text: str  # 例: "1.1-beta.2" または "1.1.2"
    repo_url: str
    icon_credit_url: str


class IGetAboutInfoUseCase(ABC):
    """About情報取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> AboutInfoDto:
        raise NotImplementedError()

