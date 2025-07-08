from pathlib import Path

import pytest

from application.dependency.path_provider import get_database_path_provider
from application.dependency.repositories import get_student_source_repository
from application.state.current_project import set_current_project_id, get_current_project_id
from application.state.debug import set_debug
from domain.models.file_item import SourceFileItem
from domain.models.values import ProjectID, StudentID


def override_dependency():
    import application.dependency.path_provider

    def get_project_list_folder_fullpath_override():
        return Path(__file__).parent / "test_project_list"

    application.dependency.path_provider.get_project_list_folder_fullpath \
        = get_project_list_folder_fullpath_override

    def get_global_base_path_override():
        return Path(__file__).parent / "test_global"

    application.dependency.path_provider.get_global_base_path \
        = get_global_base_path_override

    def get_storage_path_provider_override():
        return Path(__file__).parent / "test_storage"

    application.dependency.path_provider.get_storage_path_provider \
        = get_storage_path_provider_override


@pytest.fixture(autouse=True)
def setup_test():
    print("setup_test")
    set_debug(True)
    if get_current_project_id() is None:
        set_current_project_id(ProjectID("test_project_id"))
    override_dependency()
    database_fullpath = get_database_path_provider().fullpath()
    if database_fullpath.exists():
        database_fullpath.unlink()


def test_get_not_found():
    repo = get_student_source_repository()
    fake_student_id = StudentID("00D0000000A")

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id)


def test_put_and_get():
    repo = get_student_source_repository()
    fake_student_id = StudentID("00D0000000A")
    test_content = b"some code"
    test_encoding = "utf-8"

    repo.put(fake_student_id, SourceFileItem(content_bytes=test_content, encoding=test_encoding))

    retrieved_item = repo.get(fake_student_id)
    assert retrieved_item.content_bytes == test_content
    assert retrieved_item.encoding == test_encoding


def test_put_and_get_multiple():
    repo = get_student_source_repository()
    fake_student_id_1 = StudentID("00D0000000A")
    fake_student_id_2 = StudentID("00D0000001B")

    # ここを修正しました
    content_1 = b"some code 1"
    encoding_1 = "utf-8"
    content_2 = b"some code 2"
    encoding_2 = "ascii"

    repo.put(fake_student_id_1, SourceFileItem(content_bytes=content_1, encoding=encoding_1))
    repo.put(fake_student_id_2, SourceFileItem(content_bytes=content_2, encoding=encoding_2))

    retrieved_item_1 = repo.get(fake_student_id_1)
    assert retrieved_item_1.content_bytes == content_1
    assert retrieved_item_1.encoding == encoding_1

    retrieved_item_2 = repo.get(fake_student_id_2)
    assert retrieved_item_2.content_bytes == content_2
    assert retrieved_item_2.encoding == encoding_2


def test_exists():
    repo = get_student_source_repository()
    fake_student_id = StudentID("00D0000000A")

    assert not repo.exists(fake_student_id)

    repo.put(fake_student_id, SourceFileItem(content_bytes=b"some code", encoding="utf-8"))

    assert repo.exists(fake_student_id)


def test_delete_not_found():
    repo = get_student_source_repository()
    fake_student_id = StudentID("00D0000000A")

    with pytest.raises(FileNotFoundError):
        repo.delete(fake_student_id)


def test_put_and_delete():
    repo = get_student_source_repository()
    fake_student_id = StudentID("00D0000000A")

    repo.put(fake_student_id, SourceFileItem(content_bytes=b"more code", encoding="utf-8"))
    repo.delete(fake_student_id)

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id)


def test_put_and_delete_multiple():
    repo = get_student_source_repository()
    fake_student_id_1 = StudentID("00D0000000A")
    fake_student_id_2 = StudentID("00D0000001B")

    repo.put(fake_student_id_1,
             SourceFileItem(content_bytes=b"code 1", encoding="utf-8"))  # ここは元のままでよろしいでしょうか？
    repo.put(fake_student_id_2,
             SourceFileItem(content_bytes=b"code 2", encoding="ascii"))  # ここは元のままでよろしいでしょうか？
    repo.delete(fake_student_id_1)

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id_1)

    retrieved_item_2 = repo.get(fake_student_id_2)
    assert retrieved_item_2.content_bytes == b"code 2"
    assert retrieved_item_2.encoding == "ascii"


def test_overwrite():
    repo = get_student_source_repository()
    fake_student_id = StudentID("00D0000000A")
    test_content_1 = b"some code"
    test_content_2 = b"more code"
    test_encoding = "utf-8"

    repo.put(fake_student_id, SourceFileItem(content_bytes=test_content_1, encoding=test_encoding))
    assert repo.get(fake_student_id).content_bytes == test_content_1
    repo.put(fake_student_id, SourceFileItem(content_bytes=test_content_2, encoding=test_encoding))
    assert repo.get(fake_student_id).content_bytes == test_content_2
