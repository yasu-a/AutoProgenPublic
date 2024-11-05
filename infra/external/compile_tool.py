import subprocess
from pathlib import Path

from domain.errors import CompileToolIOError
from utils.app_logging import create_logger


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

    @classmethod
    def _is_output_from_compiler(cls, output: str) -> bool:
        return "Copyright (C) Microsoft Corporation" in output

    def run_and_get_output(self) -> str:
        try:
            output = self._run_and_get_output()
        except subprocess.CalledProcessError as e:
            output = e.stdout
            self._logger.info(f"Compiler exist with error\n{output}")
            if self._is_output_from_compiler(output):
                raise _VSDevToolError(
                    reason="コンパイルエラーが発生しました",
                    output=output,
                )
            else:
                raise CompileToolIOError(
                    reason="コンパイラを実行できません",
                    output=output,
                )
        except subprocess.TimeoutExpired as e:
            raise _VSDevToolError(
                reason="コンパイラからの応答がタイムアウトしました",
                output=e.stdout,
            )
        else:
            return output


class CompileToolIO:
    def __init__(self):
        pass

    @classmethod
    def run_and_get_output(
            cls,
            compiler_tool_fullpath: Path,
            timeout: float,
            cwd_fullpath: Path,
            target_relative_path: Path,
    ) -> str:
        try:
            compiler_tool = _VSDevTool(
                vs_dev_cmd_bat_path=compiler_tool_fullpath,
                timeout=timeout,
                cwd_fullpath=cwd_fullpath,
                target_relative_path=target_relative_path,
            )
            return compiler_tool.run_and_get_output()
        except _VSDevToolError as e:
            raise CompileToolIOError(
                reason=e.reason,
                output=e.output,
            )
