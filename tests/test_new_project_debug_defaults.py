import re
import zipfile
from pathlib import Path

import pytest


class _ArchiveValidateUseCaseStub:
    """提出アーカイブの詳細検証を成功させるテスト用代役。"""

    def execute(self, archive_fullpath: Path) -> bool:
        """テスト用アーカイブを有効として扱う。"""
        return True


class _ProjectCheckExistByNameUseCaseStub:
    """自動生成されたプロジェクト名を未使用として扱うテスト用代役。"""

    def execute(self, project_name: str) -> bool:
        """生成されたプロジェクト名は重複していないものとして扱う。"""
        return False


def test_new_project_widget_applies_debug_defaults(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    """デバッグ設定の3つの入力補助を新規プロジェクト作成結果へ反映する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PyQt5.QtWidgets import QApplication
    from autoprogen.control.widget_new_project import NewProjectWidget

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    archive_fullpath = tmp_path / "report.zip"
    with zipfile.ZipFile(archive_fullpath, "w"):
        pass
    accepted_configs = []
    widget = NewProjectWidget(
        auto_generate_project_name=True,
        initial_report_archive_fullpath=archive_fullpath,
        initial_target_number=4,
        project_check_exist_by_name_usecase=_ProjectCheckExistByNameUseCaseStub(),
        manaba_report_archive_validate_master_excel_exists_usecase=(
            _ArchiveValidateUseCaseStub()
        ),
    )
    widget.accepted.connect(accepted_configs.append)

    widget.show()
    app.processEvents()
    widget._b_create.click()

    assert len(accepted_configs) == 1
    actual = accepted_configs[0]
    assert re.fullmatch(r"proj-\d+", actual.project_name) is not None
    assert actual.manaba_report_archive_fullpath == archive_fullpath
    assert actual.target_number == 4
    widget.close()
    widget.deleteLater()
