from datetime import timedelta

import pytest

from application.dependency.services import get_match_get_best_service
from domain.models.pattern import PatternList, TextPattern, SpacePattern, EOLPattern, RegexPattern
from domain.models.test_config_options import TestConfigOptions

r"""
パターンマッチ機能の仕様:

1. パターンマッチの基本動作
- 入力テキストに対して指定されたパターンを順番にマッチングする
- 正規表現ベースのマッチングにより、最適なマッチングが選択される
- パターンの結果はMatchedTokenとNonmatchedTokenとして管理される
- 全角文字は半角文字に変換されてからマッチングが実行される

2. パターンの種類と特性
- TextPattern: 指定されたテキストと一致するかを確認するパターン
  * is_expected: パターンが出現すべきかどうか（true: 出現すべき、false: 出現すべきでない）
  * is_multiple_space_ignored: 複数の空白を一つとして扱うかどうか（デフォルト: true）
  * is_word: 単語として扱うかどうか（単語境界のチェック、デフォルト: false）
- RegexPattern: カスタム正規表現パターン
- SpacePattern: 空白文字（スペース、タブ）とマッチングするパターン（\s+）
- EOLPattern: 改行文字とマッチングするパターン（\n）

3. マッチング結果の管理
- MatchedToken: パターンがマッチした場合に生成され、開始位置と終了位置を記録
- NonmatchedToken: パターンがマッチしなかった場合に生成され、対象パターンを記録
- マッチング結果はMatchResultとして返され、正規表現パターンとテスト実行時間も記録される

4. パターンリスト管理
- PatternListによって複数のパターンがまとめて管理される
- パターンには順序があり、インデックスによって識別される
- 各パターンは正規表現グループ名（_0, _1, ...）を持つ

5. 正規表現マッチングの仕組み
- パターンリスト全体が一つの正規表現に変換される
- 各パターンは名前付きキャプチャグループとして扱われる
- 期待されるパターン（is_expected=true）は必須、期待されないパターン（is_expected=false）はオプション
- パターン間には任意の文字列（.*?）が挿入される

6. パターンの期待値と検証
- is_expectedフラグによって、パターンが存在すべきか否かを指定可能
- 期待通りにパターンが出現/非出現の場合はテスト成功、そうでない場合は失敗となる
- 全体的なマッチングが失敗した場合、すべてのパターンがNonmatchedTokenとして扱われる
"""


@pytest.fixture
def test_config_options():
    """テスト設定オプションのfixture"""
    return TestConfigOptions(
        ignore_case=False,
    )


@pytest.fixture
def case_insensitive_test_config_options():
    """大文字小文字を無視するテスト設定オプションのfixture"""
    return TestConfigOptions(
        ignore_case=True,
    )


@pytest.fixture
def match_service():
    """マッチサービスのfixture"""
    return get_match_get_best_service()


