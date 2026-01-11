from abc import ABC, abstractmethod

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget

from feature.projman.usecase.interface import NewProjectConfigDto, AbstractProjectSummary
from shared.domain.value.identifier import ProjectID


# ===== Project Create Interfaces =====

class IProjectCreateHandler(ABC):
    """Viewから見たプロジェクト作成Handlerのインターフェース"""

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()

    @abstractmethod
    def on_create_requested(self) -> None:
        """プロジェクト作成要求"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class IProjectCreateView:
    """Handlerから見たCreate Viewのインターフェース"""

    @abstractmethod
    def get_project_name(self) -> str:
        """プロジェクト名を取得"""
        raise NotImplementedError()

    @abstractmethod
    def set_project_name(self, name: str) -> None:
        """プロジェクト名を設定"""
        raise NotImplementedError()

    @abstractmethod
    def get_target_number(self) -> str:
        """設問番号を取得"""
        raise NotImplementedError()

    @abstractmethod
    def set_target_number(self, number: str) -> None:
        """設問番号を設定"""
        raise NotImplementedError()

    @abstractmethod
    def get_submission_archive_path(self) -> str:
        """提出アーカイブのパスを取得"""
        raise NotImplementedError()

    @abstractmethod
    def set_submission_archive_path(self, path: str) -> None:
        """提出アーカイブのパスを設定"""
        raise NotImplementedError()

    @abstractmethod
    def show_validation_errors(self, errors: list[str]) -> None:
        """バリデーションエラーを表示"""
        raise NotImplementedError()

    @abstractmethod
    def notify_project_created(self, config: NewProjectConfigDto) -> None:
        """プロジェクト作成成功を通知（Handlerから呼ばれる）"""
        raise NotImplementedError()

    @abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得（QObjectのparent用）"""
        raise NotImplementedError()

    @abstractmethod
    def show_initialize_error(self, message: str):
        """初期化失敗のエラーダイアログを表示する"""
        raise NotImplementedError()


# ===== Project List Interfaces =====

class IProjectListHandler(ABC):
    """
    Viewから見たHandlerのインターフェース
    ViewがユーザーアクションをHandlerに伝える際に使用
    """

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる（showEventから）"""
        raise NotImplementedError()

    @abstractmethod
    def on_open_project_requested(self, project_id: ProjectID) -> None:
        """プロジェクトを開く要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_open_folder_requested(self, project_id: ProjectID) -> None:
        """プロジェクトフォルダを開く要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_delete_project_requested(self, project_id: ProjectID) -> None:
        """プロジェクト削除要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_open_base_folder_requested(self) -> None:
        """プロジェクト管理フォルダを開く要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_refresh_requested(self) -> None:
        """プロジェクトリストの再読み込み要求"""
        raise NotImplementedError()

    @abstractmethod
    def set_size_queue(self, project_ids: list[ProjectID]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop_size_loading(self) -> None:
        """サイズ取得Workerを停止（ViewのhideEventから呼ばれる）"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class IProjectListView:
    """
    Handlerから見たViewのインターフェース
    HandlerがViewを操作する際に使用
    """

    @abstractmethod
    def update_project_list(
            self,
            projects: list[AbstractProjectSummary],
    ) -> None:
        """プロジェクトリストを更新"""
        raise NotImplementedError()

    @abstractmethod
    def update_project_size(self, project_id: ProjectID, size: int) -> None:
        """特定プロジェクトのサイズを更新"""
        raise NotImplementedError()

    @abstractmethod
    def show_delete_confirmation(self, project_id: ProjectID) -> bool:
        """削除確認ダイアログを表示（戻り値: True=削除実行, False=キャンセル）"""
        raise NotImplementedError()

    @abstractmethod
    def show_error_message(self, message: str) -> None:
        """エラーメッセージを表示"""
        raise NotImplementedError()

    @abstractmethod
    def start_size_loading(self) -> None:
        """サイズ取得の開始（ローディング表示など）"""
        raise NotImplementedError()

    @abstractmethod
    def stop_size_loading(self) -> None:
        """サイズ取得の終了"""
        raise NotImplementedError()

    @abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得（QObjectのparent用）"""
        raise NotImplementedError()


# ===== Launcher Interfaces =====

class IProjectLauncherHandler(ABC):
    """Launcher Viewから見たHandlerのインターフェース"""

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()

    @abstractmethod
    def on_setting_requested(self) -> None:
        """設定ボタンが押されたときに呼ばれる"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
# noinspection PyAbstractClass
class IProjectLauncherView:
    """Handlerから見たLauncherのインターフェース"""

    @abstractmethod
    def add_tab(self, widget: QWidget, title: str, icon: QIcon = None) -> None:
        """タブを追加（Navigatorからの構成用）"""
        raise NotImplementedError()

    @abstractmethod
    def switch_to_create_tab(self) -> None:
        """タブ1（新規作成）に切り替え"""
        raise NotImplementedError()

    @abstractmethod
    def switch_to_list_tab(self) -> None:
        """タブ2（一覧）に切り替え"""
        raise NotImplementedError()

    @abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得"""
        raise NotImplementedError()
