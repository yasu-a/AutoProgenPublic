from unittest.mock import Mock

import pytest

from autoprogen.domain.model.project_settings import (
    ProjectSettings,
    SourceCodeCheckIdentifier,
    SourceCodeCheckSkip,
)
from autoprogen.domain.model.source_code_check import (
    SourceCodeCheckCatalog,
    SourceCodeCheckEntry,
    SourceCodeCheckGroup,
    SourceCodeCheckMatchType,
)
from autoprogen.domain.model.value import ProjectID, StudentID
from autoprogen.service.student_security_settings_hash import StudentSecuritySettingsHashService


STUDENT = StudentID("20A1234567B")
OTHER_STUDENT = StudentID("20B1234567C")
SOURCE_SHA_A = "a" * 64
SOURCE_SHA_B = "b" * 64


def _entry(
        check_id: str,
        *,
        target_strings: tuple[str, ...],
        match_type: SourceCodeCheckMatchType = SourceCodeCheckMatchType.FUNCTION_CALL,
        name: str = "表示名",
        description: str = "表示用の説明文です。",
) -> SourceCodeCheckEntry:
    """検査内容と表示内容を個別に変更できるテスト規則を作る。"""
    return SourceCodeCheckEntry(
        check_id=check_id,
        name=name,
        target_strings=target_strings,
        description=description,
        match_type=match_type,
    )


def _catalog(
        *,
        reverse_order: bool = False,
        alternate_display: bool = False,
        system_targets: tuple[str, ...] = ("system", "_wsystem"),
        system_match_type: SourceCodeCheckMatchType = SourceCodeCheckMatchType.FUNCTION_CALL,
) -> SourceCodeCheckCatalog:
    """順序、表示文、検査内容を切り替えられるカタログを作る。"""
    name_suffix = "変更後" if alternate_display else "変更前"
    process_entries = (
        _entry(
            "system",
            target_strings=system_targets,
            match_type=system_match_type,
            name=f"外部コマンド {name_suffix}",
            description=f"外部コマンドの説明 {name_suffix}",
        ),
        _entry(
            "popen",
            target_strings=("popen", "_popen"),
            name=f"プロセス生成 {name_suffix}",
            description=f"プロセス生成の説明 {name_suffix}",
        ),
    )
    file_entries = (
        _entry(
            "remove",
            target_strings=("remove", "_wremove"),
            name=f"ファイル削除 {name_suffix}",
            description=f"ファイル削除の説明 {name_suffix}",
        ),
    )
    if reverse_order:
        process_entries = tuple(reversed(process_entries))
        groups = (
            SourceCodeCheckGroup("file", f"ファイル {name_suffix}", file_entries),
            SourceCodeCheckGroup("process", f"プロセス {name_suffix}", process_entries),
        )
    else:
        groups = (
            SourceCodeCheckGroup("process", f"プロセス {name_suffix}", process_entries),
            SourceCodeCheckGroup("file", f"ファイル {name_suffix}", file_entries),
        )
    return SourceCodeCheckCatalog(groups=groups)


def _settings(
        *,
        suppressed: frozenset[SourceCodeCheckIdentifier] = frozenset(),
        skips: frozenset[SourceCodeCheckSkip] = frozenset(),
) -> ProjectSettings:
    """抑制規則と学生別許可情報を指定したプロジェクト設定を作る。"""
    return ProjectSettings(
        suppressed_source_code_checks=suppressed,
        source_code_check_skips=skips,
    )


def _execute(settings: ProjectSettings, catalog: SourceCodeCheckCatalog) -> str:
    """指定した設定とカタログで対象学生のハッシュを計算する。"""
    repository = Mock()
    repository.get.return_value = settings
    factory = Mock()
    factory.create.return_value = catalog
    service = StudentSecuritySettingsHashService(
        project_settings_repository=repository,
        source_code_check_catalog_factory=factory,
    )
    result = service.execute(STUDENT)
    repository.get.assert_called_once_with()
    factory.create.assert_called_once_with()
    return result


def test_same_settings_always_produce_same_hash() -> None:
    """同一の検査設定と許可情報からは常に同じSHA-256を返す。"""
    settings = _settings(skips=frozenset({
        SourceCodeCheckSkip(STUDENT, SOURCE_SHA_A),
    }))
    first = _execute(settings, _catalog())
    second = _execute(settings, _catalog())
    assert first == second
    assert len(first) == 64


@pytest.mark.parametrize(
    ("settings", "catalog"),
    [
        (
            _settings(suppressed=frozenset({
                SourceCodeCheckIdentifier("process", "system"),
            })),
            _catalog(),
        ),
        (
            _settings(),
            _catalog(system_targets=("system", "_wsystem", "custom_system")),
        ),
        (
            _settings(),
            _catalog(system_match_type=SourceCodeCheckMatchType.STRING_LITERAL),
        ),
    ],
    ids=["active-rule", "target-strings", "match-type"],
)
def test_effective_rule_changes_change_hash(
        settings: ProjectSettings,
        catalog: SourceCodeCheckCatalog,
) -> None:
    """有効な規則、検出方式、検査対象文字列の変更をハッシュへ反映する。"""
    assert _execute(settings, catalog) != _execute(_settings(), _catalog())


def test_target_student_approval_changes_hash() -> None:
    """対象学生の許可済みソースが増えるとハッシュが変化する。"""
    before = _execute(_settings(), _catalog())
    after = _execute(_settings(skips=frozenset({
        SourceCodeCheckSkip(STUDENT, SOURCE_SHA_A),
    })), _catalog())
    assert before != after


def test_other_student_approval_does_not_change_hash() -> None:
    """他の学生だけに属する許可情報をハッシュから除外する。"""
    before = _execute(_settings(), _catalog())
    after = _execute(_settings(skips=frozenset({
        SourceCodeCheckSkip(OTHER_STUDENT, SOURCE_SHA_B),
    })), _catalog())
    assert before == after


def test_storage_order_and_display_text_do_not_change_hash() -> None:
    """規則の格納順序、対象文字列順、表示名、説明文をハッシュから除外する。"""
    standard = _catalog()
    reordered = _catalog(
        reverse_order=True,
        alternate_display=True,
        system_targets=("_wsystem", "system"),
    )
    settings = _settings(skips=frozenset({
        SourceCodeCheckSkip(STUDENT, SOURCE_SHA_A),
        SourceCodeCheckSkip(STUDENT, SOURCE_SHA_B),
    }))
    assert _execute(settings, standard) == _execute(settings, reordered)


def test_project_container_registers_service() -> None:
    """ProjectContainerがプロジェクト固有の依存先でServiceを構成する。"""
    from autoprogen.application.container.project import ProjectContainer

    container = ProjectContainer(
        project_id=ProjectID("project"),
        match_get_best_service=Mock(),
        project_repository=Mock(),
        global_settings_repository=Mock(),
        test_source_repository=Mock(),
        project_path_layout=Mock(),
        project_core_io=Mock(),
        readonly_excel_worksheet_gateway=Mock(),
    )
    service = container.student_security_settings_hash_service
    assert isinstance(service, StudentSecuritySettingsHashService)
    assert service is container.student_security_settings_hash_service
