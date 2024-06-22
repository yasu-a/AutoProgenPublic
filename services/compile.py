import subprocess
from pathlib import Path

from app_logging import create_logger
from files.project import ProjectIO
from files.settings import GlobalSettingsIO
from models.errors import ProjectIOError, CompileServiceError
from models.reuslts import CompileResult
from models.values import StudentID


class _VSDevToolError(RuntimeError):
    def __init__(self, reason: str, output: str | None):
        self.reason = reason
        self.output = output


class _VSDevTool:
    _logger = create_logger()

    def __init__(
            self,
            *,
            vs_dev_cmd_bat_path: Path,
            timeout: float,
            cwd_fullpath: Path,
            target_relative_path: Path,
    ):
        if not vs_dev_cmd_bat_path.exists():
            raise _VSDevToolError(
                reason=f"Visual Studio 開発者ツールが存在しません: {vs_dev_cmd_bat_path!s}",
                output=None,
            )
        if not cwd_fullpath.exists():
            raise _VSDevToolError(
                reason=f"コンパイル先のディレクトリが存在しません: {cwd_fullpath!s}",
                output=None,
            )
        if not (cwd_fullpath / target_relative_path).exists():
            raise _VSDevToolError(
                reason=f"コンパイル対象のファイルが存在しません: {cwd_fullpath / target_relative_path!s}",
                output=None,
            )

        self._vs_dev_cmd_bat_path = vs_dev_cmd_bat_path
        self._timeout = timeout
        self._cwd_fullpath = cwd_fullpath
        self._target_relative_path = target_relative_path

    def _create_cli_args(self) -> list[str]:
        args = ["cmd", "/k", str(self._vs_dev_cmd_bat_path), "-no_logo", "&"]
        args += ["cl", "/EHsc", str(self._target_relative_path), "&"]
        args += ["exit", "&", "exit"]
        return args

    def _run_and_get_output(self) -> str:
        args = self._create_cli_args()
        self._logger.info(f"Run command:\n  cd {self._cwd_fullpath!s}\n  " + ' '.join(args))
        output = subprocess.check_output(
            args,
            timeout=self._timeout,
            encoding="shift-jis",
            stderr=subprocess.STDOUT,
            cwd=self._cwd_fullpath,
            universal_newlines=True,
        )
        return output

    def run_and_get_output(self) -> str:
        try:
            output = self._run_and_get_output()
        except subprocess.CalledProcessError as e:
            raise _VSDevToolError(
                reason="コンパイルエラーが発生しました",
                output=e.stdout,
            )
        except subprocess.TimeoutExpired as e:
            raise _VSDevToolError(
                reason="コンパイラからの応答がタイムアウトしました",
                output=e.stdout,
            )
        else:
            return output


class CompileService:
    _logger = create_logger()

    def __init__(
            self,
            *,
            global_settings_io: GlobalSettingsIO,
            project_io: ProjectIO,
    ):
        self._global_settings_io = global_settings_io
        self._project_io = project_io

    def _compile_and_get_output(self, student_id: StudentID) -> str:
        compiler_tool_fullpath = self._global_settings_io.get_compiler_tool_fullpath()
        if compiler_tool_fullpath is None:
            raise CompileServiceError(
                reason="コンパイラが設定されていません",
                output=None,
            )

        try:
            compile_target_fullpath = self._project_io.get_student_compile_target_fullpath(
                student_id=student_id,
            )
        except ProjectIOError as e:
            raise CompileServiceError(
                reason=f"コンパイル対象を取得できません。\n{e.reason}",
                output=None,
            )

        try:
            compiler_tool = _VSDevTool(
                vs_dev_cmd_bat_path=compiler_tool_fullpath,
                timeout=self._global_settings_io.get_compiler_timeout(),
                cwd_fullpath=compile_target_fullpath.parent,
                target_relative_path=compile_target_fullpath.relative_to(
                    compile_target_fullpath.parent
                ),
            )
            output = compiler_tool.run_and_get_output()
        except _VSDevToolError as e:
            raise CompileServiceError(
                reason=f"コンパイラの実行に失敗しました。\n{e.reason}",
                output=e.output,
            )

        return output

    def compile_and_save_result(self, student_id: StudentID):
        try:
            output = self._compile_and_get_output(
                student_id=student_id,
            )
        except CompileServiceError as e:
            result = CompileResult.error(e)
        else:
            result = CompileResult.success(output)

        self._project_io.write_student_compile_result(
            student_id=student_id,
            result=result,
        )
