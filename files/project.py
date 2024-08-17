import functools
import json
import os
import re
from pathlib import Path

from app_logging import create_logger
from domain.errors import ProjectIOError
from domain.models.project_config import ProjectConfig
from domain.models.student_master import StudentMaster
from domain.models.values import ProjectName, TargetID, StudentID
from files.project_core import ProjectCoreIO
from files.project_path_provider import ProjectPathProvider, ProjectPathProviderWithoutDependency


class ProjectIOWithoutDependency:
    def __init__(
            self,
            *,
            project_path_provider_without_dependency: ProjectPathProviderWithoutDependency,
    ):
        self._project_path_provider_without_dependency = project_path_provider_without_dependency

    def read_config(self, name: ProjectName) -> ProjectConfig | None:
        project_config_json_fullpath \
            = self._project_path_provider_without_dependency.project_config_json_fullpath(name)
        if not project_config_json_fullpath.exists():
            return None
        with project_config_json_fullpath.open(mode="r", encoding="utf-8") as f:
            return ProjectConfig.from_json(json.load(f))


class ProjectIO:  # TODO: BuildIO, CompileIO, ExecuteIOを分離する
    _logger = create_logger()

    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io

    def create_project_folder(self) -> None:
        # プロジェクトフォルダを作る
        self._project_path_provider.project_folder_fullpath() \
            .mkdir(parents=True, exist_ok=False)

    def write_config(self, *, project_config: ProjectConfig):
        # プロジェクトの構成を永続化する
        project_config_json_fullpath = self._project_path_provider.project_config_json_fullpath()
        self._project_core_io.write_json(
            json_fullpath=project_config_json_fullpath,
            body=project_config.to_json(),
        )

    @functools.cache
    def read_config(self) -> ProjectConfig:
        # プロジェクトの構成を読み込む
        project_config_json_fullpath = self._project_path_provider.project_config_json_fullpath()
        body = self._project_core_io.read_json(
            json_fullpath=project_config_json_fullpath,
        )
        assert body is not None, project_config_json_fullpath
        return ProjectConfig.from_json(body)

    def write_student_master(self, student_master: StudentMaster):
        # 生徒マスターを永続化する
        student_master_json_fullpath = self._project_path_provider.student_master_json_fullpath()
        self._project_core_io.write_json(
            json_fullpath=student_master_json_fullpath,
            body=student_master.to_json(),
        )

    def read_student_master(self) -> StudentMaster:
        # 生徒マスターを読み込む
        student_master_json_fullpath = self._project_path_provider.student_master_json_fullpath()
        body = self._project_core_io.read_json(
            json_fullpath=student_master_json_fullpath,
        )
        assert body is not None, student_master_json_fullpath
        return StudentMaster.from_json(body)

    @functools.cached_property
    def students(self) -> StudentMaster:
        # 生徒マスタを読み込む
        return self.read_student_master()

    def get_project_name(self) -> ProjectName:
        # プロジェクト名を取得する
        return ProjectName(self._project_path_provider.project_folder_fullpath().stem)

    def get_target_id(self) -> TargetID:
        # プロジェクトの設問IDを取得する
        return self.read_config().target_id

    def show_student_submission_folder_in_explorer(self, student_id: StudentID) -> None:
        # 生徒の提出フォルダをエクスプローラで開く
        submission_folder_fullpath \
            = self._project_path_provider.student_submission_folder_fullpath(student_id)
        os.startfile(submission_folder_fullpath)

    def iter_student_source_file_relative_path_in_submission_folder(
            self,
            *,
            student_id: StudentID,
            target_id: TargetID,
    ) -> list[Path]:  # returns paths relative to student submission folder
        # 生徒の提出フォルダのソースコードと思われるファイルパスをイテレートする
        student_submission_folder_fullpath \
            = self._project_path_provider.student_submission_folder_fullpath(student_id)

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
            = self._project_path_provider.student_submission_folder_fullpath(student_id)
        source_file_fullpath = student_submission_folder_fullpath / relative_path
        with source_file_fullpath.open(mode="rb") as f:
            return f.read()

    def put_student_target_source_file(self, student_id: StudentID, content_str: str) -> None:
        # 生徒のビルドフォルダにソースコードを書きこむ
        student_build_folder_fullpath = self._project_path_provider.student_build_folder_fullpath(
            student_id=student_id,
        )
        if student_build_folder_fullpath.exists():
            self._project_core_io.rmtree_folder(student_build_folder_fullpath)
        student_target_source_file_fullpath \
            = self._project_path_provider.student_target_source_file_fullpath(student_id)
        student_target_source_file_fullpath.parent.mkdir(parents=True, exist_ok=True)
        with student_target_source_file_fullpath.open(mode="w", encoding="utf-8") as f:
            f.write(content_str)

    def get_student_compile_target_source_fullpath(self, student_id: StudentID) -> Path:
        # 生徒のコンパイル対象のソースファイルのパスを取得する
        compile_target_fullpath = self._project_path_provider.student_target_source_file_fullpath(
            student_id=student_id
        )
        if not compile_target_fullpath.exists():
            raise ProjectIOError(
                reason=f"コンパイル対象のファイルが存在しません: {compile_target_fullpath!s}"
            )
        return compile_target_fullpath
