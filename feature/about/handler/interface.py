from abc import ABC, abstractmethod
from abc import abstractmethod as view_abstractmethod

from feature.about.usecase.dto import AboutInfo


class IAboutDialogHandler(ABC):
    """Viewから見たHandlerのインターフェース"""

    @abstractmethod
    def set_view(self, view: "IAboutDialogView") -> None:
        """Viewを設定（循環参照を避けるため、View生成後に呼ぶ）"""
        raise NotImplementedError()

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()


# QtのmetaclassとABCのmetaclassが競合するため、ABCを継承しない
class IAboutDialogView:
    """Handlerから見たViewのインターフェース"""

    @view_abstractmethod
    def set_about_info(self, about_info: AboutInfo) -> None:
        """About情報を設定"""
        raise NotImplementedError()
