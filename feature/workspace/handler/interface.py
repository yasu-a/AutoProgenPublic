from abc import ABC, abstractmethod
from dataclasses import dataclass

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


class IStudentTableHandler(ABC):
    @abstractmethod
    def on_view_initialized(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def on_view_closed(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def on_student_id_clicked(self, student_id: StudentID):
        raise NotImplementedError()

    @abstractmethod
    def on_sore_clicked(self, student_id: StudentID):
        raise NotImplementedError()


@dataclass(slots=True)
class StudentTableRowViewModel:
    """
    テーブルの1行分のデータを表すViewModel
    ドメインロジックは持たず、表示に必要なプリミティブな情報のみを持つ
    """
    student_id: StudentID
    has_submission: bool  # 提出ファイルがあるかどうか（設問の提出コードがあるかどうかはわからない）
    name: str  # 名前
    build_stage_status: str
    compile_stage_status: str
    execute_stage_status_lst: list[str]
    test_stage_status_lst: list[str]
    error_summary: str | None  # エラー概要テキスト (Noneならエラーなし)
    error_detailed_text: str | None  # エラー詳細テキスト (Noneならエラーなし)
    score: str  # 点数テキスト (例: "90", "未採点")


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class IStudentTableView:
    @abstractmethod
    def set_handler(self, handler: IStudentTableHandler) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update_table_data(self, view_models: list[StudentTableRowViewModel]):
        raise NotImplementedError()

    @abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得（QObjectのparent用）"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class IWorkspaceWindowView:
    """Handlerから見たワークスペースウィンドウのインターフェース"""

    @abstractmethod
    def add_table(self, table_view: IStudentTableView) -> None:
        raise NotImplementedError()

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
