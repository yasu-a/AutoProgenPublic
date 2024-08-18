from app_logging import create_logger
from domain.errors import ProjectIOError, CompileServiceError, CompileToolIOError
from domain.models.result_compile import CompileResult
from domain.models.values import StudentID
from files.compile_tool import CompileToolIO
from files.progress import ProgressIO
from files.project import ProjectIO
from files.settings import GlobalSettingsIO


class CompileService:
    _logger = create_logger()

    def __init__(
            self,
            *,
            global_settings_io: GlobalSettingsIO,
            project_io: ProjectIO,
            progress_io: ProgressIO,
            compile_tool_io: CompileToolIO,
    ):
        self._global_settings_io = global_settings_io
        self._project_io = project_io
        self._progress_io = progress_io
        self._compile_tool_io = compile_tool_io

    def _compile_and_get_output(self, student_id: StudentID) -> str:
        compiler_tool_fullpath = self._global_settings_io.get_compiler_tool_fullpath()
        if compiler_tool_fullpath is None:
            raise CompileServiceError(
                reason="コンパイラが設定されていません",
                output=None,
            )

        try:
            compile_target_fullpath = self._project_io.get_student_compile_target_source_fullpath(
                student_id=student_id,
            )
        except ProjectIOError as e:
            raise CompileServiceError(
                reason=f"コンパイル対象を取得できません。\n{e.reason}",
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
            raise CompileServiceError(
                reason=f"コンパイルに失敗しました。\n{e.reason}",
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

        with self._progress_io.with_student(student_id) as student_progress_io:
            student_progress_io.write_student_compile_result(
                result=result,
            )
