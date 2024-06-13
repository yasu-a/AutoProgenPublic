import subprocess
from typing import Collection
from typing import TYPE_CHECKING

from app_logging import create_logger
from models.compile import EnvironmentCompileResult
from models.student import Student
from settings import settings_compiler

if TYPE_CHECKING:
    from files.environment import EnvironmentIO


class CompileError(ValueError):
    def __init__(self, *, reason: str, output: str | None):
        self.reason = reason
        self.output = output


class Compiler:
    _logger = create_logger()

    def __init__(
            self,
            *,
            vs_dev_cmd_bat_path: str,
            cwd_path: str,
            target_relative_path_lst: Collection[str],
            timeout: int
    ):
        self._vs_dev_cmd_bat_path = vs_dev_cmd_bat_path
        self._cwd_path = cwd_path
        self._target_relative_path_lst = target_relative_path_lst
        self._timeout = timeout

    def __validate_vs_dev_cmd_bat_path(self):
        if self._vs_dev_cmd_bat_path is None:
            raise CompileError(
                reason="コンパイラが設定されていません",
                output=None
            )

    def __create_cli_args(self):
        args = ["cmd", "/k", self._vs_dev_cmd_bat_path, "-no_logo", "&"]
        for entry_path in self._target_relative_path_lst:
            args += ["cl", "/EHsc", entry_path, "&"]
        args += ["exit", "&", "exit"]
        return args

    def __run_cli_with_args(self, args, cwd_path):
        self._logger.info("cd {cwd_path}")
        self._logger.info(" ".join(args))
        output = subprocess.check_output(
            args,
            timeout=self._timeout,
            encoding="shift-jis",
            stderr=subprocess.STDOUT,
            cwd=cwd_path,
            universal_newlines=True,
        )
        return output

    def run(self) -> str:
        try:
            self.__validate_vs_dev_cmd_bat_path()
            args = self.__create_cli_args()
            output = self.__run_cli_with_args(
                args=args,
                cwd_path=self._cwd_path,
            )
        except subprocess.CalledProcessError as e:
            self._logger.info(f"Compile error occurred:\n{e.output}")
            raise CompileError(
                reason="コンパイルエラーが発生しました",
                output=e.stdout,
            )
        except subprocess.TimeoutExpired as e:
            raise CompileError(
                reason="コンパイラからの応答がタイムアウトしました",
                output=e.stdout,
            )
        else:
            return output


class StudentEnvCompiler:
    def __init__(self, *, env_io: "EnvironmentIO", timeout=10, vs_dev_cmd_bat_path=None):
        vs_dev_cmd_bat_path \
            = vs_dev_cmd_bat_path or settings_compiler.get_vs_dev_cmd_bat_path()

        self._vs_dev_cmd_bat_path = vs_dev_cmd_bat_path
        self._env_io = env_io
        self._vs_dev_cmd_bat_path = vs_dev_cmd_bat_path
        self._timeout = timeout

    def _run_compiler(self, student_id, entry_path_lst: Collection[str]) -> str:
        compiler = Compiler(
            vs_dev_cmd_bat_path=self._vs_dev_cmd_bat_path,
            cwd_path=self._env_io.student_env_fullpath(student_id),
            target_relative_path_lst=entry_path_lst,
            timeout=self._timeout,
        )
        output = compiler.run()
        return output

    def compile_and_get_result(self, student: Student) -> EnvironmentCompileResult:
        try:
            output = self._run_compiler(
                student_id=student.meta.student_id,
                entry_path_lst=[entry.path for entry in student.env_meta.entries.values()],
            )
        except CompileError as e:
            return EnvironmentCompileResult.from_cli_and_reason(
                success=False,
                reason=e.reason,
                output=e.output,
            )
        else:
            return EnvironmentCompileResult.from_cli_and_reason(
                success=True,
                reason=None,
                output=output,
            )
