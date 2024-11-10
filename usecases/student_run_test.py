import copy
import itertools
import re
import sys
from functools import cache, lru_cache
from pprint import pprint
from typing import NamedTuple, Iterator

import unicodedata

from domain.errors import TestServiceError
from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.expected_token import TextExpectedToken, FloatExpectedToken, ExpectedTokenList, \
    AbstractExpectedToken
from domain.models.output_file import OutputFile
from domain.models.output_file_test_result import NonmatchedToken, MatchedToken
from domain.models.output_file_test_result import OutputFileTestResult
from domain.models.stages import ExecuteStage
from domain.models.student_stage_result import TestFailureStudentStageResult, \
    TestSuccessStudentStageResult, TestResultOutputFileMapping, ExecuteSuccessStudentStageResult
from domain.models.test_config_options import TestConfigOptions
from domain.models.test_result_output_file_entry import TestResultTestedOutputFileEntry, \
    AbstractTestResultOutputFileEntry, TestResultAbsentOutputFileEntry, \
    TestResultUnexpectedOutputFileEntry
from domain.models.values import FileID
from domain.models.values import StudentID, TestCaseID
from infra.repositories.student_stage_result import StudentStageResultRepository
from services.testcase_config import TestCaseConfigGetTestConfigMtimeService, \
    TestCaseConfigGetService
from utils.app_logging import create_logger


class _MatchRange(NamedTuple):
    begin: int
    end: int


@lru_cache(maxsize=1 << 20)
def _zen_to_han_char(ch: str):
    ch_converted = unicodedata.normalize("NFKC", ch)
    if len(ch_converted) != len(ch):
        return ch
    else:
        return ch_converted


def _zen_to_han(text: str):
    return "".join(_zen_to_han_char(ch) for ch in text)


