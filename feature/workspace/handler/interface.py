from abc import ABC, abstractmethod
from abc import abstractmethod as view_abstractmethod

from shared.domain.value.identifier import StudentID


# ===== Handler Interfaces (Viewから見たHandlerのインターフェース) =====

class IWorkspaceWindowHandler(ABC):
    """ワークスペースウィンドウViewから見たHandlerのインターフェース"""

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()

    @abstractmethod
    def on_toolbar_action_triggered(self, action_name: str) -> None:
        """ツールバーのアクションがトリガーされたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_student_id_cell_clicked(self, student_id: StudentID) -> None:
        """生徒の学籍番号セルがクリックされたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_mark_result_cell_clicked(self, student_id: StudentID) -> None:
        """生徒の点数セルがクリックされたとき"""
        raise NotImplementedError()


# ===== View Interfaces (Handlerから見たViewのインターフェース) =====

# Not inheriting from ABC to avoid metaclass conflict with Qt classes
class IWorkspaceWindowView:
    """Handlerから見たワークスペースウィンドウのインターフェース"""

    @view_abstractmethod
    def set_window_title(self, title: str) -> None:
        """ウィンドウタイトルを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得（ダイアログの親として使用）"""
        raise NotImplementedError()
