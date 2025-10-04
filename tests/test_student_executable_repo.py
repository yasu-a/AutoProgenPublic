import pytest

from application.dependency.repository import get_student_executable_repository
from domain.model.file_item import ExecutableFileItem


def test_get_not_found(sample_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = sample_student_ids

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id)


def test_put_and_get(sample_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = sample_student_ids

    repo.put(fake_student_id, ExecutableFileItem(content_bytes=b"\0\1\2\3\4\5\6\7"))

    assert repo.get(fake_student_id).content_bytes == b"\0\1\2\3\4\5\6\7"


def test_put_and_get_multiple(sample_student_ids):
    repo = get_student_executable_repository()
    fake_student_id_1, fake_student_id_2, *_ = sample_student_ids

    repo.put(fake_student_id_1, ExecutableFileItem(content_bytes=b"\0\1\2\3"))
    repo.put(fake_student_id_2, ExecutableFileItem(content_bytes=b"\4\5\6\7"))

    assert repo.get(fake_student_id_1).content_bytes == b"\0\1\2\3"
    assert repo.get(fake_student_id_2).content_bytes == b"\4\5\6\7"


def test_exists(sample_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = sample_student_ids

    assert not repo.exists(fake_student_id)

    repo.put(fake_student_id, ExecutableFileItem(content_bytes=b"\0\1\2\3\4\5\6\7"))

    assert repo.exists(fake_student_id)


def test_delete_not_found(sample_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = sample_student_ids

    with pytest.raises(FileNotFoundError):
        repo.delete(fake_student_id)


def test_put_and_delete(sample_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = sample_student_ids

    repo.put(fake_student_id, ExecutableFileItem(content_bytes=b"\0\1\2\3\4\5\6\7"))
    repo.delete(fake_student_id)

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id)


def test_put_and_delete_multiple(sample_student_ids):
    repo = get_student_executable_repository()
    fake_student_id_1, fake_student_id_2, *_ = sample_student_ids

    repo.put(fake_student_id_1, ExecutableFileItem(content_bytes=b"\0\1\2\3"))
    repo.put(fake_student_id_2, ExecutableFileItem(content_bytes=b"\4\5\6\7"))
    repo.delete(fake_student_id_1)

    with pytest.raises(FileNotFoundError):
        repo.get(fake_student_id_1)

    assert repo.get(fake_student_id_2).content_bytes == b"\4\5\6\7"


def test_overwrite(sample_student_ids):
    repo = get_student_executable_repository()
    fake_student_id, *_ = sample_student_ids
    test_content_1 = b"\0\1\2\3"
    test_content_2 = b"\4\5\6\7"

    repo.put(fake_student_id, ExecutableFileItem(content_bytes=test_content_1))
    assert repo.get(fake_student_id).content_bytes == test_content_1
    repo.put(fake_student_id, ExecutableFileItem(content_bytes=test_content_2))
    assert repo.get(fake_student_id).content_bytes == test_content_2
