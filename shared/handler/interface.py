from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from shared.domain.value.identifier import ProjectID, TargetID

if TYPE_CHECKING:
    from shared.domain.value.identifier import StudentID


class INavigator(ABC):
    """
    画面遷移を管理するNavigatorのインターフェース
    Handlerが画面遷移を依頼する際に使用
    """

    @abstractmethod
    def start(self) -> None:
        """
        アプリ起動時に呼ばれるメソッド
        最初の画面へ遷移させる
        """
        raise NotImplementedError()

    @abstractmethod
    def navigate_to_main_window(self, project_id: ProjectID) -> None:
        """
        メインウィンドウへ遷移する
        project_idで指定されたプロジェクトを開いてメインウィンドウを表示
        """
        raise NotImplementedError()

    @abstractmethod
    def open_compiler_search_dialog(self, parent) -> Path | None:
        """
        コンパイラ検索ダイアログを開く
        戻り値: 選択されたパス、キャンセル時はNone
        """
        raise NotImplementedError()

    @abstractmethod
    def open_setting_dialog(self, parent) -> None:
        """設定ダイアログを開く"""
        raise NotImplementedError()

    @abstractmethod
    def open_about_dialog(self, parent) -> None:
        """Aboutダイアログを開く"""
        raise NotImplementedError()

    @abstractmethod
    def open_score_export_dialog(self, parent, target_id: TargetID) -> None:
        """点数エクスポートダイアログを開く"""
        raise NotImplementedError()

    @abstractmethod
    def open_scoring_dialog(self, parent) -> None:
        """採点ダイアログを開く（最初の生徒）"""
        raise NotImplementedError()

    @abstractmethod
    def open_scoring_dialog_with_student(self, parent, student_id: "StudentID") -> None:
        """採点ダイアログを開く（指定された生徒）"""
        raise NotImplementedError()

    @abstractmethod
    def open_testcase_list_edit_dialog(self, parent) -> None:
        """テストケース編集ダイアログを開く"""
        raise NotImplementedError()
