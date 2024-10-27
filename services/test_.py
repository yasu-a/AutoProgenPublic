# import re
# from typing import Iterable, NamedTuple
#
# from Levenshtein import distance as edit_distance
# from scipy.sparse.csgraph import maximum_bipartite_matching
#
# from domain.errors import TestServiceError
# from domain.models.expected_ouput_file import ExpectedOutputFile
# from domain.models.expected_token import AbstractExpectedToken, TextExpectedToken, \
#     FloatExpectedToken
# from domain.models.student_stage_result import MatchedToken, NonmatchedToken, OutputFileTestResult, \
#     OutputFileTestResultMapping, TestCaseTestResult, TestCaseTestResultMapping, \
#     TestStudentStageResult
# from domain.models.test_config_options import TestConfigOptions
# from domain.models.values import StudentID, TestCaseID, FileID
# from files.project import ProjectIO
# from files.repositories.student_stage_result import ProgressIO
# from files.testcase_config import TestCaseIO
#
#
# class _Token(NamedTuple):
#     text: str
#     begin: int
#     end: int  # end: exclusive
#
#
# def _tokenize(string: str) -> list[_Token]:
#     def iter_token_begin_and_end() -> Iterable[tuple[int, int]]:
#         begin = 0
#         for m in re.finditer(r"\s+", string):
#             end = m.start()
#             yield begin, end
#             begin = m.end()
#         yield begin, len(string)
#
#     def tokenize():
#         tokens = []
#         for begin, end in iter_token_begin_and_end():
#             token = _Token(string[begin:end], begin, end)
#             tokens.append(token)
#         return tokens
#
#     return tokenize()
#
#
# def _is_matched(
#         token: _Token,
#         expected_token: AbstractExpectedToken,
#         allowable_edit_distance: int,
#         float_tolerance: float,
# ) -> bool:
#     # TODO: 何らかのクラスのポリモーフィズムを使え
#     if isinstance(expected_token, TextExpectedToken):
#         if allowable_edit_distance == 0:
#             return token.text == expected_token.value
#         else:
#             return edit_distance(token.text, expected_token.value) <= allowable_edit_distance
#     elif isinstance(expected_token, FloatExpectedToken):
#         try:
#             token_float = float(token.text)
#         except ValueError:
#             return False
#         return abs(token_float - expected_token.value) < float_tolerance
#     else:
#         assert False, expected_token
#
#
# def _get_token_lcs(match_table: list) \
#         -> tuple[list[int], list[int]]:  # list of matched token/expected_token indexes
#     # longest common subsequence for list of token
#     # https://qiita.com/tetsuro731/items/bc9fb99683337ae7dc2e
#     n_tokens = len(match_table)
#     n_expected_tokens = len(match_table[0])
#
#     dp = [[0] * (n_expected_tokens + 1) for _ in range(n_tokens + 1)]
#
#     for i in range(n_tokens):
#         for j in range(n_expected_tokens):
#             if match_table[i][j]:
#                 dp[i + 1][j + 1] = dp[i][j] + 1
#             else:
#                 dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])
#
#     matched_token_index_lst = []
#     matched_expected_token_index_lst = []
#     i = n_tokens - 1
#     j = n_expected_tokens - 1
#
#     while i >= 0 and j >= 0:
#         if match_table[i][j]:
#             matched_token_index_lst.append(i)
#             matched_expected_token_index_lst.append(j)
#             i -= 1
#             j -= 1
#         elif dp[i + 1][j + 1] == dp[i][j + 1]:
#             i -= 1
#         elif dp[i + 1][j + 1] == dp[i + 1][j]:
#             j -= 1
#
#     return (
#         list(reversed(matched_token_index_lst)),
#         list(reversed(matched_expected_token_index_lst)),
#     )
#
#
# class TestService:
#     def __init__(self, *, project_io: ProjectIO, progress_io: ProgressIO, testcase_io: TestCaseIO):
#         self._project_io = project_io
#         self._progress_io = progress_io
#         self._testcase_io = testcase_io
#
#     @classmethod
#     def _test_output_file_content_and_get_token_matches(
#             cls,
#             *,
#             content_string: str,
#             test_config_options: TestConfigOptions,
#             expected_output_file: ExpectedOutputFile,
#     ) -> tuple[list[MatchedToken], list[NonmatchedToken]]:
#         token_lst: list[_Token] = _tokenize(content_string)
#
#         # トークンを比較してマッチテーブルを作成
#         match_table = []  # [index of token, index of expected_token]
#         for token in token_lst:
#             match_table.append([])
#             for expected_token in expected_output_file.expected_tokens:
#                 is_matched = _is_matched(
#                     token=token,
#                     expected_token=expected_token,
#                     allowable_edit_distance=test_config_options.allowable_edit_distance,
#                     float_tolerance=test_config_options.float_tolerance,
#                 )
#                 match_table[-1].append(is_matched)
#
#         if test_config_options.ordered_matching:
#             token_indexes, expected_token_indexes = _get_token_lcs(match_table)
#         else:
#             token_indexes = list(range(len(token_lst)))
#             expected_token_indexes = list(
#                 maximum_bipartite_matching(match_table, perm_type='column')  # 2部グラフの最大マッチング問題
#             )
#             assert len(token_indexes) == len(expected_token_indexes)
#
#             # マッチしないインデックスは-1になるので対応するインデックスとともにpopする
#             for i in reversed(range(len(token_indexes))):
#                 if expected_token_indexes[i] == -1:
#                     token_indexes.pop(i)
#                     expected_token_indexes.pop(i)
#
#         matched_tokens = [
#             MatchedToken(
#                 match_begin=token_lst[i_token].begin,
#                 match_end=token_lst[i_token].end,
#                 expected_token_index=i_expected_token,
#             )
#             for i_token, i_expected_token in zip(
#                 token_indexes,
#                 expected_token_indexes,
#             )
#         ]
#         nonmatched_tokens = [
#             NonmatchedToken(
#                 expected_token_index=i_expected_token,
#             )
#             for i_expected_token in range(len(expected_output_file.expected_tokens))
#             if i_expected_token not in expected_token_indexes
#         ]
#
#         return matched_tokens, nonmatched_tokens
#
#     def _test_output_files_and_get_results(self, student_id: StudentID, testcase_id: TestCaseID) \
#             -> OutputFileTestResultMapping:
#         # 実行結果を取得する
#         with self._progress_io.with_student(student_id) as student_progress_io:
#             execute_result = student_progress_io.read_execute_result()
#
#         # テストケースの構成を読んで必要なフィールドを取り出す
#         testcase_config = self._testcase_io.read_config(
#             testcase_id=testcase_id,
#         )
#         test_config = testcase_config.test_config
#         test_config_options = test_config.options
#         expected_output_files = test_config.expected_output_files
#         expected_output_file_ids = expected_output_files.keys()
#
#         # それぞれの出力ファイルについてテストを実行する
#         testcase_execute_result = execute_result.testcase_results[testcase_id]
#         output_file_id_test_result_mapping: dict[FileID, OutputFileTestResult] = {}
#         for expected_output_file_id in expected_output_file_ids:
#             # 実行結果の出力ファイルを取得
#             output_file = testcase_execute_result.output_files.get(expected_output_file_id)
#             # 実行結果に出力がファイルが見つからなかったらエラー
#             if output_file is None:
#                 raise TestServiceError(
#                     reason=f"出力ファイル{expected_output_file_id.deployment_relative_path!s}が実行結果に見つかりません",
#                 )
#             # 出力ファイルの内容を文字列に変換できなかったらエラー
#             if output_file.content_string is None:
#                 raise TestServiceError(
#                     reason=f"出力ファイル{output_file.file_id.deployment_relative_path!s}の文字コードが不明です",
#                 )
#             # テストケースと照合
#             matched_tokens, nonmatched_tokens = (
#                 self._test_output_file_content_and_get_token_matches(
#                     content_string=output_file.content_string,
#                     test_config_options=test_config_options,
#                     expected_output_file=expected_output_files[expected_output_file_id],
#                 )
#             )
#             # 照合結果を記録
#             output_file_id_test_result_mapping[expected_output_file_id] = OutputFileTestResult(
#                 file_id=expected_output_file_id,
#                 matched_tokens=matched_tokens,
#                 nonmatched_tokens=nonmatched_tokens,
#             )
#
#         return OutputFileTestResultMapping(output_file_id_test_result_mapping)
#
#     def test_and_save_result(self, student_id: StudentID) -> None:
#         testcase_test_results: dict[TestCaseID, TestCaseTestResult] = {}
#         testcase_id_lst = self._testcase_io.list_ids()
#         if not testcase_id_lst:
#             result = TestStudentStageResult.error(
#                 reason="実行可能なテストケースがありません",
#             )
#         else:
#             for testcase_id in testcase_id_lst:
#                 try:
#                     output_files = self._test_output_files_and_get_results(
#                         student_id=student_id,
#                         testcase_id=testcase_id,
#                     )
#                 except TestServiceError as e:
#                     testcase_test_results[testcase_id] = TestCaseTestResult.error(
#                         testcase_id=testcase_id,
#                         test_config_mtime=(
#                             self._testcase_io.get_test_config_mtime(testcase_id)  # TODO: UoWの導入
#                         ),
#                         reason=e.reason,
#                     )
#                 else:
#                     testcase_test_results[testcase_id] = TestCaseTestResult.success(
#                         testcase_id=testcase_id,
#                         test_config_mtime=(
#                             self._testcase_io.get_test_config_mtime(testcase_id)  # TODO: UoWの導入
#                         ),
#                         output_file_test_results=output_files,
#                     )
#
#             # FIXME: 常に成功する
#             #        --------------------------------------------------------------------
#             #        ExecuteStageが失敗すると次のステージに進めないため常に成功するようになっている
#             #        ステージを生徒ID-ステージID-テストケースIDで細分化する
#             result = TestStudentStageResult.success(
#                 testcase_results=TestCaseTestResultMapping(
#                     testcase_test_results,
#                 )
#             )
#
#         with self._progress_io.with_student(student_id) as student_progress_io:
#             student_progress_io.write_test_result(
#                 result=result,
#             )
