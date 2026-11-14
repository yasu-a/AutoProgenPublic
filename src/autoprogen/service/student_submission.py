import re
from pathlib import Path, PurePosixPath

from autoprogen.domain.error import ManabaReportArchiveError, StudentSubmissionServiceError
from autoprogen.domain.error.stage.build import (
    MultipleSourceFilesError,
    SourceEncodingUnknownError,
    SourceFilenameMultipleNumbersError,
    SourceFilenameNoNumberError,
    SubmissionNotFoundError,
    SubmissionSourceNotFoundError,
)
from autoprogen.domain.model.manaba_report_archive import ManabaReportArchive, ManabaSubmissionFolderPath
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import StudentID, TargetID
from autoprogen.domain.service.source_code_factory import (
    SourceCodeDecodeError,
    SourceCodeFactory,
)
from autoprogen.infra.io.files.current_project import CurrentProjectCoreIO
from autoprogen.infra.path_layout import ProjectPathLayout
from autoprogen.infra.repository.current_project import CurrentProjectRepository
from autoprogen.infra.repository.student import StudentRepository
from autoprogen.util.app_logging import create_logger


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
            current_project_core_io: CurrentProjectCoreIO,
            project_path_layout: ProjectPathLayout,
    ):
        self._student_repo = student_repo
        self._current_project_core_io = current_project_core_io
        self._project_path_layout = project_path_layout

    @staticmethod
    def _ensure_path_within_base(
            *,
            base_folder_fullpath: Path,
            candidate_fullpath: Path,
    ) -> None:
        if not candidate_fullpath.is_relative_to(base_folder_fullpath):
            raise StudentSubmissionServiceError(
                reason=(
                    "提出アーカイブの展開中に不正なパスを検出しました。\n"
                    f"base={base_folder_fullpath}\n"
                    f"path={candidate_fullpath}"
                ),
            )

    def execute(self, *, archive: ManabaReportArchive):
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
            for student_id, student_submission_folder_name in \
                    student_id_to_submission_folder_name_mapping.items():
                # 生徒の展開先のフォルダのフルパス
                extract_base_folder_fullpath = (
                    self._project_path_layout.student_submission_dir(
                        student_id=student_id,
                    )
                )
                # 展開先のフォルダが存在しなかったらフォルダを生成
                extract_base_folder_fullpath.mkdir(
                    parents=True, exist_ok=False)
                submission_folder_path = ManabaSubmissionFolderPath(
                    value=PurePosixPath(student_submission_folder_name),
                )
                # ファイル列挙ルール（入れ子 ZIP の扱い含む）は archive モデル側に集約する。
                # 生徒のアーカイブ内のファイルを取得
                for folder_relative_path in archive.iter_folders_in_submission_folder(
                        submission_folder_path=submission_folder_path,
                ):
                    folder_relative_path = PurePosixPath(
                        *map(str.strip, folder_relative_path.parts)
                    )
                    dst_folder_fullpath = extract_base_folder_fullpath / folder_relative_path
                    dst_folder_fullpath = dst_folder_fullpath.resolve()
                    self._ensure_path_within_base(
                        base_folder_fullpath=extract_base_folder_fullpath,
                        candidate_fullpath=dst_folder_fullpath,
                    )
                    dst_folder_fullpath.mkdir(parents=True, exist_ok=True)

                # 生徒のアーカイブ内のファイルを取得
                it = archive.iter_files_in_submission_folder(
                    submission_folder_path=submission_folder_path,
                )
                # それぞれのファイルを展開する
                for submission_file in it:
                    content_relative_path = submission_file.relative_path
                    self._logger.info(
                        f"Extracting {student_id} {content_relative_path!s}")
                    # パスにスペースが含まれているとこの先のos.makedirsで失敗するので取り除く
                    content_relative_path = PurePosixPath(
                        *map(str.strip, content_relative_path.parts)
                    )
                    # 念のため展開先を固定し、path traversal を防ぐ。
                    # コピー先のファイルパス
                    dst_file_fullpath = extract_base_folder_fullpath / content_relative_path
                    dst_file_fullpath = dst_file_fullpath.resolve()
                    self._ensure_path_within_base(
                        base_folder_fullpath=extract_base_folder_fullpath,
                        candidate_fullpath=dst_file_fullpath.parent,
                    )
                    # 親フォルダを生成
                    dst_file_fullpath.parent.mkdir(parents=True, exist_ok=True)
                    self._current_project_core_io.write_file_content_bytes(
                        file_fullpath=dst_file_fullpath,
                        content_bytes=submission_file.content_bytes,
                    )
        except ManabaReportArchiveError as e:
            raise StudentSubmissionServiceError(
                reason=f"提出アーカイブの展開中にエラーが発生しました。\n{e.reason}",
            )


