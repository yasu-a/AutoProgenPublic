import pytest

from application.dependency.repositories import get_student_mark_repository
from domain.errors import RepositoryItemNotFoundError
from domain.models.student_mark import StudentMark


@pytest.fixture
def repo():
    return get_student_mark_repository()


@pytest.fixture
def student_id_1(sample_student_ids):
    return sample_student_ids[0]


@pytest.fixture
def student_id_2(sample_student_ids):
    return sample_student_ids[1]


def test_create_and_get(repo, student_id_1):
    """createとgetの基本テスト"""
    # 存在しない場合は作成
    mark = repo.create(student_id_1)
    assert mark.student_id == student_id_1
    assert not mark.is_marked
    # 未採点状態でscoreにアクセスするとValueError
    with pytest.raises(ValueError, match="This student has not been marked yet"):
        _ = mark.score

    # 取得して確認
    retrieved = repo.get(student_id_1)
    assert retrieved.student_id == student_id_1
    assert not retrieved.is_marked
    # 未採点状態でscoreにアクセスするとValueError
    with pytest.raises(ValueError, match="This student has not been marked yet"):
        _ = retrieved.score


def test_put_and_get(repo, student_id_1):
    """putとgetの基本テスト"""
    # 採点データを作成
    mark = StudentMark(student_id=student_id_1, score=85)
    repo.put(mark)

    # 取得して確認
    retrieved = repo.get(student_id_1)
    assert retrieved.student_id == student_id_1
    assert retrieved.score == 85
    assert retrieved.is_marked


def test_exists(repo, student_id_1, student_id_2):
    """existsのテスト"""
    # 存在しない場合
    assert not repo.exists(student_id_1)
    assert not repo.exists(student_id_2)

    # 作成後は存在する
    repo.create(student_id_1)
    assert repo.exists(student_id_1)
    assert not repo.exists(student_id_2)


def test_get_not_found(repo, student_id_1):
    """存在しないデータを取得しようとした場合のテスト"""
    with pytest.raises(RepositoryItemNotFoundError):
        repo.get(student_id_1)


def test_put_overwrite(repo, student_id_1):
    """putで上書きするテスト"""
    # 最初のデータ
    mark1 = StudentMark(student_id=student_id_1, score=85)
    repo.put(mark1)

    # 上書き
    mark2 = StudentMark(student_id=student_id_1, score=92)
    repo.put(mark2)

    # 上書きされたことを確認
    retrieved = repo.get(student_id_1)
    assert retrieved.score == 92


def test_timestamp_on_put(repo, student_id_1):
    """put時のタイムスタンプ更新テスト"""
    # 初期状態ではタイムスタンプが存在しない
    assert repo.get_timestamp(student_id_1) is None

    # データをputするとタイムスタンプが設定される
    mark = StudentMark(student_id=student_id_1, score=85)
    repo.put(mark)

    timestamp = repo.get_timestamp(student_id_1)
    assert timestamp is not None
    # タイムスタンプが現在時刻に近いことを確認（1分以内）
    from datetime import datetime
    now = datetime.now()
    assert abs((timestamp - now).total_seconds()) < 60


def test_timestamp_on_overwrite(repo, student_id_1):
    """上書き時のタイムスタンプ更新テスト"""
    # 最初のデータをput
    mark1 = StudentMark(student_id=student_id_1, score=85)
    repo.put(mark1)
    timestamp1 = repo.get_timestamp(student_id_1)

    # 少し待ってから上書き
    import time
    time.sleep(0.1)  # 100ms待機

    # 上書き
    mark2 = StudentMark(student_id=student_id_1, score=92)
    repo.put(mark2)
    timestamp2 = repo.get_timestamp(student_id_1)

    # タイムスタンプが更新されていることを確認
    assert timestamp2 > timestamp1


def test_timestamp_not_update_on_get(repo, student_id_1):
    """get時のタイムスタンプ変化なしテスト"""
    # データを作成
    mark = StudentMark(student_id=student_id_1, score=85)
    repo.put(mark)
    original_timestamp = repo.get_timestamp(student_id_1)

    # 少し待ってからget
    import time
    time.sleep(0.1)  # 100ms待機

    # getを実行
    retrieved = repo.get(student_id_1)
    assert retrieved.score == 85

    # タイムスタンプが変化していないことを確認
    current_timestamp = repo.get_timestamp(student_id_1)
    assert current_timestamp == original_timestamp


def test_timestamp_on_create(repo, student_id_1):
    """create時のタイムスタンプ設定テスト"""
    # createを実行
    _ = repo.create(student_id_1)

    # タイムスタンプが設定されていることを確認
    timestamp = repo.get_timestamp(student_id_1)
    assert timestamp is not None

    # タイムスタンプが現在時刻に近いことを確認（1分以内）
    from datetime import datetime
    now = datetime.now()
    assert abs((timestamp - now).total_seconds()) < 60


