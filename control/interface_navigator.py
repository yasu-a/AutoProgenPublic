from abc import ABC, abstractmethod

from PyQt5.QtWidgets import QMainWindow, QWidget

from domain.model.value import ProjectID


class INavigator(ABC):
    @abstractmethod
    def start(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def transition_from_launcher_to_workspace(self, project_id: ProjectID) -> QMainWindow:
        raise NotImplementedError()

    @abstractmethod
    def transition_from_workspace_to_launcher(self, current_window: QMainWindow) -> None:
        raise NotImplementedError()

    @abstractmethod
    def open_setting_dialog(self, parent: QWidget) -> None:
        raise NotImplementedError()

    @abstractmethod
    def open_about_dialog(self, parent: QWidget) -> None:
        raise NotImplementedError()

    @abstractmethod
    def open_score_export_dialog(self, parent: QWidget) -> None:
        raise NotImplementedError()

    @abstractmethod
    def open_scoring_dialog(self, parent: QWidget) -> None:
        raise NotImplementedError()

    @abstractmethod
    def open_testcase_list_edit_dialog(self, parent: QWidget) -> None:
        raise NotImplementedError()
