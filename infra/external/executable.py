import subprocess
from pathlib import Path


class ExecutableIOTimeoutError(ValueError):
    pass


class ExecutableIO:
    def __init__(
            self,
    ):
        pass

    @classmethod
    def run(
            cls,
            executable_fullpath: Path,
            timeout: float,
            input_file_fullpath: Path | None,
    ) -> str:  # returns the content of stdout as a text
        kwargs = dict(
            args=[str(executable_fullpath)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        if input_file_fullpath is not None:
            kwargs["stdin"] = input_file_fullpath.open(mode="r")
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
