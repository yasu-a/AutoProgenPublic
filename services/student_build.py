import re

from domain.errors import ProjectIOError, BuildServiceError
from domain.models.values import StudentID
from files.repositories.current_project import CurrentProjectRepository
from files.repositories.student import StudentRepository
from files.repositories.student_dynamic import StudentDynamicRepository
from files.repositories.student_stage_result import StudentStageResultRepository


class StudentBuildService:  # environment builder
    def __init__(
            self,
            *,
            student_dynamic_repo: StudentDynamicRepository,
            student_stage_result_repo: StudentStageResultRepository,
            student_repo: StudentRepository,
            current_project_repo: CurrentProjectRepository,
    ):
        self._student_dynamic_repo = student_dynamic_repo
        self._student_stage_result_repo = student_stage_result_repo
        self._student_repo = student_repo
        self._current_project_repo = current_project_repo

    def _build(self, student_id: StudentID) -> None:
        if not self._student_repo.get(student_id).is_submitted:
            raise BuildServiceError(
                reason=f"未提出の学生です。"
            )

        try:
            source_file_relative_path_lst = (
                self._project_io.iter_student_source_file_relative_path_in_submission_folder(
                    student_id=student_id,
                    target_id=self._current_project_repo.get().target_id,
                )
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
            result = BuildStudentStageResult.error(e)
        else:
            result = BuildStudentStageResult.success(
                submission_folder_hash=self._project_io.calculate_student_submission_folder_hash(
                    student_id=student_id,
                )
            )

        with self._progress_io.with_student(student_id) as student_progress_io:
            student_progress_io.write_build_result(
                result=result,
            )
