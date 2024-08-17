import uuid
from pathlib import Path

from app_logging import create_logger
from domain.errors import CompileTestServiceError, CompileToolIOError
from files.build_test import BuildTestIO
from files.compile_tool import CompileToolIO
from files.settings import GlobalSettingsIO


class CompileTestService:
    _logger = create_logger()

    def __init__(
            self,
            *,
            global_settings_io: GlobalSettingsIO,
            build_test_io: BuildTestIO,
            compile_tool_io: CompileToolIO,
    ):
        self._global_settings_io = global_settings_io
        self._build_test_io = build_test_io
        self._compile_tool_io = compile_tool_io

    def _compile_and_get_output(self, session_id: uuid.UUID, compiler_tool_fullpath: Path) -> str:
        self._logger.info(f"Compiler: {compiler_tool_fullpath!s}")

        # コンパイラの存在を確認
        if not compiler_tool_fullpath.exists():
            raise CompileTestServiceError(
                reason=f"コンパイラが存在しません: {compiler_tool_fullpath}",
                output=None,
            )

        compile_target_fullpath = self._build_test_io.get_compile_target_fullpath(session_id)
        if not compile_target_fullpath.exists():
            raise CompileTestServiceError(
                reason=f"コンパイル対象が見つかりません。",
                output=None,
            )

        try:
            output = self._compile_tool_io.run_and_get_output(
                compiler_tool_fullpath=compiler_tool_fullpath,
                timeout=self._global_settings_io.get_compiler_timeout(),
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
        return output

    def compile_and_get_output(self, compiler_tool_fullpath: Path) -> str:
        # raises CompileTestServiceError

        # テストセッションを作成
        session_id = self._build_test_io.create_session()

        # ビルド
        self._build_test_io.build(session_id)

        try:
            output = self._compile_and_get_output(
                session_id=session_id,
                compiler_tool_fullpath=compiler_tool_fullpath,
            )
        except CompileTestServiceError:
            raise
        finally:
            # テストセッションを閉じる
            self._build_test_io.close_session(session_id)

        return output
