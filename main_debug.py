from PyQt5.QtWidgets import *

from app_logging import create_logger
from controls.dialog_welcome import WelcomeDialog
from controls.window_main import MainWindow
from fonts import font
from models.errors import ProjectCreateServiceError
from models.new_project_config import NewProjectConfig
from models.values import ProjectName
from service_provider import set_debug, set_project_name, get_project_construction_service

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

if __name__ == '__main__':
    set_debug(True)

    app = QApplication(sys.argv)
    # noinspection PyArgumentList
    app.setFont(font())
    app.setStyle('Fusion')

    welcome = WelcomeDialog()
    if welcome.exec_() == QDialog.Accepted:
        result = welcome.get_result()
        if isinstance(result, ProjectName):
            project_name: ProjectName = result
            set_project_name(project_name)
        elif isinstance(result, NewProjectConfig):
            new_project_config: NewProjectConfig = result
            set_project_name(new_project_config.project_name)
            try:
                get_project_construction_service(
                    manaba_report_archive_fullpath=new_project_config.manaba_report_archive_fullpath,
                ).create_project(
                    target_id=new_project_config.target_id,
                )
            except ProjectCreateServiceError as e:
                logger.exception("Failed to create project due to error")
                # noinspection PyTypeChecker
                QMessageBox.critical(
                    None,
                    "プロジェクトの作成",
                    f"プロジェクトの作成に失敗ました。\n{e.reason}",
                )
                sys.exit(1)
        else:
            assert False, result
        window = MainWindow()
        # noinspection PyUnresolvedReferences
        window.show()
        app.exec()

    # app = QApplication(sys.argv)
    # # noinspection PyArgumentList
    # app.setFont(font())
    # app.setStyle('Fusion')
    #
    # state.setup_project(
    #     "C:/Users/yasuh/OneDrive/デスクトップ/rep",
    #     app,
    # )
    # window = MainWindow()
    # # noinspection PyUnresolvedReferences
    # window.show()
    # app.exec()
