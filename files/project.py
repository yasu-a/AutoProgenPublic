import functools
import re
from pathlib import Path

from app_logging import create_logger
from domain.errors import ProjectIOError
from domain.models.project_config import ProjectConfig
from domain.models.values import TargetID, StudentID
from files.core.project import ProjectCoreIO
from files.path_providers.project import ProjectPathProvider


class ProjectIO:  # TODO: BuildIO, CompileIO, ExecuteIOを分離する
    _logger = create_logger()

    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            student_build_path_provider: StudentBuildPathProvider,
            student_compile_path_provider: StudentCompilePathProvider,
            student_execute_path_provider: StudentExecutePathProvider,
            student_test_path_provider: StudentTestPathProvider,
            student_report_path_provider: StudentReportPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._project_path_provider = project_path_provider
        self._student_build_path_provider = student_build_path_provider
        self._student_compile_path_provider = student_compile_path_provider
        self._student_execute_path_provider = student_execute_path_provider
        self._student_test_path_provider = student_test_path_provider
        self._student_report_path_provider = student_report_path_provider
        self._project_core_io = project_core_io

    @functools.cache
    def read_config(self) -> ProjectConfig:
        # プロジェクトの構成を読み込む
        project_config_json_fullpath = self._project_path_provider.config_json_fullpath()
        body = self._project_core_io.read_json(
            json_fullpath=project_config_json_fullpath,
        )
        assert body is not None, project_config_json_fullpath
        return ProjectConfig.from_json(body)

    def calculate_student_submission_folder_hash(self, student_id: StudentID) -> int:
        # 生徒の提出フォルダのハッシュを計算する
        submission_folder_fullpath \
            = self._student_report_path_provider.submission_folder_fullpath(student_id)
        return self._project_core_io.calculate_folder_hash(
            folder_fullpath=submission_folder_fullpath,
        )

    def iter_student_source_file_relative_path_in_submission_folder(
            self,
            *,
            student_id: StudentID,
            target_id: TargetID,
    ) -> list[Path]:  # returns paths relative to student submission folder
        # 生徒の提出フォルダのソースコードと思われるファイルパスをイテレートする
        student_submission_folder_fullpath \
            = self._student_report_path_provider.submission_folder_fullpath(student_id)

        source_file_fullpath_lst = []
        for fullpath in student_submission_folder_fullpath.rglob("*.c"):
            relative_path = fullpath.relative_to(student_submission_folder_fullpath)
            assert fullpath.is_absolute(), fullpath
            assert not relative_path.is_absolute(), fullpath

            # Visual Studio のプロジェクトをそのまま出してくると名前が".c"で終わるフォルダができるので除く
            if fullpath.is_dir():
                continue

            # MacユーザのZIPファイルに生成される"__MACOSX"フォルダは除く
            if "__MACOSX" in relative_path.parts[:-1]:
                continue

            # 設問番号の抽出
            numbers_str = re.findall(r"(?<!\()\d+(?!\))", relative_path.stem)
            if len(numbers_str) > 1:
                raise ProjectIOError(
                    reason=f"ファイル名{relative_path!s}から設問番号を判別できません。\n"
                           f"ファイル名に設問番号とみられる数字が複数含まれています: {', '.join(numbers_str)}",
                )
            elif len(numbers_str) == 0:
                raise ProjectIOError(
                    reason=f"ファイル名{relative_path!s}から設問番号を判別できません。\n"
                           f"ファイル名に設問番号とみられる数字が含まれていません。",
                )
            number = int(numbers_str[0])

            # 該当する設問の場合は結果に追加
            if TargetID(number) != target_id:
                continue
            source_file_fullpath_lst.append(relative_path)

        return source_file_fullpath_lst

    def get_student_submission_file_content_bytes(self, student_id: StudentID,
                                                  relative_path: Path) -> bytes:
        # 生徒の提出フォルダにある指定されたファイルの中身を取得する
        student_submission_folder_fullpath \
            = self._student_report_path_provider.submission_folder_fullpath(student_id)
        source_file_fullpath = student_submission_folder_fullpath / relative_path
        with source_file_fullpath.open(mode="rb") as f:
            return f.read()

    def put_student_target_source_file(self, student_id: StudentID, content_str: str) -> None:
        # 生徒のビルドフォルダにソースコードを書きこむ
        student_build_folder_fullpath = self._student_build_path_provider.base_folder_fullpath(
            student_id=student_id,
        )
        if student_build_folder_fullpath.exists():
            self._project_core_io.rmtree_folder(student_build_folder_fullpath)
        student_target_source_file_fullpath \
            = self._student_build_path_provider.target_source_file_fullpath(student_id)
        student_target_source_file_fullpath.parent.mkdir(parents=True, exist_ok=True)
        with student_target_source_file_fullpath.open(mode="w", encoding="utf-8") as f:
            f.write(content_str)

    def get_student_compile_target_source_fullpath(self, student_id: StudentID) -> Path:
        # 生徒のコンパイル対象のソースファイルのパスを取得する
        compile_target_fullpath = self._student_build_path_provider.target_source_file_fullpath(
            student_id=student_id
        )
        if not compile_target_fullpath.exists():
            raise ProjectIOError(
                reason=f"コンパイル対象のファイルが存在しません: {compile_target_fullpath!s}"
            )
        return compile_target_fullpath