def test_basic_text_pattern_matching(match_service, test_config_options):
    """基本的なテキストパターンマッチングのテスト"""
    # テストケース: 単純な文字列マッチング
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    result = match_service.execute(
        content_string="Hello World",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    # マッチしたトークンの確認
    assert len(result.matched_tokens) == 2
    assert len(result.nonmatched_tokens) == 0

    # 最初のパターン（Hello）のマッチ確認
    hello_token = result.matched_tokens[0]
    assert hello_token.pattern.index == 0
    assert hello_token.begin == 0
    assert hello_token.end == 5

    # 2番目のパターン（World）のマッチ確認
    world_token = result.matched_tokens[1]
    assert world_token.pattern.index == 1
    assert world_token.begin == 6
    assert world_token.end == 11


def test_text_pattern_with_multiple_spaces(match_service, test_config_options):
    """複数空白を無視するテキストパターンのテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    result = match_service.execute(
        content_string="Hello    World",  # 複数の空白
        patterns=patterns,
        test_config_options=test_config_options,
    )

    # 複数空白があってもマッチすることを確認
    assert len(result.matched_tokens) == 2
    assert len(result.nonmatched_tokens) == 0


def test_text_pattern_with_word_boundary(match_service, test_config_options):
    """単語境界を考慮するテキストパターンのテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="test", is_multiple_space_ignored=True,
                    is_word=True),
    ])

    # 単語境界でマッチするケース
    result = match_service.execute(
        content_string="test case",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert len(result.matched_tokens) == 1
    assert len(result.nonmatched_tokens) == 0

    # 単語境界でマッチしないケース
    result = match_service.execute(
        content_string="testing case",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert len(result.matched_tokens) == 0
    assert len(result.nonmatched_tokens) == 1


def test_space_pattern_matching(match_service, test_config_options):
    """空白パターンのマッチングテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        SpacePattern(index=1, is_expected=True),
        TextPattern(index=2, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    result = match_service.execute(
        content_string="Hello World",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert len(result.matched_tokens) == 3
    assert len(result.nonmatched_tokens) == 0


def test_eol_pattern_matching(match_service, test_config_options):
    """改行パターンのマッチングテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        EOLPattern(index=1, is_expected=True),
        TextPattern(index=2, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    result = match_service.execute(
        content_string="Hello\nWorld",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert len(result.matched_tokens) == 3
    assert len(result.nonmatched_tokens) == 0


def test_regex_pattern_matching(match_service, test_config_options):
    """正規表現パターンのマッチングテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Number:", is_multiple_space_ignored=True,
                    is_word=False),
        RegexPattern(index=1, is_expected=True, regex=r"\d+"),
        TextPattern(index=2, is_expected=True, text="Name:", is_multiple_space_ignored=True,
                    is_word=False),
        RegexPattern(index=3, is_expected=True, regex=r"[A-Za-z]+"),
    ])

    result = match_service.execute(
        content_string="Number: 123 Name: John",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert len(result.matched_tokens) == 4
    assert len(result.nonmatched_tokens) == 0


def test_unexpected_pattern_matching(match_service, test_config_options):
    """期待されないパターンのマッチングテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=False, text="ERROR", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=2, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    # ERRORが含まれていない場合（期待通り）
    result = match_service.execute(
        content_string="Hello World",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert len(result.matched_tokens) == 2  # Hello, World
    assert len(result.nonmatched_tokens) == 1  # ERROR（期待されないのでマッチしない）

    # ERRORが含まれている場合（期待と異なる）
    result = match_service.execute(
        content_string="Hello ERROR World",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert len(result.matched_tokens) == 3  # Hello, ERROR, World
    assert len(result.nonmatched_tokens) == 0


def test_complete_matching_failure(match_service, test_config_options):
    """完全なマッチング失敗のテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    result = match_service.execute(
        content_string="Goodbye Universe",  # マッチしない文字列
        patterns=patterns,
        test_config_options=test_config_options,
    )

    # マッチングが完全に失敗した場合、すべてのパターンがNonmatchedTokenになる
    assert len(result.matched_tokens) == 0
    assert len(result.nonmatched_tokens) == 2


def test_case_insensitive_matching(match_service, case_insensitive_test_config_options):
    """大文字小文字を無視するマッチングのテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    result = match_service.execute(
        content_string="hello world",
        patterns=patterns,
        test_config_options=case_insensitive_test_config_options,
    )

    assert len(result.matched_tokens) == 2
    assert len(result.nonmatched_tokens) == 0


def test_zen_to_han_conversion(match_service, test_config_options):
    """全角文字から半角文字への変換テスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    result = match_service.execute(
        content_string="Ｈｅｌｌｏ　Ｗｏｒｌｄ",  # 全角文字
        patterns=patterns,
        test_config_options=test_config_options,
    )

    # 全角文字が半角文字に変換されてマッチすることを確認
    assert len(result.matched_tokens) == 2
    assert len(result.nonmatched_tokens) == 0


def test_execution_time_recording(match_service, test_config_options):
    """実行時間の記録テスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    result = match_service.execute(
        content_string="Hello",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    # 実行時間が記録されていることを確認
    assert isinstance(result.test_execution_timedelta, timedelta)
    assert result.test_execution_timedelta.total_seconds() >= 0
