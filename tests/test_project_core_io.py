from pathlib import Path

import pytest

from autoprogen.domain.error import CoreIOError
from autoprogen.domain.model.value import ProjectID
from autoprogen.infra.io.files.project import ProjectCoreIO


def _create_project_core_io(tmp_path: Path) -> tuple[ProjectCoreIO, ProjectID, Path]:
    """テスト用プロジェクトとファイルIOを作成する。"""
    project_id = ProjectID("test-project")
    project_root = tmp_path / str(project_id)
    project_root.mkdir()
    return ProjectCoreIO(project_store_dir=tmp_path), project_id, project_root


def test_missing_folder_has_same_checksum_as_empty_folder(tmp_path: Path) -> None:
    """存在しないフォルダを空フォルダと同じ状態として扱う。"""
    project_core_io, project_id, project_root = _create_project_core_io(tmp_path)
    empty_folder = project_root / "empty"
    empty_folder.mkdir()

    missing_checksum = project_core_io.calculate_folder_checksum(
        project_id=project_id,
        folder_fullpath=project_root / "missing",
    )
    empty_checksum = project_core_io.calculate_folder_checksum(
        project_id=project_id,
        folder_fullpath=empty_folder,
    )

    assert missing_checksum == empty_checksum


def test_folder_checksum_rejects_file_path(tmp_path: Path) -> None:
    """フォルダの代わりにファイルが指定された場合は拒否する。"""
    project_core_io, project_id, project_root = _create_project_core_io(tmp_path)
    file_path = project_root / "submission.txt"
    file_path.write_text("test", encoding="utf-8")

    with pytest.raises(CoreIOError, match="path must be a directory"):
        project_core_io.calculate_folder_checksum(
            project_id=project_id,
            folder_fullpath=file_path,
        )
