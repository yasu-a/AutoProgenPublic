from pathlib import Path
from unittest.mock import Mock

from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import StudentID
from autoprogen.domain.service.source_code_factory import SourceCodeFactory
from autoprogen.infra.io.project_database import ProjectDatabaseIO
from autoprogen.infra.repository.student_source_code import StudentSourceRepository
from autoprogen.service.storage import StorageLoadStudentSourceService
from autoprogen.service.student_dynamic import StudentDynamicSetSourceCodeService
from autoprogen.service.student_submission import StudentSubmissionGetSourceCodeService


def _create_student_source_repository(
    database_path: Path,
    student_id: StudentID,
) -> StudentSourceRepository:
    """外部キーの参照先を用意した学生ソースRepositoryを作成する。"""
    database_io = ProjectDatabaseIO(database_path=database_path)
    with database_io.connect() as connection:
        connection.execute(
            "CREATE TABLE student (student_id TEXT NOT NULL PRIMARY KEY)"
        )
        connection.execute(
            "INSERT INTO student (student_id) VALUES (?)",
            (str(student_id),),
        )
        connection.commit()
    return StudentSourceRepository(project_database_io=database_io)


def test_normalized_source_code_is_preserved_from_build_to_compile_storage(
    tmp_path: Path,
) -> None:
    """BUILDで正規化したソースが同じUTF-8バイト列でCOMPILEへ渡ることを確認する。"""
    student_id = StudentID("00A0000000A")
    source_relative_path = Path("prog02.c")
    submitted_text = "// 日本語\r\nint main(void) {\r\n    return 0;\r\n}\r\n"
    expected_source_code = SourceCode(
        text="// 日本語\nint main(void) {\n    return 0;\n}\n"
    )

    student_repository = Mock()
    student_repository.get.return_value.is_submitted = True
    source_path_service = Mock()
    source_path_service.execute.return_value = [source_relative_path]
    project_path_layout = Mock()
    project_path_layout.student_submission_dir.return_value = Path("submission")
    current_project_core_io = Mock()
    current_project_core_io.read_file_content_bytes.return_value = (
        submitted_text.encode("shift-jis")
    )
    source_get_service = StudentSubmissionGetSourceCodeService(
        student_submission_list_source_relative_path_query_service=source_path_service,
        student_repo=student_repository,
        source_code_factory=SourceCodeFactory(),
        project_path_layout=project_path_layout,
        current_project_core_io=current_project_core_io,
    )

    # BUILDと同じ経路で対象ファイルを正規化し、SQLiteへ保存する。
    source_code = source_get_service.execute(student_id)
    source_repository = _create_student_source_repository(
        tmp_path / "project.sqlite3",
        student_id,
    )
    StudentDynamicSetSourceCodeService(
        student_source_repo=source_repository,
    ).execute(
        student_id=student_id,
        source_code=source_code,
    )

    # COMPILEと同じ経路で保存済みソースを一時ストレージへ配置する。
    storage = Mock()
    storage.files = {}
    storage_repository = Mock()
    storage_repository.get.return_value = storage
    loaded_source_code = StorageLoadStudentSourceService(
        student_source_repo=source_repository,
        storage_repo=storage_repository,
    ).execute(
        student_id=student_id,
        storage_id=Mock(),
        file_relative_path=Path("main.c"),
    )

    assert source_code == expected_source_code
    assert loaded_source_code == expected_source_code
    assert storage.files[Path("main.c")] == expected_source_code.to_utf8_bytes()
    assert loaded_source_code.calculate_sha256() == expected_source_code.calculate_sha256()
