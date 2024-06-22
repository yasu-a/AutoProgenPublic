import functools
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterable

from app_logging import create_logger
from models.errors import ProjectIOError
from models.project_config import ProjectConfig
from models.reuslts import BuildResult, CompileResult
from models.student_master import StudentMaster
from models.values import ProjectName, TargetID, StudentID


class ProjectPathProviderWithoutDependency:
    def __init__(self, project_list_folder_fullpath: Path):
        self._base = project_list_folder_fullpath

    def project_config_json_fullpath(self, project_name: ProjectName) -> Path:
        return self._base / str(project_name) / "config.json"


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


class ProjectPathProvider:
    def __init__(self, *, project_folder_fullpath):
        self._base = project_folder_fullpath

    def project_folder_fullpath(self) -> Path:
        return self._base

    def report_folder_fullpath(self) -> Path:
        return self._base / "reports"

    def student_submission_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.report_folder_fullpath() / f"{student_id}"

    def student_master_excel_fullpath(self) -> Path:
        return self.report_folder_fullpath() / "reportlist.xlsx"

    def project_config_json_fullpath(self) -> Path:
        return self._base / "config.json"

    def student_master_json_fullpath(self) -> Path:
        return self._base / "student_master.json"

    def build_folder_fullpath(self) -> Path:
        return self._base / "build"

    def student_build_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.build_folder_fullpath() / str(student_id)

    def student_target_source_file_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "main.c"

    def student_build_result_json_fullpath(self,
                                           student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "__build_result.json"

    def student_executable_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "main.exe"

    def student_compile_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "__compile_result.json"

    def iter_student_dynamic_folder_fullpath(self, student_id: StudentID) -> Iterable[Path]:
        yield self.student_build_folder_fullpath(student_id)


class ProjectIO:
    _logger = create_logger()

    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def unlink(self, path: Path):
        assert path.is_absolute(), path
        assert path.is_relative_to(self._project_path_provider.project_folder_fullpath()), path
        self._logger.info(f"unlink {path!s}")
        path.unlink(missing_ok=False)

    def rmtree(self, path: Path):
        assert path.is_absolute(), path
        assert path.is_relative_to(self._project_path_provider.project_folder_fullpath()), path
        self._logger.info(f"rmtree {path!s}")
        shutil.rmtree(path)

    # def move_folder(self, src_path: Path, dst_path: Path):
    #     assert src_path.is_absolute(), src_path
    #     assert src_path.is_relative_to(
    #         self._project_path_provider.project_folder_fullpath()), src_path
    #     assert dst_path.is_absolute(), dst_path
    #     assert dst_path.is_relative_to(
    #         self._project_path_provider.project_folder_fullpath()), dst_path
    #     src_path.rename(dst_path)

    def write_json(self, *, json_fullpath: Path, body):
        assert json_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), json_fullpath
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        with json_fullpath.open(mode="w", encoding="utf-8") as f:
            json.dump(
                body,
                f,
                indent=2,
                ensure_ascii=False,
            )

    def read_json(self, *, json_fullpath: Path) -> Optional:
        assert json_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), json_fullpath
        with json_fullpath.open(mode="r", encoding="utf-8") as f:
            return json.load(f)

    def create_project_folder(self) -> None:
        self._project_path_provider.project_folder_fullpath().mkdir(parents=True, exist_ok=False)

    def write_config(self, *, project_config: ProjectConfig):
        project_config_json_fullpath = self._project_path_provider.project_config_json_fullpath()
        self.write_json(
            json_fullpath=project_config_json_fullpath,
            body=project_config.to_json(),
        )

    @functools.cache
    def read_config(self) -> ProjectConfig:
        project_config_json_fullpath = self._project_path_provider.project_config_json_fullpath()
        body = self.read_json(
            json_fullpath=project_config_json_fullpath,
        )
        assert body is not None, project_config_json_fullpath
        return ProjectConfig.from_json(body)

    def write_student_master(self, student_master: StudentMaster):
        student_master_json_fullpath = self._project_path_provider.student_master_json_fullpath()
        self.write_json(
            json_fullpath=student_master_json_fullpath,
            body=student_master.to_json(),
        )

    def read_student_master(self) -> StudentMaster:
        student_master_json_fullpath = self._project_path_provider.student_master_json_fullpath()
        body = self.read_json(
            json_fullpath=student_master_json_fullpath,
        )
        assert body is not None, student_master_json_fullpath
        return StudentMaster.from_json(body)

    @functools.cached_property
    def students(self) -> StudentMaster:
        return self.read_student_master()

    def get_project_name(self) -> ProjectName:
        return ProjectName(self._project_path_provider.project_folder_fullpath().stem)

    def get_target_id(self) -> TargetID:
        return self.read_config().target_id

    def show_student_submission_folder_in_explorer(self, student_id: StudentID) -> None:
        submission_folder_fullpath \
            = self._project_path_provider.student_submission_folder_fullpath(student_id)
        os.startfile(submission_folder_fullpath)

    def iter_student_source_file_relative_path_in_submission_folder(
            self,
            *,
            student_id: StudentID,
            target_id: TargetID,
    ) -> list[Path]:  # returns paths relative to student submission folder
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
                           f"設問番号とみられる数字が複数含まれています: {', '.join(numbers_str)}",
                )
            elif len(numbers_str) == 0:
                raise ProjectIOError(
                    reason=f"ファイル名{relative_path!s}から設問番号を判別できません。\n"
                           f"設問番号とみられる数字が含まれていません。",
                )
            number = int(numbers_str[0])

            # 該当する設問の場合は結果に追加
            if TargetID(number) != target_id:
                continue
            source_file_fullpath_lst.append(relative_path)

        return source_file_fullpath_lst

    def get_student_submission_file_content_bytes(self, student_id: StudentID,
                                                  relative_path: Path) -> bytes:
        student_submission_folder_fullpath \
            = self._project_path_provider.student_submission_folder_fullpath(student_id)
        source_file_fullpath = student_submission_folder_fullpath / relative_path
        with source_file_fullpath.open(mode="rb") as f:
            return f.read()

    def put_student_target_source_file(self, student_id: StudentID, content_str: str) -> None:
        student_build_folder_fullpath = self._project_path_provider.student_build_folder_fullpath(
            student_id=student_id,
        )
        if student_build_folder_fullpath.exists():
            self.rmtree(student_build_folder_fullpath)
        student_target_source_file_fullpath \
            = self._project_path_provider.student_target_source_file_fullpath(student_id)
        student_target_source_file_fullpath.parent.mkdir(parents=True, exist_ok=True)
        with student_target_source_file_fullpath.open(mode="w", encoding="utf-8") as f:
            f.write(content_str)

    def write_student_build_result(self, student_id: StudentID, result: BuildResult) -> None:
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=student_id,
        )
        self.write_json(
            json_fullpath=result_json_fullpath,
            body=result.to_json(),
        )

    def is_student_build_finished(self, student_id: StudentID) -> bool:
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=student_id,
        )
        return result_json_fullpath.exists()

    def read_student_build_result(self, student_id: StudentID) -> BuildResult:
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=student_id,
        )
        result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        body = self.read_json(
            json_fullpath=result_json_fullpath,
        )
        assert body is not None, result_json_fullpath
        return BuildResult.from_json(body)

    def get_student_compile_target_fullpath(self, student_id: StudentID) -> Path:
        compile_target_fullpath = self._project_path_provider.student_target_source_file_fullpath(
            student_id=student_id
        )
        if not compile_target_fullpath.exists():
            raise ProjectIOError(
                reason=f"コンパイル対象のファイルが存在しません: {compile_target_fullpath!s}"
            )
        return compile_target_fullpath

    def write_student_compile_result(self, student_id: StudentID, result: CompileResult) -> None:
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=student_id,
        )
        self.write_json(
            json_fullpath=result_json_fullpath,
            body=result.to_json(),
        )

    def is_student_compile_finished(self, student_id: StudentID) -> bool:
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=student_id,
        )
        return result_json_fullpath.exists()

    def read_student_compile_result(self, student_id: StudentID) -> CompileResult:
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=student_id,
        )
        result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        body = self.read_json(
            json_fullpath=result_json_fullpath,
        )
        assert body is not None, result_json_fullpath
        return CompileResult.from_json(body)

    def get_student_mtime(self, student_id: StudentID) -> datetime | None:
        mtime_max = None
        for folder_fullpath in \
                self._project_path_provider.iter_student_dynamic_folder_fullpath(student_id):
            if not folder_fullpath.exists():
                return None
            mtime = folder_fullpath.stat().st_mtime
            if mtime_max is None or mtime > mtime_max:
                mtime_max = mtime
        return mtime_max and datetime.fromtimestamp(mtime_max)

    def clear_student(self, student_id: StudentID) -> None:
        for student_dynamic_folder_fullpath in \
                self._project_path_provider.iter_student_dynamic_folder_fullpath(student_id):
            self.rmtree(student_dynamic_folder_fullpath)
