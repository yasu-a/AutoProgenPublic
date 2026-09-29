import pytest


def test_qapplication_can_start_and_stop_offscreen(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """QApplicationを画面なしで生成し、正常に終了できることを確認する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    app.processEvents()
    assert QApplication.instance() is app
    app.quit()
