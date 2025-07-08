import re
from pathlib import Path, PurePosixPath
from typing import Iterable, IO

from domain.errors import ServiceError, ManabaReportArchiveIOError, StudentSubmissionServiceError
from domain.models.values import StudentID, TargetID
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.io.report_archive import ManabaReportArchiveIO
from infra.io.student_folder_show_in_explorer import StudentFolderShowInExplorerIO
from infra.path_providers.current_project import StudentSubmissionPathProvider
from infra.repositories.current_project import CurrentProjectRepository
from infra.repositories.student import StudentRepository
from utils.app_logging import create_logger


class StudentSubmissionExistService:
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
    ):
        self._student_repo = student_repo

    def execute(self, student_id: StudentID) -> bool:
        return self._student_repo.get(student_id).is_submitted


class StudentSubmissionExtractService:
    _logger = create_logger()

    def __init__(
            self,
            *,
            student_repo: StudentRepository,
            manaba_report_archive_io: ManabaReportArchiveIO,
            current_project_core_io: CurrentProjectCoreIO,
            student_submission_path_provider: StudentSubmissionPathProvider,
    ):
        self._student_repo = student_repo
        self._manaba_report_archive_io = manaba_report_archive_io
        self._current_project_core_io = current_project_core_io
        self._student_submission_path_provider = student_submission_path_provider

    def execute(self):
        if not self._student_repo.exists_any():
            raise StudentSubmissionServiceError("生徒マスタが作成されていません")

        # 生徒マスタを読み込んで生徒ID→提出フォルダ名のマッピングを作る
        student_master = self._student_repo.list()
        student_id_to_submission_folder_name_mapping: dict[StudentID, str] = {}
        for student in student_master:
            if student.submission_folder_name is not None:
                student_id_to_submission_folder_name_mapping[student.student_id] \
                    = student.submission_folder_name

        # 生徒の提出物を展開する
        try:
            self._manaba_report_archive_io.validate_master_excel_exists()
            self._manaba_report_archive_io.validate_archive_contents(
                student_submission_folder_names=set(
                    student_id_to_submission_folder_name_mapping.values()
                ),
            )

            for student_id, student_submission_folder_name in \
                    student_id_to_submission_folder_name_mapping.items():
                # 生徒の展開先のフォルダのフルパス
                extract_base_folder_fullpath = (
                    self._student_submission_path_provider.student_submission_folder_fullpath(
                        student_id=student_id,
                    )
                )
                # 展開先のフォルダが存在しなかったらフォルダを生成
                extract_base_folder_fullpath.mkdir(parents=True, exist_ok=False)
                # 生徒のアーカイブ内のファイルの相対パスとファイルポインタのイテラブルを取得
                it: Iterable[tuple[PurePosixPath, IO[bytes]]] = (
                    self._manaba_report_archive_io.iter_student_submission_archive_contents(
                        student_id=student_id,
                        student_submission_folder_name=student_submission_folder_name,
                    )
                )
                # それぞれのファイルを展開する
                for content_relative_path, fp in it:
                    self._logger.info(f"Extracting {student_id} {content_relative_path!s}")
                    # パスにスペースが含まれているとこの先のos.makedirsで失敗するので取り除く
                    content_relative_path = PurePosixPath(
                        *map(str.strip, content_relative_path.parts)
                    )
                    # コピー先のファイルパス
                    dst_file_fullpath = extract_base_folder_fullpath / content_relative_path
                    dst_file_fullpath = dst_file_fullpath.resolve()
                    assert dst_file_fullpath.parent.is_relative_to(
                        extract_base_folder_fullpath
                    ), (dst_file_fullpath, extract_base_folder_fullpath)
                    # 親フォルダを生成
                    dst_file_fullpath.parent.mkdir(parents=True, exist_ok=True)
                    self._current_project_core_io.write_file_content_bytes(
                        file_fullpath=dst_file_fullpath,
                        content_bytes=fp.read(),
                    )
        except ManabaReportArchiveIOError as e:
            raise StudentSubmissionServiceError(
                reason=f"提出アーカイブの展開中にエラーが発生しました。\n{e.reason}",
            )


class StudentSubmissionFolderShowService:
    # 生徒の提出データが入ったフォルダをエクスプローラで開く

    def __init__(
            self,
            *,
            student_folder_show_in_explorer_io: StudentFolderShowInExplorerIO,
    ):
        self._student_folder_open_in_explorer_io = student_folder_show_in_explorer_io

    def execute(self, student_id: StudentID):
        self._student_folder_open_in_explorer_io.show_submission_folder(student_id)


