from PyQt5.QtWidgets import *

from app_logging import create_logger
from application.dependency.usecases import get_project_create_usecase
from application.state.current_project import set_current_project_id
from application.state.debug import set_debug
from controls.dialog_static_initialize import StaticInitializeProgressDialog
from controls.dialog_welcome import WelcomeDialog
# from controls.window_main import MainWindow
from domain.models.values import ProjectID
from dto.new_project_config import NewProjectConfig
from fonts import font

if __name__ == '__main__':
    import sys

    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        # noinspection PyProtectedMember
        sys._excepthook(exctype, value, traceback)  # type: ignore
        sys.exit(1)


    sys.excepthook = exception_hook

logger = create_logger()


def create_app() -> QApplication:
    class CustomStyle(QProxyStyle):
        # noinspection PyMethodOverriding
        def styleHint(self, hint, option, widget, return_data):
            if hint == QStyle.SH_ToolTip_WakeUpDelay:
                return 0  # ツールチップの表示遅延を0にする
            return super().styleHint(hint, option, widget, return_data)

    app = QApplication(sys.argv)
    # noinspection PyArgumentList
    app.setFont(font())
    app.setStyle(CustomStyle("Fusion"))

    return app


def launch_existing_project(project_id: ProjectID) -> None:
    # 現在のプロジェクトを設定
    set_current_project_id(project_id)
    # # メインウィンドウを開く
    # window = MainWindow()
    # # noinspection PyUnresolvedReferences
    # window.show()


def launch_new_project(new_project_config: NewProjectConfig) -> None:
    # 新規にプロジェクトを生成
    project_id = get_project_create_usecase().execute(
        project_name=new_project_config.project_name,
        target_number=new_project_config.target_number,
    )
    # 現在のプロジェクトを設定
    set_current_project_id(project_id)
    # 現在のプロジェクトを初期化
    StaticInitializeProgressDialog(
        manaba_report_archive_fullpath=new_project_config.manaba_report_archive_fullpath,
    ).exec_()
    # # メインウィンドウを開く
    # window = MainWindow()
    # # noinspection PyUnresolvedReferences
    # window.show()


def main():
    set_debug(True)

    # QApplicationを生成
    app = create_app()
    # ウェルカムダイアログを表示
    welcome = WelcomeDialog()
    res = welcome.exec_()
    # ウェルカムダイアログの応答によって処理を分ける
    if res == QDialog.Accepted:  # 応答がacceptedなら
        result = welcome.get_data()  # 応答結果を取得
        if isinstance(result, ProjectID):  # 既存のプロジェクトIDなら
            # 既存のプロジェクトを起動
            project_id: ProjectID = result
            launch_existing_project(project_id)
        elif isinstance(result, NewProjectConfig):  # 新規プロジェクトの構成なら
            # 新規プロジェクトを起動
            new_project_config: NewProjectConfig = result
            launch_new_project(new_project_config)
        else:
            # それ以外はあり得ない
            assert False, result
    else:  # 応答がキャンセルなら
        # 何もしない
        pass
    # Qtのイベントループに入る
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
