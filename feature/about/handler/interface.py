from abc import ABC, abstractmethod

from feature.about.usecase.interface import AboutInfoDto


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
# noinspection PyAbstractClass
class IAboutDialogView:
    """Handlerから見たViewのインターフェース"""

    @abstractmethod
    def set_about_info(self, about_info: AboutInfoDto) -> None:
        """About情報を設定"""
        raise NotImplementedError()
