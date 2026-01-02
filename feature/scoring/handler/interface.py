from abc import ABC, abstractmethod
from abc import abstractmethod as view_abstractmethod

from feature.scoring.dto import ScoringDialogState
from feature.scoring.usecase.dto import AbstractStudentTestCaseTestResultViewData
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.value.identifier import TestCaseID, FileID


# ===== Handler Interfaces (Viewから見たHandlerのインターフェース) =====

class IScoringDialogHandler(ABC):
    """採点ダイアログViewから見たHandlerのインターフェース"""

    @abstractmethod
    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        raise NotImplementedError()

    @abstractmethod
    def on_testcase_clicked(self, testcase_id: TestCaseID) -> None:
        """テストケースがクリックされたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_next_testcase_requested(self) -> None:
        """次のテストケースへの移動要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_prev_testcase_requested(self) -> None:
        """前のテストケースへの移動要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_next_student_requested(self) -> None:
        """次の生徒への移動要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_prev_student_requested(self) -> None:
        """前の生徒への移動要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_file_selected(self, file_id: FileID) -> None:
        """ファイルが選択されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_score_changed(self) -> None:
        """点数が変更されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_unmark_requested(self) -> None:
        """点数クリア要求"""
        raise NotImplementedError()

    @abstractmethod
    def on_key_pressed(self, key_code: int) -> None:
        """キーが押されたとき"""
        raise NotImplementedError()

    @abstractmethod
    def on_close_requested(self) -> None:
        """ダイアログが閉じられようとしたとき"""
        raise NotImplementedError()


# ===== View Interfaces (Handlerから見たViewのインターフェース) =====

# Not inheriting from ABC to avoid metaclass conflict with Qt classes
class IScoringDialogView:
    """Handlerから見た採点ダイアログのインターフェース"""

    @view_abstractmethod
    def set_state(self, state: ScoringDialogState) -> None:
        """状態を設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_current_state(self) -> ScoringDialogState:
        """現在の状態を取得"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_student_control_data(self, student_entity) -> None:
        """生徒コントロールのデータを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_testcase_control_data(self, testcase_id: TestCaseID | None) -> None:
        """テストケースコントロールのデータを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_source_code(self, source_code: str | None) -> None:
        """ソースコードを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_test_result_view_data(self, data) -> None:
        """テスト結果表示データを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_test_result_list_data(self, data: list[
                                                  AbstractStudentTestCaseTestResultViewData] | None) -> None:
        """テスト結果リストのデータを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_selected_testcase_id(self, testcase_id: TestCaseID | None) -> None:
        """選択中のテストケースIDを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_selected_file_id(self, file_id: FileID | None) -> None:
        """選択中のファイルIDを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_mark_score_data(self, student_mark: StudentMarkEntity | None) -> None:
        """点数入力のデータを設定"""
        raise NotImplementedError()

    @view_abstractmethod
    def get_mark_score_data(self) -> StudentMarkEntity | None:
        """点数入力のデータを取得"""
        raise NotImplementedError()

    @view_abstractmethod
    def is_mark_score_modified(self) -> bool:
        """点数入力が変更されているか"""
        raise NotImplementedError()

    @view_abstractmethod
    def set_unmarked(self) -> None:
        """点数をクリア"""
        raise NotImplementedError()
