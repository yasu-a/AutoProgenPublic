from abc import ABC, abstractmethod

from feature.about.usecase.dto import AboutInfo


class IGetAboutInfoUseCase(ABC):
    """About情報取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> AboutInfo:
        raise NotImplementedError()

