import subprocess
from pathlib import Path

from autoprogen.domain.error.stage.compile import (
    CompilerDiagnosticError,
    CompilerExecutionFailedError,
    CompilerInputFileNotFoundError,
    CompilerTimeoutError,
    CompilerWorkingDirectoryNotFoundError,
    VsDevToolNotFoundError,
)
from autoprogen.util.app_logging import create_logger


class _VSDevTool:
    """Visual Studio開発者コマンドを介してCソースをコンパイルする。"""

    _logger = create_logger()

    def __init__(
            self,
            *,
            vs_dev_cmd_bat_path: Path,
            timeout: float,
            cwd_fullpath: Path,
        target_relative_path: Path,
    ) -> None:
        """コンパイラのパスと実行条件を検証して保持する。"""
        if not vs_dev_cmd_bat_path.exists():
            raise VsDevToolNotFoundError(path=vs_dev_cmd_bat_path)
        if not cwd_fullpath.exists():
            raise CompilerWorkingDirectoryNotFoundError(path=cwd_fullpath)
        if not (cwd_fullpath / target_relative_path).exists():
            raise CompilerInputFileNotFoundError(
                path=cwd_fullpath / target_relative_path,
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
            errors="replace",
        )
        return output

    @classmethod
    def _is_output_from_compiler(cls, output: str) -> bool:
        return "Copyright (C) Microsoft Corporation" in output

    def run_and_get_output(self) -> str:
        """コンパイラを実行し、失敗原因を構造化エラーとして通知する。"""
        try:
            output = self._run_and_get_output()
        except subprocess.CalledProcessError as e:
            output = e.stdout
            self._logger.info(f"Compiler exist with error\n{output}")
            if output is not None and self._is_output_from_compiler(output):
                raise CompilerDiagnosticError(output=output)
            else:
                raise CompilerExecutionFailedError(output=output)
        except subprocess.TimeoutExpired as e:
            output = e.stdout
            if isinstance(output, bytes):
                output = output.decode("shift-jis", errors="replace")
            raise CompilerTimeoutError(output=output)
        else:
            return output


class CompileToolIO:
    """コンパイラ実行をServiceから利用するためのIO境界を提供する。"""

    def __init__(self) -> None:
        """状態を持たないコンパイラIOを初期化する。"""
        pass

    @classmethod
    def run_and_get_output(
            cls,
            compiler_tool_fullpath: Path,
            timeout: float,
            cwd_fullpath: Path,
            target_relative_path: Path,
    ) -> str:
        """指定された開発者ツールで対象ソースをコンパイルする。"""
        compiler_tool = _VSDevTool(
            vs_dev_cmd_bat_path=compiler_tool_fullpath,
            timeout=timeout,
            cwd_fullpath=cwd_fullpath,
            target_relative_path=target_relative_path,
        )
        return compiler_tool.run_and_get_output()
