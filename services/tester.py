import re
import subprocess

# from models.student import Student
from domain.models.testcase import TestCase, TestCaseResultState


class TesterError(ValueError):
    def __init__(self, result_state: TestCaseResultState):
        self.result_state = result_state


class ExecutableRunnerTimeoutError(ValueError):
    pass


class ExecutableRunner:
    def __init__(self, *, executable_fullpath: str, timeout: float, input_string: str | None):
        self.__executable_fullpath = executable_fullpath
        self.__timeout = timeout
        self.__input_string = input_string
        # self.__encoding = "utf-8"

    def run(self) -> list[str]:
        with subprocess.Popen(
                args=[self.__executable_fullpath],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
        ) as p:
            input_string = self.__input_string if self.__input_string else None
            try:
                stdout_text, stderr_text = p.communicate(
                    input=input_string,
                    timeout=self.__timeout,
                )
            except subprocess.TimeoutExpired:
                p.terminate()
                raise ExecutableRunnerTimeoutError()
            else:
                assert stderr_text is None, stderr_text
                output_lines: list[str] = stdout_text.split("\n")
                return output_lines
        #     if self.__input_string:
        #         # p.stdin.write(self.__input_string.encode(self.__encoding))
        #         p.stdin.write(self.__input_string)
        #     try:
        #         p.wait(timeout=self.__timeout)
        #     except subprocess.TimeoutExpired:
        #         raise ExecutableRunnerTimeoutError()
        #     # output_lines: list[bytes] = p.stdout.readlines()
        #     output_lines: list[str] = "".join(p.stdout.readlines()).split("\n")
        #     p.kill()
        # # output_lines_decoded = [
        # #     line.decode(self.__encoding)
        # #     for line in output_lines
        # # ]
        # # return output_lines_decoded
        # return output_lines


# https://stackoverflow.com/questions/2460177/edit-distance-in-python
def levenshtein_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


class TestCaseOutputComparator:
    def __init__(self, testcase: TestCase):
        self.__testcase = testcase
        self.__config = testcase.config

    @classmethod
    def process_spaces_start_of_line(cls, lines: list[str]) -> list[str]:
        return [
            line.lstrip()
            for line in lines
        ]

    @classmethod
    def process_spaces_end_of_line(cls, lines: list[str]) -> list[str]:
        return [
            line.rstrip()
            for line in lines
        ]

    @classmethod
    def process_multiple_spaces_between_words(cls, lines: list[str]) -> list[str]:
        return [
            re.sub(r"\b\s+\b", " ", line)
            for line in lines
        ]

    @classmethod
    def process_empty_lines(cls, lines: list[str]) -> list[str]:
        return [
            line
            for line in lines
            if line.strip()
        ]

    @classmethod
    def process_letter_case_difference(cls, lines: list[str]) -> list[str]:
        return [
            line.lower()
            for line in lines
        ]

    @classmethod
    def compare_lines_with_levenshtein_distance(
            cls, lines_left: list[str], lines_right: list[str], max_distance: int
    ):
        if len(lines_left) != len(lines_right):
            return False
        for lines_left, line_right in zip(lines_left, lines_right):
            if levenshtein_distance(lines_left, line_right) > max_distance:
                return False
        return True

    def process_lines_with_testcase_config(self, lines: list[str]) -> list[str]:
        if self.__config.allow_spaces_start_of_line:
            lines = self.process_spaces_start_of_line(lines)
        if self.__config.allow_spaces_end_of_line:
            lines = self.process_spaces_end_of_line(lines)
        if self.__config.allow_multiple_spaces_between_words:
            lines = self.process_multiple_spaces_between_words(lines)
        if self.__config.allow_empty_lines:
            lines = self.process_empty_lines(lines)
        if self.__config.allow_letter_case_difference:
            lines = self.process_letter_case_difference(lines)
        return lines

    def compare_lines_with_testcase_config(self, lines_left: list[str], lines_right: list[str]) \
            -> bool:
        return self.compare_lines_with_levenshtein_distance(
            lines_left=lines_left,
            lines_right=lines_right,
            max_distance=self.__config.allowable_line_levenshtein_distance,
        )

    def compare_with(self, actual_output_lines: list[str]) -> bool:
        actual_output_lines = self.process_lines_with_testcase_config(
            actual_output_lines
        )
        expected_output_lines = self.process_lines_with_testcase_config(
            self.__testcase.expected_output_lines
        )
        return self.compare_lines_with_testcase_config(
            lines_left=actual_output_lines,
            lines_right=expected_output_lines,
        )

