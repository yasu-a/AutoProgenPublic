# feature/testcase のHandlerインターフェース
from abc import ABC, abstractmethod
from typing import Any


class ITestCaseConfigEditHandler(ABC):
    """Handlerのインターフェース"""

    @abstractmethod
    def on_run_test_requested(self) -> None:
        """テスト実行が要求されたとき"""
        raise NotImplementedError()


# QtのmetaclassとABCのmetaclassが競合するため、ABCを継承しない（@abstractmethodは残す）
class ITestCaseConfigEditView:
    """Viewのインターフェース - 子ウィジェットへのアクセサを提供"""

    @abstractmethod
    def set_handler(self, handler: ITestCaseConfigEditHandler) -> None:
        """Handlerを注入（DI）"""
        raise NotImplementedError()

    @abstractmethod
    def get_input_files_widget(self) -> Any:
        """入力ファイル編集ウィジェットを取得"""
        raise NotImplementedError()

    @abstractmethod
    def get_execute_options_widget(self) -> Any:
        """実行オプション編集ウィジェットを取得"""
        raise NotImplementedError()

    @abstractmethod
    def get_expected_output_files_widget(self) -> Any:
        """期待出力ファイル編集ウィジェットを取得"""
        raise NotImplementedError()

    @abstractmethod
    def get_test_options_widget(self) -> Any:
        """テストオプション編集ウィジェットを取得"""
        raise NotImplementedError()

    @abstractmethod
    def get_test_tester_widget(self) -> Any:
        """テスト実行ウィジェットを取得"""
        raise NotImplementedError()

    @abstractmethod
    def get_current_expected_file_id(self) -> Any:
        """現在選択されている期待出力ファイルIDを取得"""
        raise NotImplementedError()
