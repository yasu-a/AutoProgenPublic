"""採点ダイアログへ渡す学生一覧と学生移動の契約を検証する。"""

from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import QApplication, QWidget

from autoprogen.control.dialog_mark import MarkDialog, MarkDialogState
from autoprogen.control.navigator import Navigator
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID, TestCaseID

TestCaseID.__test__ = False


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _create_mark_dialog(
        student_ids: list[StudentID],
        *,
        testcase_ids: list[TestCaseID] | None = None,
) -> MarkDialog:
    """学生移動の検証に必要な最小限の依存関係でダイアログを作る。"""
    testcase_list_usecase = Mock()
    testcase_list_usecase.execute.return_value = testcase_ids or []
    settings_get = Mock()
    settings_get.execute.return_value.bulk_grading_skips = frozenset()
    return MarkDialog(
        student_ids=student_ids,
        global_settings_get_usecase=Mock(),
        testcase_config_list_id_usecase=testcase_list_usecase,
        student_mark_view_data_get_mark_summary_usecase=Mock(),
        student_mark_view_data_get_test_result_usecase=Mock(),
        student_source_code_get_usecase=Mock(),
        student_mark_get_usecase=Mock(),
        student_mark_put_usecase=Mock(),
        project_settings_get_usecase=settings_get,
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


def test_dialog_does_not_apply_mark_state_border(qt_app: QApplication) -> None:
    """採点ダイアログへ点数状態を示す枠線を適用しない。"""
    dialog = _create_mark_dialog([StudentID("21D5109047B")])

    assert dialog.styleSheet() == ""


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
    """Navigatorが一括・個別採点を同じ生成処理へ渡し、空一覧を開かない。"""
    from autoprogen.control import dialog_mark

    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    third = StudentID("25B0000001C")
    project_container = Mock()
    project_container.project_settings_get_usecase.execute.return_value.bulk_grading_skips = (
        frozenset({third})
    )
    project_container.student_mark_list_usecase.execute.return_value = [
        StudentMark(second, 80),
        StudentMark(third, None),
    ]
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
    assert dialog_type.call_args.kwargs["student_ids"] == [second]
    project_container.student_mark_list_usecase.execute.assert_called_once_with()
    project_container.project_settings_get_usecase.execute.assert_called_once_with()
    dialog.states.create_state_of_first_student.assert_called_once_with()
    dialog.exec_.assert_called_once_with()

    dialog_type.reset_mock()
    dialog.reset_mock()
    project_container.student_mark_list_usecase.execute.reset_mock()
    project_container.student_mark_list_usecase.execute.return_value = [
        StudentMark(first, 90),
    ]
    navigator.open_scoring_dialog_for_student(parent, first)
    assert dialog_type.call_args.kwargs["student_ids"] == [first]
    project_container.student_mark_list_usecase.execute.assert_called_once_with(
        student_ids=(first,),
    )

    # 除外中でも個別採点の画面は開ける。
    dialog_type.reset_mock()
    project_container.student_mark_list_usecase.execute.reset_mock()
    project_container.student_mark_list_usecase.execute.return_value = [
        StudentMark(third, None),
    ]
    navigator.open_scoring_dialog_for_student(parent, third)
    assert dialog_type.call_args.kwargs["student_ids"] == [third]
    project_container.student_mark_list_usecase.execute.assert_called_once_with(
        student_ids=(third,),
    )

    # 対象がない場合も、全学生が除外されている場合も起動しない。
    dialog_type.reset_mock()
    project_container.student_mark_list_usecase.execute.return_value = []
    navigator.open_scoring_dialog(parent)
    dialog_type.assert_not_called()

    project_container.student_mark_list_usecase.execute.return_value = [
        StudentMark(third, None),
    ]
    navigator.open_scoring_dialog(parent)
    dialog_type.assert_not_called()


def test_testcase_navigation_uses_ws_and_vertical_arrow_keys(
        qt_app: QApplication,
) -> None:
    """テストケースをW・Sと上下キーで移動し、Q・Eでは移動しない。"""
    student_id = StudentID("21D5109047B")
    first = TestCaseID("テストケース01")
    second = TestCaseID("テストケース02")
    dialog = _create_mark_dialog(
        [student_id],
        testcase_ids=[first, second],
    )
    dialog._state = MarkDialogState(
        student_id=student_id,
        testcase_id=first,
    )
    dialog._student_mark_view_data_get_test_result_usecase.execute.return_value.is_success = False
    dialog.set_state = Mock()

    for key in (Qt.Key_S, Qt.Key_Down):
        dialog.eventFilter(
            dialog,
            QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier),
        )
        state = dialog.set_state.call_args.args[0]
        assert state.testcase_id == second

    dialog._state = MarkDialogState(
        student_id=student_id,
        testcase_id=second,
    )
    for key in (Qt.Key_W, Qt.Key_Up):
        dialog.eventFilter(
            dialog,
            QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier),
        )
        state = dialog.set_state.call_args.args[0]
        assert state.testcase_id == first

    dialog.set_state.reset_mock()
    for key in (Qt.Key_Q, Qt.Key_E):
        dialog.eventFilter(
            dialog,
            QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier),
        )
    dialog.set_state.assert_not_called()


def test_excluded_student_is_read_only_and_returns_to_editable(
        qt_app: QApplication,
) -> None:
    """除外中は灰色・編集不可で、設定解除後は編集と保存ができる。"""
    student_id = StudentID("21D5109047B")
    dialog = _create_mark_dialog([student_id])
    dialog._state = MarkDialogState(student_id=student_id)
    dialog._student_mark_get_usecase.execute.return_value = StudentMark(student_id, 70)
    settings_get = dialog._project_settings_get_usecase
    settings_get.execute.return_value.bulk_grading_skips = frozenset({student_id})

    dialog._update_score_editor()
    assert not dialog._w_mark_score._le_score.isEnabled()
    assert not dialog._w_mark_score._b_unmark.isEnabled()
    assert "#e6e6e6" in dialog._w_mark_score._le_score.styleSheet()
    assert "#a0a0a0" in dialog.styleSheet()
    dialog._w_mark_score.set_unmarked()
    assert dialog._w_mark_score.get_data().score == 70

    # 無効な入力欄をコードから変更しても、保存処理は除外状態を再確認する。
    dialog._w_mark_score._le_score.setText("90")
    dialog.closeEvent(QCloseEvent())
    dialog._student_mark_put_usecase.execute.assert_not_called()

    settings_get.execute.return_value.bulk_grading_skips = frozenset()
    dialog._update_score_editor()
    assert dialog._w_mark_score._le_score.isEnabled()
    assert dialog._w_mark_score._b_unmark.isEnabled()
    assert dialog._w_mark_score._le_score.styleSheet() == ""
    assert dialog.styleSheet() == ""
    dialog._w_mark_score._le_score.setText("80")
    dialog.closeEvent(QCloseEvent())
    saved = dialog._student_mark_put_usecase.execute.call_args.args[0]
    assert saved.student_id == student_id
    assert saved.score == 80
    dialog.close()
