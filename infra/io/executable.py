import subprocess
from pathlib import Path
from pprint import pformat

from utils.app_logging import create_logger


class ExecutableIOTimeoutError(ValueError):
    pass


class ExecutableIO:
    _logger = create_logger()

    def __init__(
            self,
    ):
        pass

    def run(
            self,
            executable_fullpath: Path,
            timeout: float,
            input_file_fullpath: Path | None,
    ) -> str:  # returns the content of stdout as a text
        kwargs = dict(
            # Set the current working directory to the parent directory of the executable
            cwd=str(executable_fullpath.parent),
            args=[str(executable_fullpath.name)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,  # cwdを動作させるために必要？
        )
        if input_file_fullpath is not None:
            kwargs["stdin"] = input_file_fullpath.open(mode="r")
        self._logger.info(
            "Run executable:\n" + pformat(kwargs)
            + "\nFiles:\n" + "\n".join(map(str, executable_fullpath.parent.iterdir()))
        )
        try:
            with subprocess.Popen(**kwargs) as p:
                try:
                    stdout_text, stderr_text = p.communicate(
                        timeout=timeout,
                    )
                except subprocess.TimeoutExpired:
                    p.terminate()
                    raise ExecutableIOTimeoutError()
                else:
                    assert stderr_text is None, stderr_text
                    return stdout_text.replace("\r\n", "\n")
        finally:
            if input_file_fullpath is not None:
                kwargs["stdin"].close()
