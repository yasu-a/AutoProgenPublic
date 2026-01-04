import re
from pathlib import Path
from typing import Callable

from feature.projman.domain.interface.gateway import \
    StudentSubmissionListSourceRelativePathGatewayError, \
    IStudentSubmissionListSourceRelativePathGateway, IStudentSubmissionGetFileContentGateway
from shared.domain.error import ServiceError
from shared.domain.interface.gateway import (
    IStudentSubmissionGetSourceContentGateway,
    IStudentSubmissionGetChecksumGateway,
    IStudentSubmissionFolderShowGateway,
    IFolderShowInExplorerGateway,
)
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student import StudentRepository
from shared.infra.system.current_project_core_io import CurrentProjectCoreIO


class StudentSubmissionGetSourceFileGatewayError(ServiceError):
    def __init__(self, reason: str) -> None:
        self.reason = reason


class StudentSubmissionGetSourceContentGateway(IStudentSubmissionGetSourceContentGateway):
    def __init__(
            self,
            *,
            student_submission_list_source_relative_path_gateway: IStudentSubmissionListSourceRelativePathGateway,
            student_submission_get_file_content_gateway: IStudentSubmissionGetFileContentGateway,
            student_repo: StudentRepository,
    ):
        self._student_submission_list_source_relative_path_gateway = student_submission_list_source_relative_path_gateway
        self._student_submission_get_file_content_gateway = student_submission_get_file_content_gateway
        self._student_repo = student_repo

    def execute(self, student_id: StudentID) -> str:
        # 未提出の場合はエラー
        if not self._student_repo.get(student_id).is_submitted:
            raise StudentSubmissionGetSourceFileGatewayError(
                reason=f"未提出の学生です。"
            )

        # 設問に回答したソースコードを探す
        try:
            source_file_relative_path_lst = (
                self._student_submission_list_source_relative_path_gateway.execute(
                    student_id=student_id,
                )
            )
        except StudentSubmissionListSourceRelativePathGatewayError as e:
            raise StudentSubmissionGetSourceFileGatewayError(
                reason=f"提出フォルダからソースファイルを抽出中にエラーが発生しました。\n{e.reason}",
            )

        # ソースコードが複数見つかったらエラー
        if len(source_file_relative_path_lst) > 1:
            raise StudentSubmissionGetSourceFileGatewayError(
                reason="提出物に複数のソースファイルが見つかりました。\n" + '\n'.join(
                    map(str, source_file_relative_path_lst)
                ),
            )

        # ソースコードが見つからなかったらエラー
        elif len(source_file_relative_path_lst) == 0:
            raise StudentSubmissionGetSourceFileGatewayError(
                reason=f"提出物にソースファイルが見つかりませんでした。"
            )

        # ソースコードを読み込む
        source_file_relative_path = source_file_relative_path_lst[0]
        content_bytes = self._student_submission_get_file_content_gateway.execute(
            student_id=student_id,
            file_relative_path=source_file_relative_path,
        )

        # エンコーディングを見つける
        try:
            content_text = content_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            try:
                content_text = content_bytes.decode("shift-jis", errors="strict")
            except UnicodeDecodeError:
                raise StudentSubmissionGetSourceFileGatewayError(
                    reason=f"ソースファイルの文字コードが判定できません。\n"
                           f"ファイル名: {source_file_relative_path}\n"
                )

        # 改行コードを\nに置き換える
        content_text = re.sub(r"\n|\r\n", "\n", content_text)

        return content_text


class StudentSubmissionGetChecksumGateway(IStudentSubmissionGetChecksumGateway):
    def __init__(
            self,
            *,
            student_submission_folder_fullpath: Callable[[StudentID], Path],
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_submission_folder_fullpath = student_submission_folder_fullpath
        self._current_project_core_io = current_project_core_io

    def execute(self, student_id: StudentID) -> int:
        folder_fullpath = self._student_submission_folder_fullpath(student_id)
        checksum = self._current_project_core_io.calculate_folder_checksum(
            folder_fullpath=folder_fullpath,
        )
        return checksum


class StudentSubmissionFolderShowGateway(IStudentSubmissionFolderShowGateway):
    def __init__(
            self,
            *,
            student_submission_folder_fullpath: Callable[[StudentID], Path],
            folder_show_in_explorer_gateway: IFolderShowInExplorerGateway,
    ):
        self._student_submission_folder_fullpath = student_submission_folder_fullpath
        self._folder_show_in_explorer_gateway = folder_show_in_explorer_gateway

    def execute(self, student_id: StudentID) -> None:
        submission_folder_fullpath = self._student_submission_folder_fullpath(student_id)
        self._folder_show_in_explorer_gateway.execute(submission_folder_fullpath)
