from abc import ABC, abstractmethod

from shared.domain.value.identifier import StudentID


# ===== Handler Interfaces (Viewから見たHandlerのインターフェース) =====

class IWorkspaceWindowHandler(ABC):
    """ワークスペースウィンドウViewから見たHandlerのインターフェース"""

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()

    @abstractmethod
    def on_view_closed(self) -> None:
        """Viewが閉じられるときに呼ばれる（クリーンアップ処理）"""
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
# noinspection PyAbstractClass
class IProcessResourceUsageStatusBarView:
    """Handlerから見たリソース使用状況ステータスバーのインターフェース"""

    @abstractmethod
    def set_resource_usage(self, cpu_percent: int, memory_mega_bytes: int, disk_read_count: int,
                           disk_write_count: int) -> None:
        """リソース使用状況を設定"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class IWorkspaceWindowView:
    """Handlerから見たワークスペースウィンドウのインターフェース"""

    @abstractmethod
    def set_window_title(self, title: str) -> None:
        """ウィンドウタイトルを設定"""
        raise NotImplementedError()

    @abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得（ダイアログの親として使用）"""
        raise NotImplementedError()

    @abstractmethod
    def get_process_resource_usage_status_bar_view(self) -> IProcessResourceUsageStatusBarView:
        """リソース使用状況ステータスバーのViewを取得"""
        raise NotImplementedError()
