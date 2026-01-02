from abc import ABC, abstractmethod
from abc import abstractmethod as view_abstractmethod
from pathlib import Path
from typing import List, Union

from feature.projman.usecase.dto import NormalProjectSummary, ErrorProjectSummary
from feature.projman.view.dto import NewProjectConfig
from shared.domain.value.identifier import ProjectID


# ===== Handler Interfaces (Viewから見たHandlerのインターフェース) =====

class IProjectOpenDialogHandler(ABC):
    """Dialog Viewから見たHandlerのインターフェース"""

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる（初期タブ決定）"""
        raise NotImplementedError()

    @abstractmethod
    def on_setting_requested(self) -> None:
        """設定ボタンが押されたときに呼ばれる"""
        raise NotImplementedError()


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


class IProjectCreateHandler(ABC):
    """Viewから見たプロジェクト作成Handlerのインターフェース"""

    @abstractmethod
    def on_create_requested(self) -> None:
        """プロジェクト作成要求"""
        raise NotImplementedError()


# ===== View Interfaces (Handlerから見たViewのインターフェース) =====

# Not inheriting from ABC to avoid metaclass conflict with Qt classes
class IProjectOpenDialogView:
    """Handlerから見たDialogのインターフェース"""

    @view_abstractmethod
    def switch_to_create_tab(self) -> None:
        """タブ1（新規作成）に切り替え"""
        raise NotImplementedError()

    @view_abstractmethod
    def switch_to_list_tab(self) -> None:
        """タブ2（一覧）に切り替え"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_result(self) -> NewProjectConfig | ProjectID | None:
        """ダイアログの結果を取得"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_result(self, result: NewProjectConfig | ProjectID) -> None:
        """ダイアログの結果を設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_parent_widget(self):
        """親ウィジェットを取得（QObjectのparent用）"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
class IProjectListView:
    """
    Handlerから見たViewのインターフェース
    HandlerがViewを操作する際に使用
    """

    @view_abstractmethod
    def update_project_list(
            self,
            projects: List[Union[NormalProjectSummary, ErrorProjectSummary]]
    ) -> None:
        """プロジェクトリストを更新"""
        raise NotImplementedError()

    @view_abstractmethod
    def update_project_size(self, project_id: ProjectID, size: int) -> None:
        """特定プロジェクトのサイズを更新"""
        raise NotImplementedError()

    @view_abstractmethod
    def show_delete_confirmation(self, project_id: ProjectID) -> bool:
        """削除確認ダイアログを表示（戻り値: True=削除実行, False=キャンセル）"""
        raise NotImplementedError()

    @view_abstractmethod
    def show_error_message(self, message: str) -> None:
        """エラーメッセージを表示"""
        raise NotImplementedError()

    @view_abstractmethod
    def start_size_loading(self) -> None:
        """サイズ取得の開始（ローディング表示など）"""
        raise NotImplementedError()

    @view_abstractmethod
    def stop_size_loading(self) -> None:
        """サイズ取得の終了"""
        raise NotImplementedError()


# Not inheriting from ABC to avoid metaclass conflict with Qt classes
class IProjectCreateView:
    """Handlerから見たCreate Viewのインターフェース"""

    @view_abstractmethod
    def get_project_name(self) -> str:
        """プロジェクト名を取得"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_target_number(self) -> int:
        """設問番号を取得"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_submission_archive_path(self) -> Path:
        """提出アーカイブのパスを取得"""
        raise NotImplementedError()

    @view_abstractmethod
    def validate_and_get_errors(self) -> List[str]:
        """バリデーション実行（戻り値: エラーリスト、空ならOK）"""
        raise NotImplementedError()

    @view_abstractmethod
    def show_validation_errors(self, errors: List[str]) -> None:
        """バリデーションエラーを表示"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_create_result(self) -> NewProjectConfig | None:
        """作成結果を取得（バリデーション済み）"""
        raise NotImplementedError()

    @view_abstractmethod
    def notify_project_created(self, config: NewProjectConfig) -> None:
        """プロジェクト作成成功を通知（Handlerから呼ばれる）"""
        raise NotImplementedError()
