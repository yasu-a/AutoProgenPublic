import os
from typing import TYPE_CHECKING

from utils import app_logging
from utils.app_logging import create_logger

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication
    from controls.window_main import MainWindow
    from domain.models.values import ProjectID
    from controls.dto.new_project_config import NewProjectConfig

if __name__ == '__main__':
    import sys

    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        # noinspection PyProtectedMember
        sys._excepthook(exctype, value, traceback)  # type: ignore
        sys.exit(1)


    sys.excepthook = exception_hook

_logger = create_logger()


def create_app() -> "QApplication":
    from PyQt5.QtWidgets import QApplication, QProxyStyle, QStyle
    from application.dependency.usecases import get_app_version_get_text_usecase
    from res.icons import get_icon
    from res.fonts import get_font

    class CustomStyle(QProxyStyle):
        # noinspection PyMethodOverriding
        def styleHint(self, hint, option, widget, return_data):
            if hint == QStyle.SH_ToolTip_WakeUpDelay:
                return 0  # ツールチップの表示遅延を0にする
            return super().styleHint(hint, option, widget, return_data)

    app = QApplication(sys.argv)
    app.setApplicationName("プロ言採点")
    app.setApplicationVersion(get_app_version_get_text_usecase().execute())
    app.setWindowIcon(get_icon("app"))
    # noinspection PyArgumentList
    app.setFont(get_font())
    app.setStyle(CustomStyle("Fusion"))

    return app


def launch_existing_project(project_id: "ProjectID") -> "MainWindow":
    from application.dependency.usecases import get_project_open_usecase
    from controls.window_main import MainWindow

    # 現在のプロジェクトを設定
    get_project_open_usecase().execute(project_id)
    # メインウィンドウを開く
    window = MainWindow()
    # noinspection PyUnresolvedReferences
    window.show()

    return window


def launch_new_project(new_project_config: "NewProjectConfig") -> "MainWindow":
    from application.dependency.usecases import get_project_create_usecase
    from application.dependency.usecases import get_project_open_usecase
    from controls.dialog_project_initialize import ProjectInitializeProgressDialog
    from controls.window_main import MainWindow
    from PyQt5.QtWidgets import QDialog, QMessageBox

    # 新規にプロジェクトを生成

    project_id = get_project_create_usecase().execute(
        project_name=new_project_config.project_name,
        target_number=new_project_config.target_number,
        zip_name=new_project_config.manaba_report_archive_fullpath.name,
    )
    # 現在のプロジェクトを設定
    get_project_open_usecase().execute(project_id)
    # 現在のプロジェクトを初期化
    dialog = ProjectInitializeProgressDialog(
        manaba_report_archive_fullpath=new_project_config.manaba_report_archive_fullpath,
    )
    if dialog.exec_() != QDialog.Accepted:
        QMessageBox.critical(
            dialog,
            "プロジェクトの初期化",
            dialog.get_error_object().message,
            QMessageBox.Ok,
        )
        sys.exit(1)

    # メインウィンドウを開く
    window = MainWindow()
    # noinspection PyUnresolvedReferences
    window.show()

    return window


def main():
    from application.state.debug import set_debug
    from controls.dialog_welcome import WelcomeDialog
    from PyQt5.QtWidgets import QDialog
    from domain.models.values import ProjectID
    from controls.dto.new_project_config import NewProjectConfig

    # 環境変数からデバッグ用の構成を用意
    app_logging.set_level(app_logging.INFO)
    if os.getenv("APP_DEBUG"):
        set_debug(True)
        _logger.info("STARTING WITH DEBUG MODE")
        if os.getenv("APP_VERBOSE_LOG"):
            app_logging.set_level(app_logging.DEBUG)
            _logger.info("VERBOSE LOG ENABLED")

    # QApplicationを生成
    app = create_app()
    # ウェルカムダイアログを表示
    welcome = WelcomeDialog()
    res = welcome.exec_()
    # ウェルカムダイアログの応答によって処理を分ける
    if res == QDialog.Accepted:  # 応答がacceptedなら
        result = welcome.get_data()  # 応答結果を取得
        del welcome  # ウェルカムダイアログを解放
        if isinstance(result, ProjectID):  # 既存のプロジェクトIDなら
            # 既存のプロジェクトを起動
            project_id: ProjectID = result
            window = launch_existing_project(project_id)
        elif isinstance(result, NewProjectConfig):  # 新規プロジェクトの構成なら
            # 新規プロジェクトを起動
            new_project_config: NewProjectConfig = result
            window = launch_new_project(new_project_config)
        else:
            # それ以外はあり得ない
            assert False, result
        # Qtのイベントループに入る
        _ = window  # C++に解放されないようにインスタンスを保つ
        sys.exit(app.exec_())
    else:  # 応答がキャンセルなら
        pass  # 何もしない


if __name__ == '__main__':
    main()