def test_timestamp_for_nonexistent_student(repo, student_id_1):
    """存在しない学生のタイムスタンプ取得テスト"""
    # 存在しない学生のタイムスタンプを取得
    timestamp = repo.get_timestamp(student_id_1)
    assert timestamp is None


def test_timestamp_consistency_with_data(repo, student_id_1, student_id_2):
    """タイムスタンプとデータの一貫性テスト"""
    # 学生1のデータを作成
    mark1 = StudentMark(student_id=student_id_1, score=85)
    repo.put(mark1)
    timestamp1 = repo.get_timestamp(student_id_1)

    # 学生2のデータを作成
    mark2 = StudentMark(student_id=student_id_2, score=92)
    repo.put(mark2)
    timestamp2 = repo.get_timestamp(student_id_2)

    # それぞれ独立したタイムスタンプを持っていることを確認
    assert timestamp1 < timestamp2

    # データを取得して一貫性を確認
    retrieved1 = repo.get(student_id_1)
    retrieved2 = repo.get(student_id_2)

    assert retrieved1.score == 85
    assert retrieved2.score == 92


def test_multiple_students_independence(repo, student_id_1, student_id_2):
    """複数生徒の独立性テスト"""
    # 生徒1のデータ
    mark1 = StudentMark(student_id=student_id_1, score=85)
    repo.put(mark1)

    # 生徒2のデータ
    mark2 = StudentMark(student_id=student_id_2, score=92)
    repo.put(mark2)

    # それぞれ独立していることを確認
    retrieved1 = repo.get(student_id_1)
    retrieved2 = repo.get(student_id_2)

    assert retrieved1.student_id == student_id_1
    assert retrieved1.score == 85
    assert retrieved2.student_id == student_id_2
    assert retrieved2.score == 92


def test_score_none_and_setter(repo, student_id_1):
    """scoreがNoneの場合とsetterのテスト"""
    # 初期状態
    mark = repo.create(student_id_1)
    assert not mark.is_marked
    # 未採点状態でscoreにアクセスするとValueError
    with pytest.raises(ValueError, match="This student has not been marked yet"):
        _ = mark.score

    # scoreを設定
    mark.score = 85
    repo.put(mark)

    # 取得して確認
    retrieved = repo.get(student_id_1)
    assert retrieved.score == 85
    assert retrieved.is_marked

    # scoreをNoneに戻す
    mark.set_unmarked()
    repo.put(mark)

    # 取得して確認
    retrieved = repo.get(student_id_1)
    assert not retrieved.is_marked
    # 未採点状態でscoreにアクセスするとValueError
    with pytest.raises(ValueError, match="This student has not been marked yet"):
        _ = retrieved.score


def test_score_property_validation(repo, student_id_1):
    """scoreプロパティのバリデーションテスト"""
    # 未採点の状態でscoreにアクセス
    mark = repo.create(student_id_1)
    with pytest.raises(ValueError, match="This student has not been marked yet"):
        _ = mark.score

    # scoreを設定後はアクセス可能
    mark.score = 85
    assert mark.score == 85


def test_value_error_on_unmarked_score_access(repo, student_id_1):
    """未採点状態でのscoreアクセス時のValueErrorテスト"""
    # 未採点のStudentMarkを作成
    mark = StudentMark(student_id=student_id_1, score=None)

    # scoreプロパティにアクセスするとValueErrorが発生
    with pytest.raises(ValueError, match="This student has not been marked yet"):
        _ = mark.score

    # is_markedはFalse
    assert not mark.is_marked

    # 採点後はアクセス可能
    mark.score = 85
    assert mark.score == 85
    assert mark.is_marked


def test_score_setter_validation(repo, student_id_1):
    """score setterのバリデーションテスト"""
    mark = StudentMark(student_id=student_id_1, score=None)

    # 有効な値を設定
    mark.score = 85
    assert mark.score == 85
    assert mark.is_marked

    # set_unmarkedでNoneに戻す
    mark.set_unmarked()
    assert not mark.is_marked
    # 未採点状態でscoreにアクセスするとValueError
    with pytest.raises(ValueError, match="This student has not been marked yet"):
        _ = mark.score

    # 再度有効な値を設定
    mark.score = 92
    assert mark.score == 92
    assert mark.is_marked


def test_student_mark_methods(repo, student_id_1):
    """StudentMarkのメソッドテスト"""
    # 未採点状態
    mark = repo.create(student_id_1)
    assert not mark.is_marked
    with pytest.raises(ValueError):
        _ = mark.score

    # 採点後
    mark.score = 85
    assert mark.is_marked
    assert mark.score == 85

    # 未採点に戻す
    mark.set_unmarked()
    assert not mark.is_marked
    with pytest.raises(ValueError):
        _ = mark.score
