from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QToolButton

from autoprogen.control.widget_student_table_control import StudentTableControlWidget
from autoprogen.control.window_main import MainWindow
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


def test_control_actions_share_icons_signals_and_selection_state(
        qt_app: QApplication,
) -> None:
    """操作Actionがアイコンと選択状態に応じた有効状態を持つ。"""
    widget = StudentTableControlWidget()
    actions = widget.context_actions()
    requested: list[str] = []
    widget.open_folder_requested.connect(lambda: requested.append("folder"))
    widget.open_scoring_requested.connect(lambda: requested.append("scoring"))
    widget.clear_mark_requested.connect(lambda: requested.append("clear"))

    assert all(not action.isEnabled() for action in actions)
    assert all(not action.icon().isNull() for action in actions)
    assert actions[0].text() == "展開された提出ファイルを編集"
    assert all(
        button.toolButtonStyle() == Qt.ToolButtonIconOnly
        for button in widget.findChildren(QToolButton)
    )

    widget.set_selection_state(
        selected=True,
        marked=False,
        has_submission=False,
    )
    assert not actions[0].isEnabled()
    assert actions[1].isEnabled()
    assert not actions[2].isEnabled()

    widget.set_selection_state(
        selected=True,
        marked=True,
        has_submission=True,
    )
    for action in actions:
        action.trigger()

    assert requested == ["folder", "scoring", "clear"]


def test_selection_updates_controls_and_error_detail(qt_app: QApplication) -> None:
    """行選択時に操作可否と下部のエラー詳細を同じ学生へ同期する。"""
    student_id = StudentID("21D5109047B")
    window = Mock()
    window._MainWindow__selected_student_id = Mock(return_value=student_id)
    window._MainWindow__show_student_error_detail = Mock()
    window._facade.get_student_mark.return_value = (
        StudentMark(student_id, 80, confirmed=False)
    )
    window._w_student_table.selected_student_has_submission.return_value = True

    MainWindow._MainWindow__w_student_table_selection_changed(window)

    window._w_student_table_control.set_selection_state.assert_called_once_with(
        selected=True,
        marked=True,
        has_submission=True,
    )
    window._MainWindow__show_student_error_detail.assert_called_once_with(student_id)


def test_clear_mark_action_clears_score_and_confirmation(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """確認後の点数クリアを選択学生のFacade処理へ委譲する。"""
    student_id = StudentID("21D5109047B")
    window = Mock()
    window._MainWindow__selected_student_id = Mock(return_value=student_id)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        Mock(return_value=QMessageBox.Yes),
    )

    MainWindow._MainWindow__selected_student_mark_clear_requested(window)

    window._facade.clear_student_mark.assert_called_once_with(student_id)


def test_context_menu_uses_same_actions_as_control_buttons(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """右クリックした行を選択し、操作欄と同じActionをメニューへ表示する。"""
    actions = (Mock(), Mock(), Mock())
    shown: dict[str, object] = {}

    class MenuStub:
        """コンテキストメニューへ渡されたActionと位置を記録する。"""

        def __init__(self, parent) -> None:
            """メニューの親を記録する。"""
            shown["parent"] = parent

        def addActions(self, actual_actions) -> None:
            """追加されたActionを記録する。"""
            shown["actions"] = tuple(actual_actions)

        def exec_(self, position) -> None:
            """メニューの表示位置を記録する。"""
            shown["position"] = position

    monkeypatch.setattr("autoprogen.control.window_main.QMenu", MenuStub)
    window = Mock()
    window._w_student_table.select_row_at.return_value = True
    window._w_student_table_control.context_actions.return_value = actions
    position = QPoint(10, 20)
    global_position = QPoint(30, 40)
    window._w_student_table.viewport().mapToGlobal.return_value = global_position

    MainWindow._MainWindow__w_student_table_context_menu_requested(
        window,
        position,
    )

    window._w_student_table.select_row_at.assert_called_once_with(position)
    assert shown["actions"] == actions
    assert shown["position"] == global_position


def test_student_without_errors_hides_detail_dock(qt_app: QApplication) -> None:
    """選択学生にエラーがない場合は以前のエラー詳細を閉じる。"""
    student_id = StudentID("21D5109047B")
    window = Mock()
    window._navigator.create_student_error_detail_widget.return_value = None

    MainWindow._MainWindow__show_student_error_detail(window, student_id)

    window._student_error_dock.hide.assert_called_once_with()
