import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest

from application.container import AppContainer, ProjectContainer
from domain.model.value import ProjectID
from infra.path_layout import AppPathConfig
from tests.helpers.archive_names import normalize_archive_name
from usecase.dto.project import ProjectInitializeResult


@dataclass(frozen=True)
class ProjectInitializeRun:
    project_container: ProjectContainer
    result: ProjectInitializeResult
    archive_fullpath: Path


@pytest.fixture
def test_root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("autoprogen")


@pytest.fixture
def app_path_config(test_root: Path) -> AppPathConfig:
    return AppPathConfig.testing(test_root)


def _copy_required_app_resources(
        *,
        repo_root: Path,
        app_path_config: AppPathConfig,
) -> None:
    app_path_config.app_base_dir.mkdir(parents=True, exist_ok=True)
    app_path_config.project_store_dir.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(
        repo_root / "app_version.json",
        app_path_config.app_base_dir / "app_version.json",
    )

    vctest_src = repo_root / "vctest"
    if vctest_src.exists():
        shutil.copytree(
            vctest_src,
            app_path_config.app_base_dir / "vctest",
            dirs_exist_ok=True,
        )


@pytest.fixture
def prepared_app_path_config(app_path_config: AppPathConfig) -> AppPathConfig:
    repo_root = Path(__file__).parents[1]

    _copy_required_app_resources(
        repo_root=repo_root,
        app_path_config=app_path_config,
    )

    return app_path_config


@pytest.fixture
def app_container(prepared_app_path_config: AppPathConfig) -> AppContainer:
    return AppContainer(
        app_path_config=prepared_app_path_config,
    )


@pytest.fixture
def archive_path() -> Callable[[str], Path]:
    def _archive_path(name: str) -> Path:
        normalized_name = normalize_archive_name(name)
        archive_fullpath = Path(__file__).parent / "testdata" / "archives" / normalized_name
        if archive_fullpath.is_file():
            return archive_fullpath

        raise AssertionError(
            "Archive fixture not found: "
            + normalized_name
            + "\nPath:\n"
            + str(archive_fullpath)
        )

    return _archive_path


@pytest.fixture
def create_project(app_container: AppContainer):
    def _create_project(
            *,
            project_name: str,
            source_archive_name: str,
            target_number: int = 2,
    ) -> ProjectID:
        return app_container.project_create_usecase.execute(
            project_name=project_name,
            target_number=target_number,
            zip_name=source_archive_name,
        )

    return _create_project


@pytest.fixture
def open_project_container(app_container: AppContainer):
    def _open_project_container(project_id: ProjectID) -> ProjectContainer:
        app_container.project_open_usecase.execute(project_id)
        return app_container.create_project_container(project_id)

    return _open_project_container


@pytest.fixture
def run_project_initialize_from_archive(
        create_project,
        open_project_container,
        archive_path,
):
    def _run_project_initialize_from_archive(
            *,
            archive_name: str,
            project_name: str,
            target_number: int = 2,
    ) -> ProjectInitializeRun:
        normalized_archive_name = normalize_archive_name(archive_name)
        archive_fullpath = archive_path(normalized_archive_name)

        project_id = create_project(
            project_name=project_name,
            source_archive_name=normalized_archive_name,
            target_number=target_number,
        )

        project_container = open_project_container(project_id)

        result = project_container.current_project_initialize_static_usecase.execute(
            manaba_report_archive_fullpath=archive_fullpath,
        )

        return ProjectInitializeRun(
            project_container=project_container,
            result=result,
            archive_fullpath=archive_fullpath,
        )

    return _run_project_initialize_from_archive


@pytest.fixture
def initialized_project_from_archive(run_project_initialize_from_archive):
    def _initialized_project_from_archive(
            *,
            archive_name: str,
            project_name: str,
            target_number: int = 2,
    ) -> ProjectContainer:
        run = run_project_initialize_from_archive(
            archive_name=archive_name,
            project_name=project_name,
            target_number=target_number,
        )

        assert not run.result.has_error, run.result.message

        return run.project_container

    return _initialized_project_from_archive
