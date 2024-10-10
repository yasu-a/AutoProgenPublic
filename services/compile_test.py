import uuid
from pathlib import Path

from app_logging import create_logger
from domain.errors import CompileTestServiceError, CompileToolIOError
from domain.models.values import IOSessionID
from files.external.compile_tool import CompileToolIO
from files.repositories.global_settings import GlobalSettingsRepository
from files.repositories.test_run import TestRunRepository
from files.repositories.test_run_source import TestRunSourceRepository


class TestRunService:
    _logger = create_logger()

    def __init__(
            self,
            *,
            global_settings_io: GlobalSettingsRepository,
            test_run_repo: TestRunRepository,
            compile_tool_io: CompileToolIO,
            test_run_source_repo: TestRunSourceRepository,
    ):
        self._global_settings_io = global_settings_io
        self._test_session_repo = test_run_repo
        self._compile_tool_io = compile_tool_io
        self._test_run_source_repo = test_run_source_repo

    def create(self) -> IOSessionID:
        test_run_id = IOSessionID(uuid.uuid4())
        self._test_session_repo.create(test_run_id)
        return test_run_id

    def compile(self, test_run_id: IOSessionID, compiler_tool_fullpath: Path) -> str:
        self._logger.info(f"Compiler: {compiler_tool_fullpath}")

        # コンパイラの存在を確認
        if not compiler_tool_fullpath.exists():
            raise CompileTestServiceError(
                reason=f"コンパイラが存在しません: {compiler_tool_fullpath}",
                output=None,
            )

        # コンパイルするソースファイルを配置
        compile_target_content = self._test_run_source_repo.get()
        compile_target_name = "test.c"
        compile_target_fullpath = self._test_session_repo.set_file(
            test_run_id=test_run_id,
            filename=compile_target_name,
            content=compile_target_content,
        )

        # コンパイルを実行
        if not compile_target_fullpath.exists():
            raise CompileTestServiceError(
                reason=f"コンパイル対象が見つかりません。",
                output=None,
            )

        try:
            output = self._compile_tool_io.run_and_get_output(
                compiler_tool_fullpath=compiler_tool_fullpath,
                timeout=self._global_settings_io.get().compile_timeout,
                cwd_fullpath=compile_target_fullpath.parent,
                target_relative_path=compile_target_fullpath.relative_to(
                    compile_target_fullpath.parent
                ),
            )
        except CompileToolIOError as e:
            self._logger.info(f"Failure:\n{e.output}")
            raise CompileTestServiceError(
                reason=f"コンパイルに失敗しました。\n{e.reason}",
                output=e.output,
            )

        self._logger.info(f"Success:\n{output}")
        return output  # returns output

    def delete(self, test_run_id: IOSessionID) -> None:
        self._test_session_repo.delete(test_run_id)