class _Matcher:
    _logger = create_logger()

    def __init__(
            self,
            *,
            content_string: str,
            expected_tokens: list[AbstractExpectedToken],
            test_config_options: TestConfigOptions,
    ):
        self._content_string = _zen_to_han(content_string)
        self._expected_tokens = []
        for i, expected_token in enumerate(expected_tokens):
            expected_token = copy.deepcopy(expected_token)
            setattr(expected_token, "additional_fields", {"index": i})
            self._expected_tokens.append(expected_token)
        self._test_config_options = test_config_options

    @classmethod
    def _create_regex(cls, query_text: str):
        query_text = _zen_to_han(query_text)
        words = re.findall(r"\S+", query_text)
        return r"\b" + r"\s+".join(re.escape(word) for word in words) + r"\b"

    @cache
    def _find_token_matches(self, expected_token: AbstractExpectedToken) \
            -> list[_MatchRange]:
        # トークン種別ごとにマッチを行う
        token_matches: list[_MatchRange] = []
        if isinstance(expected_token, TextExpectedToken):
            for m in re.finditer(
                    self._create_regex(expected_token.value),
                    self._content_string,
            ):
                token_matches.append(
                    _MatchRange(
                        begin=m.start(),
                        end=m.end(),
                    )
                )
        elif isinstance(expected_token, FloatExpectedToken):
            for m in re.finditer(
                    r"\b[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?\b",
                    self._content_string,
            ):
                value = float(m.group())
                if abs(value - expected_token.value) <= self._test_config_options.float_tolerance:
                    token_matches.append(
                        _MatchRange(
                            begin=m.start(),
                            end=m.end(),
                        )
                    )
        else:
            assert False, expected_token
        return token_matches

    @cache
    def _find_matches(self) \
            -> list[tuple[AbstractExpectedToken, list[_MatchRange]]]:
        matches: list[tuple[AbstractExpectedToken, list[_MatchRange]]] = []
        for expected_token in self._expected_tokens:
            token_matches: list[_MatchRange] = self._find_token_matches(expected_token)
            matches.append((expected_token, token_matches))
        self._logger.info(
            f"Matcher found {sum(map(lambda item: len(item[1]), matches))} matches in text"
        )
        return matches

    @cache
    def _list_match_combinations(self) \
            -> list[dict[AbstractExpectedToken, _MatchRange]]:
        matches: list[tuple[AbstractExpectedToken, list[_MatchRange]]] = self._find_matches()
        token_index_combination_it = itertools.product(
            *(
                range(-1, len(match_ranges))  # -1: unused token
                for _, match_ranges in matches
            )
        )

        total = 1
        for _, match_ranges in matches:
            total *= len(match_ranges) + 1
        self._logger.info(
            f"Matcher will iterate {total} combinations"
        )

        match_combinations = []
        for token_index_combination in token_index_combination_it:
            match_combination: dict[AbstractExpectedToken, _MatchRange] = {}
            for i, (expected_token, match_ranges) in enumerate(matches):
                token_index = token_index_combination[i]
                if token_index >= 0:
                    match_combination[expected_token] = match_ranges[token_index]
            match_combinations.append(match_combination)
        return match_combinations

    def _iter_match_combinations_no_range_wrap(self) \
            -> Iterator[dict[AbstractExpectedToken, _MatchRange]]:
        matches: list[tuple[AbstractExpectedToken, list[_MatchRange]]] = self._find_matches()
        match_ranges: set[_MatchRange] = {
            match_range
            for _, match_ranges in matches
            for match_range in match_ranges
        }
        match_range_wrap_lut: dict[tuple[_MatchRange, _MatchRange], bool] = {}
        for left in match_ranges:
            for right in match_ranges:
                match_range_wrap_lut[(left, right)] = (
                        left.begin <= right.end - 1 and right.begin <= left.end - 1
                )

        for match_combination in self._list_match_combinations():
            wrap = False
            for et_left, et_right in itertools.combinations(match_combination.keys(), 2):
                mr_left, mr_right = match_combination[et_left], match_combination[et_right]
                if match_range_wrap_lut[(mr_left, mr_right)]:
                    wrap = True
                    break
            if not wrap:
                yield match_combination

    def _iter_match_combinations_ordered(self) \
            -> Iterator[dict[AbstractExpectedToken, _MatchRange]]:
        for match_combination in self._iter_match_combinations_no_range_wrap():
            unordered = False
            # match_combinationのキー（AbstractExpectedToken）を順番に並び替える
            expected_tokens = [
                expected_token
                for expected_token in self._expected_tokens
                if expected_token in match_combination
            ]
            # 順序が正しいか検証
            for i in range(len(expected_tokens) - 1):
                et_left, et_right = expected_tokens[i], expected_tokens[i + 1]
                mr_left, mr_right = match_combination[et_left], match_combination[et_right]
                if not mr_left.end <= mr_right.begin:
                    unordered = True
                    break
            if not unordered:
                yield match_combination

    def _iter_match_combinations_unordered(self) \
            -> Iterator[dict[AbstractExpectedToken, _MatchRange]]:
        for match_combination in self._iter_match_combinations_no_range_wrap():
            yield match_combination

    def get_best_token_matches(self) -> tuple[list[MatchedToken], list[NonmatchedToken]]:
        if self._test_config_options.ordered_matching:
            it = self._iter_match_combinations_ordered()
        else:
            it = itertools.chain(
                self._iter_match_combinations_ordered(),
                self._iter_match_combinations_unordered(),
            )

        best_match_combination: dict[AbstractExpectedToken, _MatchRange] = {}
        best_match_token_count = 0
        for match_combination in it:
            match_token_count = len(match_combination)
            if best_match_token_count < match_token_count:
                best_match_combination = match_combination
                best_match_token_count = match_token_count
                # 完全マッチならすぐ終了
                if match_token_count == len(self._expected_tokens):
                    break

        matched_tokens = [
            MatchedToken(
                match_begin=match_range.begin,
                match_end=match_range.end,
                expected_token_index=getattr(expected_token, "additional_fields")["index"],
            )
            for expected_token, match_range in best_match_combination.items()
        ]
        nonmatched_tokens = [
            NonmatchedToken(
                expected_token_index=getattr(expected_token, "additional_fields")["index"],
            )
            for expected_token in self._expected_tokens
            if expected_token not in best_match_combination
        ]
        return matched_tokens, nonmatched_tokens


def test_main():
    test_config_options = TestConfigOptions(
        ordered_matching=True,
        float_tolerance=0.0001,
        allowable_edit_distance=0,
    )
    expected_output_file = ExpectedOutputFile(
        file_id=FileID.STDOUT,
        expected_tokens=ExpectedTokenList([
            TextExpectedToken("n"),
            FloatExpectedToken(1),
            TextExpectedToken("num2"),
            FloatExpectedToken(2),
            TextExpectedToken("num3"),
            FloatExpectedToken(3),
        ]),
    )
    m = _Matcher(
        content_string="ｎum1: 1 1.0000001\nnum2: 2 3\nnum3: 3",
        test_config_options=test_config_options,
        expected_tokens=expected_output_file.expected_tokens,
    )
    print(*m._iter_match_combinations_no_range_wrap(), sep="\n")
    print()
    print(*m._iter_match_combinations_ordered(), sep="\n")
    print()
    pprint(m.get_best_token_matches())