#
# class StudentEnvironmentTester:
#     def __init__(self, env_io: "EnvironmentIO", testcase_io: "TestCaseIO"):
#         self.__env_io = env_io
#         self.__testcase_io = testcase_io
#
#     def run_executable_of_student(self, student: Student, target_index: int, testcase: TestCase) \
#             -> list[str]:
#         entry_source = student.env_meta.get_env_entry_by_label_and_number(
#             label=EnvEntryLabel.SOURCE_MAIN,
#             number=target_index,
#         )
#         if entry_source is None:  # ソースがない（未提出？）
#             raise TesterError(
#                 result_state=TestCaseResultState.NO_BUILD_FOUND,
#             )
#
#         executable_fullpath = self.__env_io.get_student_env_executable_fullpath(
#             student_id=student.meta.student_id,
#             item_name=entry_source.path,
#         )
#         if executable_fullpath is None:  # ソースはあるけど実行ファイルがない（コンパイル失敗？）
#             raise TesterError(
#                 result_state=TestCaseResultState.NO_BUILD_FOUND,
#             )
#
#         runner = ExecutableRunner(
#             executable_fullpath=executable_fullpath,
#             timeout=testcase.config.timeout,
#             input_string=testcase.expected_input,
#         )
#
#         try:
#             output_lines = runner.run()
#         except ExecutableRunnerTimeoutError:
#             raise TesterError(
#                 result_state=TestCaseResultState.EXECUTION_TIMEOUT,
#             )
#         return output_lines
#
#     def run_testcase_on_student(self, student: Student, target_index: int, testcase: TestCase) \
#             -> TestCaseResult:
#         try:
#             actual_output_lines = self.run_executable_of_student(student, target_index, testcase)
#         except TesterError as e:
#             result = TestCaseResult(
#                 testcase=copy.deepcopy(testcase),
#                 actual_output_lines=None,
#                 result_state=e.result_state,
#             )
#         else:
#             passed = TestCaseOutputComparator(testcase=testcase).compare_with(
#                 actual_output_lines=actual_output_lines,
#             )
#             result = TestCaseResult(
#                 testcase=copy.deepcopy(testcase),
#                 actual_output_lines=actual_output_lines,
#                 result_state=(
#                     TestCaseResultState.OK
#                     if passed
#                     else TestCaseResultState.WRONG_ANSWER
#                 ),
#             )
#         return result
#
#     def run_test_session_on_student(self, student: Student, target_index: int) \
#             -> TestSessionResult:
#         try:
#             test_session: TestSession \
#                 = self.__testcase_io.validate_and_get_test_session(target_index)
#             # if test_session.is_effectively_empty():
#             #     raise TestCaseConfigError(
#             #         fetal=True,
#             #         reason=f"設問 {target_index:02} には有効なテストケースが１つも定義されていません",
#             #         target_index=target_index,
#             #         testcase_index=None,
#             #     )
#             if test_session.has_no_testcases():
#                 raise TestCaseConfigError(
#                     fetal=True,
#                     reason=f"設問 {target_index:02} にテストケースが定義されていません。不要な場合はテストケースの設定で設問を消去してください。",
#                     target_index=target_index,
#                     testcase_index=None,
#                 )
#         except TestCaseConfigError as e:
#             return TestSessionResult(
#                 testcase_results=None,
#                 reason=e.reason,
#             )
#
#         testcase_results = []
#         for testcase in test_session.testcases:
#             testcase_result = self.run_testcase_on_student(
#                 student=student,
#                 target_index=target_index,
#                 testcase=testcase,
#             )
#             testcase_results.append(testcase_result)
#         return TestSessionResult(
#             testcase_results=testcase_results,
#             reason=None,
#         )
#
#     def run_all_tests_on_student(self, student: Student,
#                                  target_indexes: list[int]) -> dict[int, TestSessionResult]:
#         target_test_session_mapping: dict[int, TestSessionResult] \
#             = {}  # target_index -> TestSessionResult
#         for target_index in target_indexes:
#             target_test_session_mapping[target_index] \
#                 = self.run_test_session_on_student(student, target_index)
#         return target_test_session_mapping
