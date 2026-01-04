import re
from pathlib import Path
from typing import Callable

from feature.projman.domain.interface.gateway import \
    IStudentSubmissionListSourceRelativePathGateway, \
    StudentSubmissionListSourceRelativePathGatewayError, IStudentSubmissionGetFileContentGateway
from shared.domain.value.identifier import StudentID, TargetID
from shared.infra.repository.current_project import CurrentProjectRepository
from shared.infra.system.current_project_core_io import CurrentProjectCoreIO


class StudentSubmissionListSourceRelativePathGateway(
    IStudentSubmissionListSourceRelativePathGateway
):
    def __init__(
            self,
            *,
            student_submission_folder_fullpath: Callable[[StudentID], Path],
            current_project_core_io: CurrentProjectCoreIO,
            current_project_repo: CurrentProjectRepository,
    ):
        self._student_submission_folder_fullpath = student_submission_folder_fullpath
        self._current_project_core_io = current_project_core_io
        self._current_project_repo = current_project_repo

    def execute(
            self,
            *,
            student_id: StudentID,
    ) -> list[Path]:  # returns paths relative to StudentEntity submission folder
        target_id = self._current_project_repo.get().target_id

        student_submission_folder_fullpath = self._student_submission_folder_fullpath(student_id)

        source_file_fullpath_lst = []
        # 生徒の提出フォルダのソースコードと思われるファイルパスをイテレートする
        for file_relative_path in self._current_project_core_io.walk_files(
                folder_fullpath=student_submission_folder_fullpath,
                return_absolute=False,
        ):
            # 拡張子が.c以外のファイルは除く
            if file_relative_path.suffix != ".c":
                continue

            # Visual Studio のプロジェクトをそのまま出してくると名前が".c"で終わるフォルダができるので除く
            if file_relative_path.is_dir():
                continue

            # MacユーザのZIPファイルに生成される"__MACOSX"フォルダは除く
            if "__MACOSX" in file_relative_path.parts[:-1]:
                continue

            # 設問番号の抽出
            numbers_str = re.findall(r"(?<!\()\d+(?!\))", file_relative_path.stem)
            if len(numbers_str) > 1:
                raise StudentSubmissionListSourceRelativePathGatewayError(
                    reason=f"ファイル名{file_relative_path!s}から設問番号を判別できません。\n"
                           f"ファイル名に数字が複数含まれています: {', '.join(numbers_str)}",
                )
            elif len(numbers_str) == 0:
                raise StudentSubmissionListSourceRelativePathGatewayError(
                    reason=f"ファイル名{file_relative_path!s}から設問番号を判別できません。\n"
                           f"ファイル名に数字が含まれていません。",
                )
            number = int(numbers_str[0])

            # 該当する設問の場合は結果に追加
            if TargetID(number) != target_id:
                continue
            source_file_fullpath_lst.append(file_relative_path)

        return source_file_fullpath_lst


class StudentSubmissionGetFileContentGateway(IStudentSubmissionGetFileContentGateway):
    def __init__(
            self,
            *,
            student_submission_folder_fullpath: Callable[[StudentID], Path],
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_submission_folder_fullpath = student_submission_folder_fullpath
        self._current_project_core_io = current_project_core_io

    def execute(
            self,
            *,
            student_id: StudentID,
            file_relative_path: Path,
    ) -> bytes:
        student_submission_folder_fullpath = self._student_submission_folder_fullpath(student_id)

        file_fullpath = student_submission_folder_fullpath / file_relative_path
        if not file_fullpath.exists():
            raise FileNotFoundError()

        return self._current_project_core_io.read_file_content_bytes(
            file_fullpath=file_fullpath,
        )
