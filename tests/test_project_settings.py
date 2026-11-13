import json
from pathlib import Path
from unittest.mock import Mock

from autoprogen.domain.model.project_settings import (
    ProjectSettings,
    SourceCodeCheckIdentifier,
    SourceCodeCheckSkip,
)
from autoprogen.domain.model.value import ProjectID, StudentID
from autoprogen.infra.io.files.current_project import CurrentProjectCoreIO
from autoprogen.infra.io.files.project import ProjectCoreIO
from autoprogen.infra.path_layout import ProjectPathLayout
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository


def _create_layout(tmp_path: Path, project_name: str) -> ProjectPathLayout:
    """テスト用プロジェクトのパス構成を生成する。"""
    return ProjectPathLayout(
        project_id=ProjectID(project_name),
        root=tmp_path / project_name,
    )


def _create_repository(
        tmp_path: Path,
        project_name: str,
) -> ProjectSettingsRepository:
    """実ファイルを使用するテスト用Repositoryを生成する。"""
    layout = _create_layout(tmp_path, project_name)
    layout.root.mkdir(parents=True, exist_ok=True)
    project_core_io = ProjectCoreIO(project_store_dir=tmp_path)
    return ProjectSettingsRepository(
        project_path_layout=layout,
        current_project_core_io=CurrentProjectCoreIO(
            current_project_id=layout.project_id,
            project_core_io=project_core_io,
        ),
    )


def test_project_settings_survive_json_round_trip() -> None:
    """無効化した規則のグループIDとチェックIDをJSON往復後も維持する。"""
    settings = ProjectSettings(
        disabled_source_code_checks=frozenset({
            SourceCodeCheckIdentifier(group_id="file", check_id="write"),
            SourceCodeCheckIdentifier(group_id="process", check_id="system"),
        }),
        source_code_check_skips=frozenset({
            SourceCodeCheckSkip(
                student_id=StudentID("00A0000000A"),
                source_sha256="a" * 64,
            ),
        }),
    )

    json_body = json.loads(json.dumps(settings.to_json()))
    restored = ProjectSettings.from_json(json_body)

    assert restored == settings


def test_project_settings_adds_source_code_check_skip() -> None:
    """学生とソースコードの組み合わせを既定設定へ追加できることを確認する。"""
    student_id = StudentID("00A0000000A")

    settings = ProjectSettings.create_default().with_source_code_check_skip(
        student_id=student_id,
        source_sha256="a" * 64,
    )

    assert settings.source_code_check_skips == frozenset({
        SourceCodeCheckSkip(
            student_id=student_id,
            source_sha256="a" * 64,
        ),
    })


def test_project_settings_repository_returns_default_when_file_is_missing(
        tmp_path: Path,
) -> None:
    """旧プロジェクトに設定ファイルがない場合は既定設定を返す。"""
    layout = _create_layout(tmp_path, "project-a")
    current_project_core_io = Mock()
    repository = ProjectSettingsRepository(
        project_path_layout=layout,
        current_project_core_io=current_project_core_io,
    )

    settings = repository.get()

    assert settings == ProjectSettings.create_default()
    current_project_core_io.read_json.assert_not_called()


def test_project_settings_repository_keeps_projects_independent(
        tmp_path: Path,
) -> None:
    """異なるプロジェクトの設定がそれぞれのパスへ保存されることを確認する。"""
    repository_a = _create_repository(tmp_path, "project-a")
    repository_b = _create_repository(tmp_path, "project-b")
    settings_a = ProjectSettings(
        disabled_source_code_checks=frozenset({
            SourceCodeCheckIdentifier(group_id="process", check_id="system"),
        }),
        source_code_check_skips=frozenset({
            SourceCodeCheckSkip(
                student_id=StudentID("00A0000000A"),
                source_sha256="a" * 64,
            ),
        }),
    )
    settings_b = ProjectSettings(
        disabled_source_code_checks=frozenset({
            SourceCodeCheckIdentifier(group_id="file", check_id="write"),
        }),
        source_code_check_skips=frozenset({
            SourceCodeCheckSkip(
                student_id=StudentID("00B0000000B"),
                source_sha256="b" * 64,
            ),
        }),
    )

    repository_a.put(settings_a)
    repository_b.put(settings_b)

    assert _create_repository(tmp_path, "project-a").get() == settings_a
    assert _create_repository(tmp_path, "project-b").get() == settings_b
