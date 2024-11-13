import copy
import itertools
from functools import cache
from typing import Iterator

from domain.models.output_file_test_result import NonmatchedToken, MatchedToken
from domain.models.pattern import AbstractPattern, MatchRange, MatchSource, PatternMatchOptions
from domain.models.test_config_options import TestConfigOptions
from services.dto.match_result import MatchServiceResult
from utils.app_logging import create_logger
from utils.zen_han import zen_to_han


class _Matcher:
    _logger = create_logger()

    def __init__(
            self,
            *,
            content_string: str,
            patterns: list[AbstractPattern],
            test_config_options: TestConfigOptions,
    ):
        self._content_string = zen_to_han(content_string)
        self._patterns: list[AbstractPattern] = []
        for i, pattern in enumerate(patterns):
            pattern = copy.deepcopy(pattern)
            self._patterns.append(pattern)
        self._test_config_options = test_config_options

    @cache
    def _find_token_matches(self, pattern: AbstractPattern) \
            -> list[MatchRange]:
        # トークン種別ごとにマッチを行ってすべてのマッチ箇所を返す
        return pattern.find_matches(
            source=MatchSource(
                source_text=self._content_string,
            ),
            options=PatternMatchOptions(
                float_tolerance=self._test_config_options.float_tolerance,
            ),
        )

    @cache
    def _find_matches(self) \
            -> list[tuple[AbstractPattern, list[MatchRange]]]:
        # すべてのパターンに対してすべてのマッチ箇所を見つける
        matches: list[tuple[AbstractPattern, list[MatchRange]]] = []
        for pattern in self._patterns:
            pattern: AbstractPattern
            token_matches: list[MatchRange] = self._find_token_matches(pattern)
            matches.append((pattern, token_matches))
        self._logger.info(
            f"Matcher found {sum(map(lambda item: len(item[1]), matches))} matches in text"
        )
        return matches

    @cache
    def _list_ordered_match_combinations(self) \
            -> list[dict[AbstractPattern, MatchRange]]:
        # すべてのパターンに対するすべてのマッチ箇所について，マッチ箇所のいずれかを取るか一つも取らないかの組み合わせを見つける

        # すべてのパターンに対してすべてのマッチ箇所を見つける
        matches: list[tuple[AbstractPattern, list[MatchRange]]] = self._find_matches()

        # 順序付けられたマッチ範囲を持つマッチ箇所の組み合わせを生成する再帰ジェネレータ
        def iter_index_combinations(index_combination: tuple[int, ...] = (), prev_match_end=0):
            if len(index_combination) == len(matches):
                yield index_combination
            else:
                head = len(index_combination)
                for index in range(-1, len(matches[head][1])):  # -1: unused token
                    new_prev_match_end = prev_match_end
                    if index >= 0:  # valid index of list[MatchRange]
                        match_range: MatchRange = matches[head][1][index]
                        # マッチ位置が前に戻るならスキップ
                        if prev_match_end > match_range.begin:
                            continue
                        new_prev_match_end = match_range.end
                    yield from iter_index_combinations(
                        index_combination + (index,),
                        prev_match_end=new_prev_match_end,
                    )

        # マッチ箇所の組み合わせを返す
        match_combinations = []
        for token_index_combination in iter_index_combinations():
            match_combination: dict[AbstractPattern, MatchRange] = {}
            for i, (pattern, match_ranges) in enumerate(matches):
                token_index = token_index_combination[i]
                if token_index >= 0:  # valid index of list[MatchRange]
                    match_combination[pattern] = match_ranges[token_index]
            match_combinations.append(match_combination)

        self._logger.info(
            f"Matcher found {len(match_combinations)} match-combinations"
        )

        return match_combinations

    def _iter_match_combinations_no_range_wrap(self) \
            -> Iterator[dict[AbstractPattern, MatchRange]]:
        # マッチの組み合わせから範囲が重複するものを取り除く

        # 任意の2つの範囲どうしが重複しているかどうかのルックアップテーブルを作る
        matches: list[tuple[AbstractPattern, list[MatchRange]]] = self._find_matches()
        match_ranges: set[MatchRange] = {
            match_range
            for _, match_ranges in matches
            for match_range in match_ranges
        }
        match_range_wrap_lut: dict[tuple[MatchRange, MatchRange], bool] = {}
        for left in match_ranges:
            for right in match_ranges:
                match_range_wrap_lut[(left, right)] = (
                        left.begin <= right.end - 1 and right.begin <= left.end - 1
                )

        # 範囲が重複しない組み合わせのみをyieldする
        for match_combination in self._list_ordered_match_combinations():
            wrap = False
            for et_left, et_right in itertools.combinations(match_combination.keys(), 2):
                mr_left, mr_right = match_combination[et_left], match_combination[et_right]
                if match_range_wrap_lut[(mr_left, mr_right)]:
                    wrap = True
                    break
            if not wrap:
                yield match_combination

    @classmethod
    def _calculate_match_score(cls, match_combination: dict[AbstractPattern, MatchRange]) \
            -> tuple[int, ...]:
        # マッチングのスコアを計算する
        #  - 第1スコア（最優先）：マッチしたパターンの数
        #  - 第2スコア：マッチした部分文字列の長さの総和
        # このスコアは大きいほどよい
        match_count = len(match_combination)
        match_length = sum(match_range.length for match_range in match_combination.values())
        return match_count, match_length

    def get_best_token_matches(self) -> MatchServiceResult:
        # もっともよいマッチを探索して，マッチしたトークンの集合とマッチしないトークンの集合を返す
        it = self._iter_match_combinations_no_range_wrap()

        best_match_combination: dict[AbstractPattern, MatchRange] | None = None
        best_score = None
        for match_combination in it:
            match_combination: dict[AbstractPattern, MatchRange]
            score = self._calculate_match_score(match_combination)

            if best_score is None or best_score < score:
                best_match_combination = match_combination
                best_score = score

        return MatchServiceResult(
            matched_tokens=[
                MatchedToken(
                    begin=match_range.begin,
                    end=match_range.end,
                    pattern=pattern,
                )
                for pattern, match_range in best_match_combination.items()
            ],
            nonmatched_tokens=[
                NonmatchedToken(
                    pattern=pattern,
                )
                for pattern in self._patterns
                if pattern not in best_match_combination
            ],
        )


class MatchGetBestService:
    def __init__(self):
        pass

    @classmethod
    def execute(
            cls,
            *,
            content_string: str,
            patterns: list[AbstractPattern],
            test_config_options: TestConfigOptions,
    ) -> MatchServiceResult:
        return _Matcher(
            content_string=content_string,
            patterns=patterns,
            test_config_options=test_config_options,
        ).get_best_token_matches()
