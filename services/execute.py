import subprocess
from typing import TextIO

from domain.errors import ExecuteServiceError
from domain.models.result_execute import OutputFileMapping, TestCaseExecuteResult, \
    TestCaseExecuteResultMapping, ExecuteResult
from domain.models.testcase import TestCaseExecuteConfig
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
            input_fp: TextIO | None,
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
        self._testcase_io.clone_student_executable_to_execute_folder(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        self._testcase_io.create_input_files_to_execute_folder(
            student_id=student_id,
            testcase_id=testcase_id,
        )

    def _execute_and_get_output(self, student_id: StudentID, testcase_id: TestCaseID) \
            -> tuple[TestCaseExecuteConfig, OutputFileMapping]:  # 使用した構成と出力を返す
        """
        与えられた生徒IDとテストケースIDに対して、実行可能な構成を読み取り、
        実行し、その結果の標準出力と出力ファイルを収集します。

        Parameters:
        student_id (StudentID): 生徒のID
        testcase_id (TestCaseID): テストケースのID

        Returns:
        tuple[ExecuteConfig, TestCaseExecuteResultOutputFiles]:
            - ExecuteConfig: 実行に使用された構成
            - TestCaseExecuteResultOutputFiles: 実行結果の出力ファイル

        Raises:
        ExecuteServiceError: 実行中にエラーが発生した場合
        """
        # 実行フォルダのファイル構成を構築
        self._construct_test_folder_from_testcase(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        # 実行構成を読み取る
        execute_config = self._testcase_io.read_config(testcase_id).execute_config
        # 実行可能なファイルのフルパスを取得
        executable_fullpath = self._testcase_io.get_executable_fullpath_if_exists(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        # 実行フォルダのファイル構成を記憶
        file_relative_path_lst_base = self._testcase_io.list_file_relative_paths_in_execute_folder(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        # 実行可能なファイルが存在しない場合、例外を発生させる
        if executable_fullpath is None:
            raise ExecuteServiceError(
                reason="実行ファイルが存在しません",
                execute_config=execute_config,
            )

        # 標準入力ファイルを読み取り、実行ファイルを実行する子プロセスを開始する
        try:
            stdin_fp = self._testcase_io.get_stdin_fp(student_id, testcase_id)
            if stdin_fp is None:  # 標準入力ファイルが存在しない場合は標準入力を渡さない
                runner = ExecutableRunner(
                    executable_fullpath=str(executable_fullpath),
                    timeout=execute_config.options.timeout,
                    input_fp=None,
                )
                stdout_text = runner.run()
            else:  # 標準入力ファイルが存在する場合はコンテキストを管理して渡す
                with self._testcase_io.get_stdin_fp(student_id, testcase_id) as stdin_fp:
                    runner = ExecutableRunner(
                        executable_fullpath=str(executable_fullpath),
                        timeout=execute_config.options.timeout,
                        input_fp=stdin_fp,
                    )
                    stdout_text = runner.run()
        except ExecutableRunnerTimeoutError:
            raise ExecuteServiceError(
                reason="実行がタイムアウトしました",
                execute_config=execute_config,
            )
        else:
            # 標準出力は改行コードがCR+LFになることがあるのでLFに統一する
            stdout_text = stdout_text.replace("\r\n", "\n")
            # 標準出力を書きだす
            self._testcase_io.dump_stdout(
                student_id=student_id,
                testcase_id=testcase_id,
                stdout_text=stdout_text,
            )
            # 書きだした標準出力を含む出力ファイルを読み取る
            file_relative_path_lst_diff = (
                self._testcase_io.list_file_relative_paths_difference_in_test_folder(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    file_relative_paths_base=file_relative_path_lst_base,
                )
            )
            output_files = (
                self._testcase_io.read_relative_file_paths_in_test_folder_as_output_files(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    file_relative_paths=file_relative_path_lst_diff,
                )
            )
            return execute_config, output_files

    def execute_and_save_result(self, student_id: StudentID) -> None:
        testcase_execute_result_mapping: dict[TestCaseID, TestCaseExecuteResult] = {}
        testcase_id_lst = self._testcase_io.list_ids()
        if not testcase_id_lst:
            result = ExecuteResult.error(
                reason="実行可能なテストケースがありません",
            )
        else:
            for testcase_id in testcase_id_lst:
                try:
                    execute_config, output_files = self._execute_and_get_output(
                        student_id=student_id,
                        testcase_id=testcase_id,
                    )
                except ExecuteServiceError as e:
                    testcase_execute_result_mapping[testcase_id] = TestCaseExecuteResult.error(
                        testcase_id=testcase_id,
                        execute_config_hash=hash(e.execute_config),
                        reason=e.reason,
                    )
                else:
                    testcase_execute_result_mapping[testcase_id] = TestCaseExecuteResult.success(
                        testcase_id=testcase_id,
                        execute_config_hash=hash(execute_config),
                        output_files=output_files,
                    )

            # FIXME: 常に成功する
            #        --------------------------------------------------------------------
            #        ExecuteStageが失敗すると次のステージに進めないため常に成功するようになっている
            #        ステージを生徒ID-ステージID-テストケースIDで細分化する
            result = ExecuteResult.success(
                testcase_results=TestCaseExecuteResultMapping(
                    testcase_execute_result_mapping,
                ),
            )

        with self._progress_io.with_student(student_id) as student_progress_io:
            student_progress_io.write_execute_result(
                result=result,
            )