if __name__ == '__main__':
    test_main()
    sys.exit(0)


class StudentRunTestStageUseCase:  # TODO: ロジックからStudentTestServiceを分離
    def __init__(
            self,
            *,
            testcase_config_get_service: TestCaseConfigGetService,
            student_stage_result_repo: StudentStageResultRepository,
            testcase_config_get_test_config_mtime_service: TestCaseConfigGetTestConfigMtimeService,
    ):
        self._testcase_config_get_service = testcase_config_get_service
        self._student_stage_result_repo = student_stage_result_repo
        self._testcase_config_get_test_config_mtime_service = testcase_config_get_test_config_mtime_service

    def execute(self, student_id: StudentID, testcase_id: TestCaseID) -> None:
        try:
            # 実行結果を取得する
            if not self._student_stage_result_repo.exists(
                    student_id=student_id,
                    stage=ExecuteStage(testcase_id=testcase_id),
            ):
                raise TestServiceError(
                    reason="実行結果が見つかりません",
                )
            execute_result = self._student_stage_result_repo.get(
                student_id=student_id,
                stage=ExecuteStage(testcase_id=testcase_id),
            )
            if not execute_result.is_success:
                raise TestServiceError(
                    reason="失敗した実行のテストはできません",
                )
            assert isinstance(execute_result, ExecuteSuccessStudentStageResult)

            # テストケースのテスト構成を読み込む
            test_config = self._testcase_config_get_service.execute(
                testcase_id=testcase_id,
            ).test_config

            # テストの実行 - それぞれの出力ファイルについてテストを実行する
            output_file_id_test_result_mapping: dict[FileID, AbstractTestResultOutputFileEntry] = {}
            # v 正解
            expected_output_file_ids: set[FileID] = set(test_config.expected_output_files.keys())
            # v 実行結果
            actual_output_file_ids: set[FileID] = set(execute_result.output_files.keys())
            for file_id in expected_output_file_ids | actual_output_file_ids:
                expected_output_file: ExpectedOutputFile | None \
                    = test_config.expected_output_files.get(file_id)
                # ^ None if not found
                actual_output_file: OutputFile | None \
                    = execute_result.output_files.get(file_id)
                # ^ None if not found

                # # 実行結果にファイルが存在する場合，その内容を文字列に変換できなかったらエラー
                # if actual_output_file is not None:
                #     if actual_output_file.content_string is None:
                #         raise TestServiceError(
                #             reason=f"出力ファイル{actual_output_file.file_id!s}の文字コードが不明です",
                #         )

                if actual_output_file is not None and expected_output_file is None:
                    # 実行結果には含まれているがテストケースにはない出力ファイル
                    file_test_result = TestResultUnexpectedOutputFileEntry(
                        file_id=file_id,
                        actual=actual_output_file,
                    )
                elif actual_output_file is None and expected_output_file is not None:
                    # 実行結果には含まれていないがテストケースで出力が期待されているファイル
                    file_test_result = TestResultAbsentOutputFileEntry(
                        file_id=file_id,
                        expected=expected_output_file,
                    )
                elif actual_output_file is not None and expected_output_file is not None:
                    # 実行結果とテストケースの両方に含まれているファイル
                    #  -> テストを行う
                    matched_tokens, nonmatched_tokens = (
                        _Matcher(
                            content_string=actual_output_file.content_string,
                            test_config_options=test_config.options,
                            expected_tokens=expected_output_file.expected_tokens,
                        ).get_best_token_matches()
                    )
                    file_test_result = TestResultTestedOutputFileEntry(
                        file_id=file_id,
                        actual=actual_output_file,
                        expected=expected_output_file,
                        test_result=OutputFileTestResult(
                            matched_tokens=matched_tokens,
                            nonmatched_tokens=nonmatched_tokens,
                        ),
                    )
                else:
                    assert False, "unreachable"
                output_file_id_test_result_mapping[file_id] = file_test_result

            # すべての出力ファイルの結果を生成
            test_result_output_files = TestResultOutputFileMapping(
                output_file_id_test_result_mapping
            )
        except TestServiceError as e:
            self._student_stage_result_repo.put(
                result=TestFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    reason=e.reason,
                )
            )
        else:
            test_config_mtime = self._testcase_config_get_test_config_mtime_service.execute(
                testcase_id=testcase_id,
            )  # TODO: UoWの導入
            self._student_stage_result_repo.put(
                result=TestSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    test_config_mtime=test_config_mtime,
                    test_result_output_files=test_result_output_files,
                )
            )
