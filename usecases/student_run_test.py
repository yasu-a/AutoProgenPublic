import re
from typing import Iterable, NamedTuple

from Levenshtein import distance as edit_distance
from scipy.sparse.csgraph import maximum_bipartite_matching

from domain.errors import TestServiceError
from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.expected_token import AbstractExpectedToken, TextExpectedToken
from domain.models.expected_token import FloatExpectedToken
from domain.models.output_file import OutputFile
from domain.models.output_file_test_result import MatchedToken, NonmatchedToken, \
    OutputFileTestResult
from domain.models.stages import ExecuteStage
from domain.models.student_stage_result import TestFailureStudentStageResult, \
    TestSuccessStudentStageResult, TestResultOutputFileMapping, ExecuteSuccessStudentStageResult
from domain.models.test_config_options import TestConfigOptions
from domain.models.test_result_output_file_entry import TestResultTestedOutputFileEntry, \
    AbstractTestResultOutputFileEntry, TestResultAbsentOutputFileEntry, \
    TestResultUnexpectedOutputFileEntry
from domain.models.values import StudentID, TestCaseID, FileID
from infra.repositories.student_stage_result import StudentStageResultRepository
from services.testcase_config import TestCaseConfigGetTestConfigMtimeService, \
    TestCaseConfigGetService


class _Token(NamedTuple):
    text: str
    begin: int
    end: int  # end: exclusive


def _tokenize(string: str) -> list[_Token]:
    def iter_token_begin_and_end() -> Iterable[tuple[int, int]]:
        begin = 0
        for m in re.finditer(r"\s+", string):
            end = m.start()
            yield begin, end
            begin = m.end()
        yield begin, len(string)

    def tokenize():
        tokens = []
        for begin, end in iter_token_begin_and_end():
            token = _Token(string[begin:end], begin, end)
            tokens.append(token)
        return tokens

    return tokenize()


def _is_matched(
        token: _Token,
        expected_token: AbstractExpectedToken,
        allowable_edit_distance: int,
        float_tolerance: float,
) -> bool:
    # TODO: 何らかのクラスのポリモーフィズムを使え
    if isinstance(expected_token, TextExpectedToken):
        if allowable_edit_distance == 0:
            return token.text == expected_token.value
        else:
            return edit_distance(token.text, expected_token.value) <= allowable_edit_distance
    elif isinstance(expected_token, FloatExpectedToken):
        try:
            token_float = float(token.text)
        except ValueError:
            return False
        return abs(token_float - expected_token.value) < float_tolerance
    else:
        assert False, expected_token


def _get_token_lcs(match_table: list) \
        -> tuple[list[int], list[int]]:  # list of matched token/expected_token indexes
    # longest common subsequence for list of token
    # https://qiita.com/tetsuro731/items/bc9fb99683337ae7dc2e
    n_tokens = len(match_table)
    n_expected_tokens = len(match_table[0])

    dp = [[0] * (n_expected_tokens + 1) for _ in range(n_tokens + 1)]

    for i in range(n_tokens):
        for j in range(n_expected_tokens):
            if match_table[i][j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])

    matched_token_index_lst = []
    matched_expected_token_index_lst = []
    i = n_tokens - 1
    j = n_expected_tokens - 1

    while i >= 0 and j >= 0:
        if match_table[i][j]:
            matched_token_index_lst.append(i)
            matched_expected_token_index_lst.append(j)
            i -= 1
            j -= 1
        elif dp[i + 1][j + 1] == dp[i][j + 1]:
            i -= 1
        elif dp[i + 1][j + 1] == dp[i + 1][j]:
            j -= 1

    return (
        list(reversed(matched_token_index_lst)),
        list(reversed(matched_expected_token_index_lst)),
    )


def test_output_file_content_and_get_token_matches(
        *,
        content_string: str,
        test_config_options: TestConfigOptions,
        expected_output_file: ExpectedOutputFile,
) -> tuple[list[MatchedToken], list[NonmatchedToken]]:
    token_lst: list[_Token] = _tokenize(content_string)

    # トークンを比較してマッチテーブルを作成
    match_table = []  # [index of token, index of expected_token]
    for token in token_lst:
        match_table.append([])
        for expected_token in expected_output_file.expected_tokens:
            is_matched = _is_matched(
                token=token,
                expected_token=expected_token,
                allowable_edit_distance=test_config_options.allowable_edit_distance,
                float_tolerance=test_config_options.float_tolerance,
            )
            match_table[-1].append(is_matched)

    if test_config_options.ordered_matching:
        token_indexes, expected_token_indexes = _get_token_lcs(match_table)
    else:
        token_indexes = list(range(len(token_lst)))
        expected_token_indexes = list(
            maximum_bipartite_matching(match_table, perm_type='column')  # 2部グラフの最大マッチング問題
        )
        assert len(token_indexes) == len(expected_token_indexes)

        # マッチしないインデックスは-1になるので対応するインデックスとともにpopする
        for i in reversed(range(len(token_indexes))):
            if expected_token_indexes[i] == -1:
                token_indexes.pop(i)
                expected_token_indexes.pop(i)

    matched_tokens = [
        MatchedToken(
            match_begin=token_lst[i_token].begin,
            match_end=token_lst[i_token].end,
            expected_token_index=i_expected_token,
        )
        for i_token, i_expected_token in zip(
            token_indexes,
            expected_token_indexes,
        )
    ]
    nonmatched_tokens = [
        NonmatchedToken(
            expected_token_index=i_expected_token,
        )
        for i_expected_token in range(len(expected_output_file.expected_tokens))
        if i_expected_token not in expected_token_indexes
    ]

    return matched_tokens, nonmatched_tokens


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

                # 実行結果にファイルが存在する場合，その内容を文字列に変換できなかったらエラー
                if actual_output_file is not None:
                    if actual_output_file.content_string is None:
                        raise TestServiceError(
                            reason=f"出力ファイル{actual_output_file.file_id!s}の文字コードが不明です",
                        )

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
                        test_output_file_content_and_get_token_matches(
                            content_string=actual_output_file.content_string,
                            test_config_options=test_config.options,
                            expected_output_file=expected_output_file,
                        )
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
