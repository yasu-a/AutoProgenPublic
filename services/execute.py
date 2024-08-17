import subprocess
from typing import TextIO

from domain.errors import ExecuteServiceError
from domain.models.reuslts import ExecuteResult, TestCaseExecuteResultSet, TestCaseExecuteResult, \
    ExecuteResultFlag
from domain.models.testcase import ExecuteConfig
from domain.models.values import TestCaseID, StudentID
from files.progress import ProgressIO
from files.project import ProjectIO
from files.testcase import TestCaseIO


# TODO: ExecutableRunner should be a repository

class ExecutableRunnerTimeoutError(ValueError):
    pass


class ExecutableRunner:
    def __init__(
            self,
            *,
            executable_fullpath: str,
            timeout: float,
            input_fp: TextIO,
    ):
        self._executable_fullpath = executable_fullpath
        self._timeout = timeout
        self._input_fp = input_fp

    def run(self) -> str:  # returns the content of stdout as a text
        kwargs = {
            "args": [self._executable_fullpath],
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "universal_newlines": True,
        }
        if self._input_fp is not None:
            kwargs["stdin"] = self._input_fp
        with subprocess.Popen(**kwargs) as p:
            try:
                stdout_text, stderr_text = p.communicate(
                    timeout=self._timeout,
                )
            except subprocess.TimeoutExpired:
                p.terminate()
                raise ExecutableRunnerTimeoutError()
            else:
                assert stderr_text is None, stderr_text
                return stdout_text.replace("\r\n", "\n")


class ExecuteService:
    def __init__(
            self,
            *,
            project_io: ProjectIO,
            testcase_io: TestCaseIO,
            progress_io: ProgressIO,
    ):
        self._project_io = project_io
        self._testcase_io = testcase_io
        self._progress_io = progress_io

    def _construct_test_folder_from_testcase(self, student_id: StudentID, testcase_id: TestCaseID):
        self._testcase_io.clone_student_executable_to_test_folder(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        self._testcase_io.create_input_files_to_test_folder(
            student_id=student_id,
            testcase_id=testcase_id,
        )

    def _execute_and_dump_stdout(self, student_id: StudentID, testcase_id: TestCaseID) \
            -> ExecuteConfig:  # 使用した構成を返す
        self._construct_test_folder_from_testcase(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        testcase_config = self._testcase_io.read_config(testcase_id)
        executable_fullpath = self._testcase_io.get_executable_fullpath_if_exists(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        if executable_fullpath is None:
            raise ExecuteServiceError(
                reason="実行ファイルが存在しません",
                execute_config=testcase_config.execute_config,
            )
        with self._testcase_io.get_stdin_fp(student_id, testcase_id) as stdin_fp:
            try:
                runner = ExecutableRunner(
                    executable_fullpath=str(executable_fullpath),
                    timeout=testcase_config.execute_config.options.timeout,
                    input_fp=stdin_fp,
                )
                stdout_text = runner.run()
            except ExecutableRunnerTimeoutError:
                raise ExecuteServiceError(
                    reason="実行がタイムアウトしました",
                    execute_config=testcase_config.execute_config,
                )
            else:
                self._testcase_io.dump_stdout(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    stdout_text=stdout_text,
                )
                return testcase_config.execute_config

    def execute_and_save_result(self, student_id: StudentID):
        testcase_result_set = TestCaseExecuteResultSet()
        for testcase_id in self._testcase_io.list_ids():
            try:
                execute_config = self._execute_and_dump_stdout(student_id, testcase_id)
            except ExecuteServiceError as e:
                testcase_result_set.add(
                    TestCaseExecuteResult(
                        testcase_id=testcase_id,
                        execute_config=e.execute_config,
                        flag=ExecuteResultFlag.EXECUTION_FAILED,
                        reason=e.reason,
                    )
                )
            else:
                testcase_result_set.add(
                    TestCaseExecuteResult(
                        testcase_id=testcase_id,
                        execute_config=execute_config,
                        flag=ExecuteResultFlag.EXIT_NORMALLY,
                    )
                )
        result = ExecuteResult.success(
            testcase_result_set=testcase_result_set,
        )

        with self._progress_io.with_student(student_id) as progress_io_with_student:
            progress_io_with_student.write_student_execute_result(
                result=result,
            )
