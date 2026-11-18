from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QDialog

from autoprogen.control.navigator import Navigator
from autoprogen.domain.model.app_version import AppVersion, ReleaseType
from autoprogen.domain.model.global_settings import GlobalSettings


APP_VERSION = AppVersion(
    major=1,
    minor=2,
    release_type=ReleaseType.BETA,
    patch=1,
)


def _make_navigator(
        *,
        agreed_version: AppVersion | None,
) -> tuple[Navigator, Mock, GlobalSettings]:
    """指定した同意状態を持つNavigatorと依存オブジェクトを返す。"""
    settings = GlobalSettings.create_default()
    settings.last_agreed_usage_notice_version = agreed_version

    app_container = Mock()
    app_container.app_version_repository.get.return_value = APP_VERSION
    app_container.global_settings_get_usecase.execute.return_value = settings

    return Navigator(app_container=app_container), app_container, settings


def test_usage_notice_is_not_shown_for_agreed_version(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """現在のバージョンへ同意済みなら確認画面を表示しない。"""
    navigator, app_container, _ = _make_navigator(
        agreed_version=APP_VERSION,
    )
    dialog_constructor = Mock(side_effect=AssertionError("dialog must not open"))
    monkeypatch.setattr(
        "autoprogen.control.dialog_usage_notice.UsageNoticeDialog",
        dialog_constructor,
    )

    assert navigator._confirm_usage_notice_if_required()
    dialog_constructor.assert_not_called()
    app_container.global_settings_put_usecase.execute.assert_not_called()


def test_usage_notice_acceptance_is_saved(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """未同意のバージョンで確認すると全体設定へ保存する。"""
    navigator, app_container, settings = _make_navigator(
        agreed_version=None,
    )
    dialog = Mock()
    dialog.exec_.return_value = QDialog.Accepted
    dialog_constructor = Mock(return_value=dialog)
    monkeypatch.setattr(
        "autoprogen.control.dialog_usage_notice.UsageNoticeDialog",
        dialog_constructor,
    )

    assert navigator._confirm_usage_notice_if_required()

    dialog_constructor.assert_called_once_with(
        app_version_text="1.2-beta.1",
    )
    assert settings.last_agreed_usage_notice_version == APP_VERSION
    app_container.global_settings_put_usecase.execute.assert_called_once_with(settings)


def test_usage_notice_rejection_does_not_save_agreement(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """確認を拒否した場合は同意状態を保存しない。"""
    navigator, app_container, settings = _make_navigator(
        agreed_version=None,
    )
    dialog = Mock()
    dialog.exec_.return_value = QDialog.Rejected
    monkeypatch.setattr(
        "autoprogen.control.dialog_usage_notice.UsageNoticeDialog",
        Mock(return_value=dialog),
    )

    assert not navigator._confirm_usage_notice_if_required()
    assert settings.last_agreed_usage_notice_version is None
    app_container.global_settings_put_usecase.execute.assert_not_called()


def test_existing_project_is_not_opened_when_usage_notice_is_rejected(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """注意事項を拒否した場合は既存プロジェクトを開かない。"""
    navigator, app_container, _ = _make_navigator(agreed_version=None)
    monkeypatch.setattr(
        navigator,
        "_confirm_usage_notice_if_required",
        Mock(return_value=False),
    )

    result = navigator.transition_from_launcher_to_workspace(Mock())

    assert result is None
    app_container.project_open_usecase.execute.assert_not_called()


def test_new_project_is_not_created_when_usage_notice_is_rejected(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """注意事項を拒否した場合は新しいプロジェクトを作成しない。"""
    navigator, app_container, _ = _make_navigator(agreed_version=None)
    monkeypatch.setattr(
        navigator,
        "_confirm_usage_notice_if_required",
        Mock(return_value=False),
    )

    result = navigator._launch_new_project(Mock())

    assert result is None
    app_container.project_create_usecase.execute.assert_not_called()
