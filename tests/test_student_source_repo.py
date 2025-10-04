import pytest

from application.dependency.repository import get_student_source_repository
from domain.model.file_item import SourceFileItem


def test_get_not_found(sample_student_ids):
    repo = get_student_source_repository()
    fake_student_id, *_ = sample_student_ids

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id)


def test_put_and_get(sample_student_ids):
    repo = get_student_source_repository()
    fake_student_id, *_ = sample_student_ids
    test_content = b"some code"
    test_encoding = "utf-8"

    repo.put(fake_student_id, SourceFileItem(content_bytes=test_content, encoding=test_encoding))

    retrieved_item = repo.get(fake_student_id)
    assert retrieved_item.content_bytes == test_content
    assert retrieved_item.encoding == test_encoding


def test_put_and_get_multiple(sample_student_ids):
    repo = get_student_source_repository()
    fake_student_id_1, fake_student_id_2, *_ = sample_student_ids

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


def test_exists(sample_student_ids):
    repo = get_student_source_repository()
    fake_student_id, *_ = sample_student_ids

    assert not repo.exists(fake_student_id)

    repo.put(fake_student_id, SourceFileItem(content_bytes=b"some code", encoding="utf-8"))

    assert repo.exists(fake_student_id)


def test_delete_not_found(sample_student_ids):
    repo = get_student_source_repository()
    fake_student_id, *_ = sample_student_ids

    with pytest.raises(FileNotFoundError):
        repo.delete(fake_student_id)


def test_put_and_delete(sample_student_ids):
    repo = get_student_source_repository()
    fake_student_id, *_ = sample_student_ids

    repo.put(fake_student_id, SourceFileItem(content_bytes=b"more code", encoding="utf-8"))
    repo.delete(fake_student_id)

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id)


def test_put_and_delete_multiple(sample_student_ids):
    repo = get_student_source_repository()
    fake_student_id_1, fake_student_id_2, *_ = sample_student_ids

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


def test_overwrite(sample_student_ids):
    repo = get_student_source_repository()
    fake_student_id, *_ = sample_student_ids
    test_content_1 = b"some code"
    test_content_2 = b"more code"
    test_encoding = "utf-8"

    repo.put(fake_student_id, SourceFileItem(content_bytes=test_content_1, encoding=test_encoding))
    assert repo.get(fake_student_id).content_bytes == test_content_1
    repo.put(fake_student_id, SourceFileItem(content_bytes=test_content_2, encoding=test_encoding))
    assert repo.get(fake_student_id).content_bytes == test_content_2