class StudentSubmissionGetChecksumService:
    def __init__(
            self,
            *,
            student_submission_path_provider: StudentSubmissionPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_submission_path_provider = student_submission_path_provider
        self._current_project_core_io = current_project_core_io

    def execute(self, student_id: StudentID) -> int:
        folder_fullpath \
            = self._student_submission_path_provider.student_submission_folder_fullpath(student_id)
        checksum = self._current_project_core_io.calculate_folder_checksum(
            folder_fullpath=folder_fullpath,
        )
        return checksum


class StudentSubmissionListSourceRelativePathQueryServiceError(ServiceError):
    def __init__(self, reason: str) -> None:
        self.reason = reason


class StudentSubmissionListSourceRelativePathQueryService:
    def __init__(
            self,
            *,
            student_submission_path_provider: StudentSubmissionPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
            current_project_repo: CurrentProjectRepository,
    ):
        self._student_submission_path_provider = student_submission_path_provider
        self._current_project_core_io = current_project_core_io
        self._current_project_repo = current_project_repo

    def execute(
            self,
            *,
            student_id: StudentID,
    ) -> list[Path]:  # returns paths relative to student submission folder
        target_id = self._current_project_repo.get().target_id

        student_submission_folder_fullpath \
            = self._student_submission_path_provider.student_submission_folder_fullpath(student_id)

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
                raise StudentSubmissionListSourceRelativePathQueryServiceError(
                    reason=f"ファイル名{file_relative_path!s}から設問番号を判別できません。\n"
                           f"ファイル名に数字が複数含まれています: {', '.join(numbers_str)}",
                )
            elif len(numbers_str) == 0:
                raise StudentSubmissionListSourceRelativePathQueryServiceError(
                    reason=f"ファイル名{file_relative_path!s}から設問番号を判別できません。\n"
                           f"ファイル名に数字が含まれていません。",
                )
            number = int(numbers_str[0])

            # 該当する設問の場合は結果に追加
            if TargetID(number) != target_id:
                continue
            source_file_fullpath_lst.append(file_relative_path)

        return source_file_fullpath_lst


class StudentSubmissionGetFileContentQueryService:
    def __init__(
            self,
            *,
            student_submission_path_provider: StudentSubmissionPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_submission_path_provider = student_submission_path_provider
        self._current_project_core_io = current_project_core_io

    def execute(
            self,
            *,
            student_id: StudentID,
            file_relative_path: Path,
    ) -> bytes:
        student_submission_folder_fullpath \
            = self._student_submission_path_provider.student_submission_folder_fullpath(student_id)

        file_fullpath = student_submission_folder_fullpath / file_relative_path
        if not file_fullpath.exists():
            raise FileNotFoundError()

        return self._current_project_core_io.read_file_content_bytes(
            file_fullpath=file_fullpath,
        )


class StudentSubmissionGetSourceFileServiceError(ServiceError):
    def __init__(self, reason: str) -> None:
        self.reason = reason


class StudentSubmissionGetSourceContentService:
    def __init__(
            self,
            *,
            student_submission_list_source_relative_path_query_service: StudentSubmissionListSourceRelativePathQueryService,
            student_submission_get_file_content_query_service: StudentSubmissionGetFileContentQueryService,
            student_repo: StudentRepository,
    ):
        self._student_submission_list_source_relative_path_query_service = student_submission_list_source_relative_path_query_service
        self._student_submission_get_file_content_query_service = student_submission_get_file_content_query_service
        self._student_repo = student_repo

    def execute(self, student_id: StudentID) -> str:
        # 未提出の場合はエラー
        if not self._student_repo.get(student_id).is_submitted:
            raise StudentSubmissionGetSourceFileServiceError(
                reason=f"未提出の学生です。"
            )

        # 設問に回答したソースコードを探す
        try:
            source_file_relative_path_lst = (
                self._student_submission_list_source_relative_path_query_service.execute(
                    student_id=student_id,
                )
            )
        except StudentSubmissionListSourceRelativePathQueryServiceError as e:
            raise StudentSubmissionGetSourceFileServiceError(
                reason=f"提出フォルダからソースファイルを抽出中にエラーが発生しました。\n{e.reason}",
            )

        # ソースコードが複数見つかったらエラー
        if len(source_file_relative_path_lst) > 1:
            raise StudentSubmissionGetSourceFileServiceError(
                reason="提出物に複数のソースファイルが見つかりました。\n" + '\n'.join(
                    map(str, source_file_relative_path_lst)
                ),
            )

        # ソースコードが見つからなかったらエラー
        elif len(source_file_relative_path_lst) == 0:
            raise StudentSubmissionGetSourceFileServiceError(
                reason=f"提出物にソースファイルが見つかりませんでした。"
            )

        # ソースコードを読み込む
        source_file_relative_path = source_file_relative_path_lst[0]
        content_bytes = self._student_submission_get_file_content_query_service.execute(
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
                raise StudentSubmissionGetSourceFileServiceError(
                    reason=f"ソースファイルの文字コードが判定できません。\n"
                           f"ファイル名: {source_file_relative_path}\n"
                )

        # 改行コードを\nに置き換える
        content_text = re.sub(r"\n|\r\n", "\n", content_text)

        return content_text
