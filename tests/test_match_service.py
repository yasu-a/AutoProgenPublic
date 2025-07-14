import random
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
    assert result.count_matched_tokens() == 2
    assert result.count_nonmatched_tokens() == 0

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

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


def test_basic_pattern_1(match_service, test_config_options):
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Exit", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="Small", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=2, is_expected=True, text="3", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=3, is_expected=True, text="Capital", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=4, is_expected=True, text="2", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=5, is_expected=True, text="Numeric", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=6, is_expected=True, text="1", is_multiple_space_ignored=True,
                    is_word=False),
    ])
    result = match_service.execute(
        content_string="Exit.\nSmall letter:10\nCapital letter:2\nNumeric letter:3\n",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.is_accepted is False


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
    assert result.count_matched_tokens() == 2
    assert result.count_nonmatched_tokens() == 0

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


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

    assert result.count_matched_tokens() == 1
    assert result.count_nonmatched_tokens() == 0

    # is_acceptedの確認（期待されるパターンがマッチ）
    assert result.is_accepted is True

    # 単語境界でマッチしないケース
    result = match_service.execute(
        content_string="testing case",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 0
    assert result.count_nonmatched_tokens() == 1

    # is_acceptedの確認（期待されるパターンがマッチしない）
    assert result.is_accepted is False


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

    assert result.count_matched_tokens() == 3
    assert result.count_nonmatched_tokens() == 0

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


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

    assert result.count_matched_tokens() == 3
    assert result.count_nonmatched_tokens() == 0

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


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

    assert result.count_matched_tokens() == 4
    assert result.count_nonmatched_tokens() == 0

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


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

    assert result.count_matched_tokens() == 2  # Hello, World
    assert result.count_nonmatched_tokens() == 1  # ERROR（期待されないのでマッチしない）

    # is_acceptedの確認（期待されないパターンが出現しない）
    assert result.is_accepted is True

    # ERRORが含まれている場合（期待と異なる）
    result = match_service.execute(
        content_string="Hello ERROR World",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 3  # Hello, ERROR, World
    assert result.count_nonmatched_tokens() == 0

    # is_acceptedの確認（期待されないパターンが出現した）
    assert result.is_accepted is False


# noinspection DuplicatedCode
def test_multiple_unexpected_patterns_continuous(match_service, test_config_options):
    """複数の期待されないパターンが連続で存在する場合のテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="A", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=False, text="X", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=2, is_expected=False, text="Y", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=3, is_expected=True, text="B", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    # XとYが連続で含まれている場合（期待と異なる）
    result = match_service.execute(
        content_string="A X Y B",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 4  # A, X, Y, B
    assert result.count_nonmatched_tokens() == 0

    # 出現位置の確認
    a_token = result.matched_tokens[0]
    assert a_token.pattern.index == 0
    assert a_token.begin == 0
    assert a_token.end == 1

    x_token = result.matched_tokens[1]
    assert x_token.pattern.index == 1
    assert x_token.begin == 2
    assert x_token.end == 3

    y_token = result.matched_tokens[2]
    assert y_token.pattern.index == 2
    assert y_token.begin == 4
    assert y_token.end == 5

    b_token = result.matched_tokens[3]
    assert b_token.pattern.index == 3
    assert b_token.begin == 6
    assert b_token.end == 7

    # is_acceptedの確認（期待されないパターンが出現した）
    assert result.is_accepted is False

    # XとYが含まれていない場合（期待通り）
    result = match_service.execute(
        content_string="A B",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 2  # A, B
    assert result.count_nonmatched_tokens() == 2  # X, Y

    # is_acceptedの確認（期待されないパターンが出現しない）
    assert result.is_accepted is True


# noinspection DuplicatedCode
def test_multiple_unexpected_patterns_discontinuous(match_service, test_config_options):
    """複数の期待されないパターンが非連続で存在する場合のテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="A", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=False, text="X", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=2, is_expected=True, text="B", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=3, is_expected=False, text="Y", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=4, is_expected=True, text="C", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    # XとYが非連続で含まれている場合（期待と異なる）
    result = match_service.execute(
        content_string="A X B Y C",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 5  # A, X, B, Y, C
    assert result.count_nonmatched_tokens() == 0

    # 出現位置の確認
    a_token = result.matched_tokens[0]
    assert a_token.pattern.index == 0
    assert a_token.begin == 0
    assert a_token.end == 1

    x_token = result.matched_tokens[1]
    assert x_token.pattern.index == 1
    assert x_token.begin == 2
    assert x_token.end == 3

    b_token = result.matched_tokens[2]
    assert b_token.pattern.index == 2
    assert b_token.begin == 4
    assert b_token.end == 5

    y_token = result.matched_tokens[3]
    assert y_token.pattern.index == 3
    assert y_token.begin == 6
    assert y_token.end == 7

    c_token = result.matched_tokens[4]
    assert c_token.pattern.index == 4
    assert c_token.begin == 8
    assert c_token.end == 9

    # is_acceptedの確認（期待されないパターンが出現した）
    assert result.is_accepted is False

    # XとYが含まれていない場合（期待通り）
    result = match_service.execute(
        content_string="A B C",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 3  # A, B, C
    assert result.count_nonmatched_tokens() == 2  # X, Y

    # is_acceptedの確認（期待されないパターンが出現しない）
    assert result.is_accepted is True


# noinspection DuplicatedCode
def test_multiple_unexpected_patterns_mixed(match_service, test_config_options):
    """複数の期待されないパターンが混在する場合のテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="A", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=False, text="X", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=2, is_expected=True, text="B", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=3, is_expected=False, text="Y", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=4, is_expected=False, text="Z", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=5, is_expected=True, text="C", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    # すべての期待されないパターンが含まれている場合（期待と異なる）
    result = match_service.execute(
        content_string="A X B Y Z C",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 6  # A, X, B, Y, Z, C
    assert result.count_nonmatched_tokens() == 0

    # 出現位置の確認
    a_token = result.matched_tokens[0]
    assert a_token.pattern.index == 0
    assert a_token.begin == 0
    assert a_token.end == 1

    x_token = result.matched_tokens[1]
    assert x_token.pattern.index == 1
    assert x_token.begin == 2
    assert x_token.end == 3

    b_token = result.matched_tokens[2]
    assert b_token.pattern.index == 2
    assert b_token.begin == 4
    assert b_token.end == 5

    y_token = result.matched_tokens[3]
    assert y_token.pattern.index == 3
    assert y_token.begin == 6
    assert y_token.end == 7

    z_token = result.matched_tokens[4]
    assert z_token.pattern.index == 4
    assert z_token.begin == 8
    assert z_token.end == 9

    c_token = result.matched_tokens[5]
    assert c_token.pattern.index == 5
    assert c_token.begin == 10
    assert c_token.end == 11

    # is_acceptedの確認（期待されないパターンが出現した）
    assert result.is_accepted is False

    # 一部の期待されないパターンのみが含まれている場合（期待と異なる）
    result = match_service.execute(
        content_string="A X B C",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 4  # A, X, B, C
    assert result.count_nonmatched_tokens() == 2  # Y, Z

    # is_acceptedの確認（期待されないパターンが出現した）
    assert result.is_accepted is False

    # 期待されないパターンが含まれていない場合（期待通り）
    result = match_service.execute(
        content_string="A B C",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 3  # A, B, C
    assert result.count_nonmatched_tokens() == 3  # X, Y, Z

    # is_acceptedの確認（期待されないパターンが出現しない）
    assert result.is_accepted is True


def test_unexpected_pattern_nonmatching_1(match_service, test_config_options):
    """期待されないパターンがマッチングしない場合のテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="Hello", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="World", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=2, is_expected=False, text="#", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=3, is_expected=True, text="!", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    # ERRORがHelloとWorldの間に含まれている場合（期待通り）
    result = match_service.execute(
        content_string="Hello#World!",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 3  # Hello, World, !
    assert result.count_nonmatched_tokens() == 1  # ERROR
    assert result.is_accepted is True

    # ERRORがWorldと!の間に含まれている（期待と異なる）
    result = match_service.execute(
        content_string="HelloWorld#!",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 4  # Hello, World, #, !
    assert result.count_nonmatched_tokens() == 0

    assert result.is_accepted is False


def test_unexpected_pattern_nonmatching_2(match_service, test_config_options):
    """期待されないパターンがマッチングしない場合のテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="A", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="1", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=2, is_expected=False, text="X", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=3, is_expected=True, text="B", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=4, is_expected=True, text="2", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    # 期待通り
    result = match_service.execute(
        content_string="A: 1\nB: 2",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 4  # A, 1, 2, 3
    assert result.count_nonmatched_tokens() == 1  # X

    assert result.is_accepted is True

    # 期待と異なる
    result = match_service.execute(
        content_string="A: 1\nX\nB: 2",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 5  # A, 1, X, B, 2
    assert result.count_nonmatched_tokens() == 0

    assert result.is_accepted is False


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
    assert result.count_matched_tokens() == 0
    assert result.count_nonmatched_tokens() == 2

    # is_acceptedの確認（期待されるパターンがマッチしない）
    assert result.is_accepted is False


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

    assert result.count_matched_tokens() == 2
    assert result.count_nonmatched_tokens() == 0

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


# noinspection DuplicatedCode
def test_asterisk_pattern_matching_1(match_service, test_config_options):
    """アスタリスクパターンのマッチングテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="*", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="**", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    # 連続したアスタリスクのケース
    result = match_service.execute(
        content_string="***",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 2
    assert result.count_nonmatched_tokens() == 0

    # 最初のパターン（*）のマッチ確認
    first_token = result.matched_tokens[0]
    assert first_token.pattern.index == 0
    assert first_token.begin == 0
    assert first_token.end == 1

    # 2番目のパターン（**）のマッチ確認
    second_token = result.matched_tokens[1]
    assert second_token.pattern.index == 1
    assert second_token.begin == 1
    assert second_token.end == 3

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


# noinspection DuplicatedCode
def test_asterisk_pattern_matching_2(match_service, test_config_options):
    """アスタリスクパターンのマッチングテスト"""
    patterns = PatternList([
        TextPattern(index=0, is_expected=True, text="*", is_multiple_space_ignored=True,
                    is_word=False),
        TextPattern(index=1, is_expected=True, text="**", is_multiple_space_ignored=True,
                    is_word=False),
    ])

    # 改行を含むケース
    result = match_service.execute(
        content_string="*\n**",
        patterns=patterns,
        test_config_options=test_config_options,
    )

    assert result.count_matched_tokens() == 2
    assert result.count_nonmatched_tokens() == 0

    # 最初のパターン（*）のマッチ確認
    first_token = result.matched_tokens[0]
    assert first_token.pattern.index == 0
    assert first_token.begin == 0
    assert first_token.end == 1

    # 2番目のパターン（**）のマッチ確認
    second_token = result.matched_tokens[1]
    assert second_token.pattern.index == 1
    assert second_token.begin == 2
    assert second_token.end == 4

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


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
    assert result.count_matched_tokens() == 2
    assert result.count_nonmatched_tokens() == 0

    # is_acceptedの確認（すべて期待されるパターンがマッチ）
    assert result.is_accepted is True


def test_execution_time_recording(match_service, test_config_options):
    """実行時間の記録テスト"""
    rng = random.Random(42)

    patterns = PatternList([
        TextPattern(index=i, is_expected=True, text=rng.choice("abcd"),
                    is_multiple_space_ignored=True,
                    is_word=False)
        for i in range(10)
    ])

    result = match_service.execute(
        content_string="".join(rng.choice("abc") for _ in range(60)),
        patterns=patterns,
        test_config_options=test_config_options,
    )
    print(result.is_accepted)

    # 実行時間が記録されていることを確認
    assert isinstance(result.test_execution_timedelta, timedelta)
    assert result.test_execution_timedelta.total_seconds() > 0

    # is_acceptedの確認（実行時間テストなので結果は問わない）
    assert isinstance(result.is_accepted, bool)
