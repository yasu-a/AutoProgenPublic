import re

from domain.errors import ProjectIOError, BuildServiceError
from domain.models.reuslts import BuildResult
from domain.models.values import StudentID
from files.progress import ProgressIO
from files.project import ProjectIO


class BuildService:  # environment builder
    def __init__(
            self,
            *,
            project_io: ProjectIO,
            progress_io: ProgressIO,
    ):
        self._project_io = project_io
        self._progress_io = progress_io

    def _build(self, student_id: StudentID) -> None:
        if not self._project_io.students[student_id].is_submitted:
            raise BuildServiceError(
                reason=f"未提出の学生です。"
            )

        try:
            source_file_relative_path_lst = self._project_io.iter_student_source_file_relative_path_in_submission_folder(
                student_id=student_id,
                target_id=self._project_io.get_target_id(),
            )
        except ProjectIOError as e:
            raise BuildServiceError(
                reason=f"提出フォルダからソースファイルを抽出中にエラーが発生しました。\n{e.reason}",
            )
        if len(source_file_relative_path_lst) > 1:
            raise BuildServiceError(
                reason="提出物に複数のソースファイルが見つかりました。\n" + '\n'.join(
                    map(str, source_file_relative_path_lst)
                ),
            )
        elif len(source_file_relative_path_lst) == 0:
            raise BuildServiceError(
                reason=f"提出物にソースファイルが見つかりませんでした。"
            )

        source_file_relative_path = source_file_relative_path_lst[0]
        content_bytes = self._project_io.get_student_submission_file_content_bytes(
            student_id=student_id,
            relative_path=source_file_relative_path,
        )

        try:
            content_str = content_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            try:
                content_str = content_bytes.decode("shift-jis", errors="strict")
            except UnicodeDecodeError:
                raise BuildServiceError(
                    reason=f"ソースファイルの文字コードが判定できません。\n"
                           f"ファイル名: {source_file_relative_path}\n"
                )
        content_str = re.sub(r"\n|\r\n", "\n", content_str)

        self._project_io.put_student_target_source_file(
            student_id=student_id,
            content_str=content_str,
        )

    def build_and_save_result(self, student_id: StudentID) -> None:
        try:
            self._build(
                student_id=student_id,
            )
        except BuildServiceError as e:
            result = BuildResult.error(e)
        else:
            result = BuildResult.success()

        with self._progress_io.with_student(student_id) as progress_io_with_student:
            progress_io_with_student.write_student_build_result(
                result=result,
            )
