"""
Qtアプリケーションのスタイル設定を提供するモジュール
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication, QProxyStyle, QStyle


def _create_custom_style(base_style: str):
    """
    カスタムスタイルクラスを作成
    ツールチップの表示遅延を0にする
    """
    from PyQt5.QtWidgets import QProxyStyle, QStyle
    
    class CustomStyle(QProxyStyle):
        # noinspection PyMethodOverriding
        def styleHint(self, hint, option, widget, return_data):
            if hint == QStyle.SH_ToolTip_WakeUpDelay:
                return 0  # ツールチップの表示遅延を0にする
            return super().styleHint(hint, option, widget, return_data)
    
    return CustomStyle(base_style)


def apply_qt_style(app: "QApplication", *, set_app_info: bool = True) -> None:
    """
    QApplicationにスタイル、フォント、アイコンを適用
    
    Args:
        app: スタイルを適用するQApplicationインスタンス
        set_app_info: Trueの場合、アプリケーション名とバージョンも設定する
    """
    from shared.view.style.icon import get_icon
    from shared.view.style.font import get_font
    
    # スタイルを適用
    app.setStyle(_create_custom_style("Fusion"))
    
    # フォントを適用
    # noinspection PyArgumentList
    app.setFont(get_font())
    
    # アイコンを適用
    app.setWindowIcon(get_icon("app"))
    
    # アプリケーション情報を設定（オプション）
    if set_app_info:
        from app.di.provider import get_app_name_provider, get_app_version_provider
        app.setApplicationName(get_app_name_provider().provide())
        app.setApplicationVersion(str(get_app_version_provider().provide()))

