import shutil
import zipfile
from pathlib import Path


def _create_project_and_run_initialize(
        *,
        app_container,
        project_name: str,
        archive_fullpath: Path,
        target_number: int = 2,
):
    project_id = app_container.project_create_usecase.execute(
        project_name=project_name,
        target_number=target_number,
        zip_name=archive_fullpath.name,
    )
    app_container.project_open_usecase.execute(project_id)
    project_container = app_container.create_project_container(project_id)
    result = project_container.current_project_initialize_static_usecase.execute(
        manaba_report_archive_fullpath=archive_fullpath,
    )
    return project_container, result


def _copy_archive(
        *,
        source_archive_fullpath: Path,
        destination_archive_fullpath: Path,
) -> Path:
    shutil.copyfile(source_archive_fullpath, destination_archive_fullpath)
    return destination_archive_fullpath


def _add_extra_submission_folder_to_archive(
        *,
        source_archive_fullpath: Path,
        destination_archive_fullpath: Path,
) -> Path:
    with zipfile.ZipFile(source_archive_fullpath, "r") as src, zipfile.ZipFile(
            destination_archive_fullpath, "w", compression=zipfile.ZIP_DEFLATED
    ) as dst:
        for info in src.infolist():
            if info.is_dir():
                dst.writestr(info, b"")
                continue
            dst.writestr(info, src.read(info.filename))
        dst.writestr("extra_student@extra_student/prog02_1.c", b"int main(){return 0;}")
    return destination_archive_fullpath


def test_project_initialize_from_broken_archive_returns_error(
        app_container,
        test_root,
):
    archive_fullpath = test_root / "broken_archive.zip"
    archive_fullpath.write_bytes(b"not-a-zip")

    project_container, result = _create_project_and_run_initialize(
        app_container=app_container,
        project_name="archive_init_broken_archive",
        archive_fullpath=archive_fullpath,
    )

    assert result.has_error
    assert "破損" in result.message
    assert not project_container.current_project_repository.get().is_initialized
    assert project_container.student_repository.list() == []


def test_project_initialize_from_archive_without_reportlist_returns_error(
        app_container,
        archive_path,
        test_root,
):
    source_archive_fullpath = archive_path("report-test-1")
    archive_fullpath = _copy_archive(
        source_archive_fullpath=source_archive_fullpath,
        destination_archive_fullpath=test_root / "report_test_1_without_reportlist.zip",
    )

    with zipfile.ZipFile(archive_fullpath, "r") as src, zipfile.ZipFile(
            test_root / "report_test_1_without_reportlist_repacked.zip",
            "w",
            compression=zipfile.ZIP_DEFLATED,
    ) as dst:
        for info in src.infolist():
            if info.filename.endswith("reportlist.xlsx"):
                continue
            if info.is_dir():
                dst.writestr(info, b"")
                continue
            dst.writestr(info, src.read(info.filename))
    archive_fullpath = test_root / "report_test_1_without_reportlist_repacked.zip"

    project_container, result = _create_project_and_run_initialize(
        app_container=app_container,
        project_name="archive_init_missing_reportlist",
        archive_fullpath=archive_fullpath,
    )

    assert result.has_error
    assert "reportlist.xlsx" in result.message
    assert not project_container.current_project_repository.get().is_initialized
    assert project_container.student_repository.list() == []


def test_project_initialize_from_archive_with_extra_submission_folder_returns_error(
        app_container,
        archive_path,
        test_root,
):
    archive_fullpath = _add_extra_submission_folder_to_archive(
        source_archive_fullpath=archive_path("report-test-1"),
        destination_archive_fullpath=test_root / "report_test_1_with_extra_folder.zip",
    )

    project_container, result = _create_project_and_run_initialize(
        app_container=app_container,
        project_name="archive_init_extra_submission_folder",
        archive_fullpath=archive_fullpath,
    )

    assert result.has_error
    assert "存在しないはずの提出フォルダ" in result.message
    assert "extra_student@extra_student" in result.message
    assert not project_container.current_project_repository.get().is_initialized
    assert project_container.student_repository.list() == []
