"""採点ダイアログへ渡す学生一覧と学生移動の契約を検証する。"""

from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import QApplication, QWidget

from autoprogen.control.dialog_mark import MarkDialog, MarkDialogState
from autoprogen.control.navigator import Navigator
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _create_mark_dialog(student_ids: list[StudentID]) -> MarkDialog:
    """学生移動の検証に必要な最小限の依存関係でダイアログを作る。"""
    testcase_list_usecase = Mock()
    testcase_list_usecase.execute.return_value = []
    return MarkDialog(
        student_ids=student_ids,
        global_settings_get_usecase=Mock(),
        testcase_config_list_id_usecase=testcase_list_usecase,
        student_mark_view_data_get_mark_summary_usecase=Mock(),
        student_mark_view_data_get_test_result_usecase=Mock(),
        student_source_code_get_usecase=Mock(),
        student_mark_get_usecase=Mock(),
        student_mark_put_usecase=Mock(),
    )


def test_mark_dialog_rejects_empty_student_list(qt_app: QApplication) -> None:
    """採点対象がない状態でダイアログを直接構築できないことを確認する。"""
    with pytest.raises(ValueError, match="at least one student"):
        _create_mark_dialog([])


def test_single_student_hides_navigation_and_ignores_student_keys(
        qt_app: QApplication,
) -> None:
    """個別採点では学生移動ボタンを隠し、A・Dキーによる移動を行わない。"""
    student_id = StudentID("21D5109047B")
    dialog = _create_mark_dialog([student_id])
    dialog._state = MarkDialogState(student_id=student_id)
    dialog.set_state = Mock()

    assert dialog._w_student_control._b_prev.isHidden()
    assert dialog._w_student_control._b_next.isHidden()
    assert not dialog.states.can_move_between_students()
    assert not dialog.states.can_move_to_prev_student()
    assert not dialog.states.can_move_to_next_student()

    for key in (Qt.Key_A, Qt.Key_D):
        dialog.eventFilter(
            dialog,
            QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier),
        )

    dialog.set_state.assert_not_called()


def test_multiple_students_preserve_order_and_allow_navigation(
        qt_app: QApplication,
) -> None:
    """一括採点では渡された順序を維持し、次の学生へ移動できる。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    supplied = [first, second]
    dialog = _create_mark_dialog(supplied)
    supplied.reverse()
    dialog._state = MarkDialogState(student_id=first)
    dialog.set_state = Mock()

    assert not dialog._w_student_control._b_prev.isHidden()
    assert not dialog._w_student_control._b_next.isHidden()
    assert dialog.states.can_move_between_students()
    assert not dialog.states.can_move_to_prev_student()
    assert dialog.states.can_move_to_next_student()

    dialog.eventFilter(
        dialog,
        QKeyEvent(QEvent.KeyPress, Qt.Key_D, Qt.NoModifier),
    )

    state = dialog.set_state.call_args.args[0]
    assert state.student_id == second

    dialog._state = state
    assert dialog.states.can_move_to_prev_student()
    assert not dialog.states.can_move_to_next_student()


def test_student_switch_and_close_keep_saving_modified_score(
        qt_app: QApplication,
) -> None:
    """学生切替時と画面終了時に変更された点数を従来どおり保存する。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    dialog = _create_mark_dialog([first, second])
    dialog._state = MarkDialogState(student_id=first)
    dialog._MarkDialog__reflect_state = Mock()
    dialog._w_mark_score = Mock()
    dialog._w_mark_score.is_modified.return_value = True
    dialog._w_mark_score.get_data.return_value = StudentMark(first, 50)

    dialog.set_state(MarkDialogState(student_id=second))
    saved = dialog._student_mark_put_usecase.execute.call_args.args[0]
    assert saved.student_id == first
    assert saved.score == 50

    dialog._student_mark_put_usecase.execute.reset_mock()
    dialog._w_mark_score.get_data.return_value = StudentMark(second, 60)
    dialog.closeEvent(QCloseEvent())
    saved = dialog._student_mark_put_usecase.execute.call_args.args[0]
    assert saved.student_id == second
    assert saved.score == 60


def test_navigator_uses_common_launch_path_and_skips_empty_list(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Navigatorが全学生・個別採点を同じ生成処理へ渡し、空一覧を開かない。"""
    from autoprogen.control import dialog_mark

    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    project_container = Mock()
    project_container.student_list_id_usecase.execute.return_value = [second, first]
    app_container = Mock()
    navigator = Navigator(app_container=app_container)
    navigator._current_project_container = project_container
    parent = QWidget()

    dialog = Mock()
    dialog.states.create_state_of_first_student.return_value = MarkDialogState(
        student_id=second,
    )
    dialog_type = Mock(return_value=dialog)
    monkeypatch.setattr(dialog_mark, "MarkDialog", dialog_type)

    navigator.open_scoring_dialog(parent)
    assert dialog_type.call_args.kwargs["student_ids"] == [second, first]
    dialog.states.create_state_of_first_student.assert_called_once_with()
    dialog.exec_.assert_called_once_with()

    dialog_type.reset_mock()
    dialog.reset_mock()
    navigator.open_scoring_dialog_for_student(parent, first)
    assert dialog_type.call_args.kwargs["student_ids"] == [first]

    dialog_type.reset_mock()
    project_container.student_list_id_usecase.execute.return_value = []
    navigator.open_scoring_dialog(parent)
    dialog_type.assert_not_called()