class StudentSubmissionGetChecksumService:
    def __init__(
            self,
            *,
            project_path_layout: ProjectPathLayout,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._project_path_layout = project_path_layout
        self._current_project_core_io = current_project_core_io

    def execute(self, student_id: StudentID) -> int:
        folder_fullpath = self._project_path_layout.student_submission_dir(student_id)
        checksum = self._current_project_core_io.calculate_folder_checksum(
            folder_fullpath=folder_fullpath,
        )
        return checksum


class StudentSubmissionListSourceRelativePathQueryService:
    def __init__(
            self,
            *,
            project_path_layout: ProjectPathLayout,
            current_project_core_io: CurrentProjectCoreIO,
            current_project_repo: CurrentProjectRepository,
    ):
        self._project_path_layout = project_path_layout
        self._current_project_core_io = current_project_core_io
        self._current_project_repo = current_project_repo

    def execute(
            self,
            *,
            student_id: StudentID,
    ) -> list[Path]:  # returns paths relative to student submission folder
        target_id = self._current_project_repo.get().target_id

        student_submission_folder_fullpath = self._project_path_layout.student_submission_dir(
            student_id
        )

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
            numbers_str = re.findall(
                r"(?<!\()\d+(?!\))", file_relative_path.stem)
            if len(numbers_str) > 1:
                raise SourceFilenameMultipleNumbersError(
                    file_relative_path=file_relative_path,
                    numbers=numbers_str,
                )
            elif len(numbers_str) == 0:
                raise SourceFilenameNoNumberError(
                    file_relative_path=file_relative_path,
                )
            number = int(numbers_str[0])

            # 該当する設問の場合は結果に追加
            if TargetID(number) != target_id:
                continue
            source_file_fullpath_lst.append(file_relative_path)

        return source_file_fullpath_lst


class StudentSubmissionGetSourceCodeService:
    """提出物から対象Cファイルを選び、正規化済みソースコードを返す。"""

    def __init__(
            self,
            *,
            student_submission_list_source_relative_path_query_service: StudentSubmissionListSourceRelativePathQueryService,
            student_repo: StudentRepository,
            source_code_factory: SourceCodeFactory,
            project_path_layout: ProjectPathLayout,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        """対象ファイルの特定、読込、正規化に必要な依存を受け取る。"""
        self._student_submission_list_source_relative_path_query_service = student_submission_list_source_relative_path_query_service
        self._student_repo = student_repo
        self._source_code_factory = source_code_factory
        self._project_path_layout = project_path_layout
        self._current_project_core_io = current_project_core_io

    def execute(self, student_id: StudentID) -> SourceCode:
        """学生の対象Cファイルを特定し、正規化済みモデルへ変換する。"""
        # 未提出の場合はエラー
        if not self._student_repo.get(student_id).is_submitted:
            raise SubmissionNotFoundError()

        # 設問に回答したソースコードを探す
        source_file_relative_path_lst = (
            self._student_submission_list_source_relative_path_query_service.execute(
                student_id=student_id,
            )
        )

        # ソースコードが複数見つかったらエラー
        if len(source_file_relative_path_lst) > 1:
            raise MultipleSourceFilesError(
                file_relative_paths=source_file_relative_path_lst,
            )

        # ソースコードが見つからなかったらエラー
        elif len(source_file_relative_path_lst) == 0:
            raise SubmissionSourceNotFoundError()

        # ソースコードを読み込む
        source_file_relative_path = source_file_relative_path_lst[0]
        source_file_fullpath = (
            self._project_path_layout.student_submission_dir(student_id)
            / source_file_relative_path
        )
        source_code_bytes = self._current_project_core_io.read_file_content_bytes(
            file_fullpath=source_file_fullpath,
        )

        # 対象Cファイルが確定した後、一度だけ文字コードと改行を正規化する。
        try:
            return self._source_code_factory.create(source_code_bytes)
        except SourceCodeDecodeError:
            raise SourceEncodingUnknownError(
                file_relative_path=source_file_relative_path,
            )
