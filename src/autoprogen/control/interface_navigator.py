from abc import ABC, abstractmethod

from PyQt5.QtWidgets import QMainWindow, QWidget

from autoprogen.domain.model.value import ProjectID, StudentID


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
    def open_project_settings_dialog(self, parent: QWidget) -> None:
        """現在のプロジェクト専用の設定画面を開く。"""
        raise NotImplementedError()

    @abstractmethod
    def open_student_error_detail_dialog(self, parent: QWidget, student_id: StudentID) -> None:
        """学生のエラー詳細を閲覧用ダイアログで表示する。"""
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
    def open_scoring_dialog_for_student(self, parent: QWidget, student_id: StudentID) -> None:
        raise NotImplementedError()

    @abstractmethod
    def open_testcase_list_edit_dialog(self, parent: QWidget) -> bool:
        """編集画面を開き、テストケースに変更があったかを返す。"""
        raise NotImplementedError()
