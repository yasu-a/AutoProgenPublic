import functools
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterable

from app_logging import create_logger
from domain.errors import ProjectIOError
from domain.models.project_config import ProjectConfig
from domain.models.reuslts import BuildResult, CompileResult, ExecuteResult
from domain.models.student_master import StudentMaster
from domain.models.values import ProjectName, TargetID, StudentID, TestCaseID


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

    # プロジェクト
    def project_folder_fullpath(self) -> Path:
        return self._base

    def project_config_json_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "config.json"

    # 提出レポート
    def report_folder_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "reports"

    def student_submission_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.report_folder_fullpath() / f"{student_id}"

    # 提出レポートに付属するマスターデータ
    def student_master_excel_fullpath(self) -> Path:
        return self.report_folder_fullpath() / "reportlist.xlsx"

    def student_master_json_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "student_master.json"

    # ビルド
    def build_folder_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "build"

    def student_build_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.build_folder_fullpath() / str(student_id)

    def student_target_source_file_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "main.c"

    def student_build_result_json_fullpath(self,
                                           student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "__build_result.json"

    # コンパイル
    def student_executable_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "main.exe"

    def student_compile_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self.student_build_folder_fullpath(student_id) / "__compile_result.json"

    # テストケース構成
    def testcase_folder_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "testcase"

    def testcase_config_json_fullpath(self, testcase_id: TestCaseID) -> Path:
        return self.testcase_folder_fullpath() / f"{testcase_id}.json"

    # テスト実行
    def test_folder_fullpath(self) -> Path:
        return self.project_folder_fullpath() / "test"

    def student_test_base_folder_fullpath(self, student_id: StudentID) -> Path:
        return self.test_folder_fullpath() / str(student_id)

    def student_test_folder_fullpath(self, student_id: StudentID,
                                     testcase_id: TestCaseID) -> Path:
        return self.student_test_base_folder_fullpath(student_id) / str(testcase_id)

    def student_execute_result_json_fullpath(self, student_id: StudentID) -> Path:
        return self.student_test_base_folder_fullpath(student_id) / "__execute_result.json"

    def student_test_stdin_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.student_test_folder_fullpath(student_id, testcase_id) / "__stdin__"

    def student_test_stdout_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.student_test_folder_fullpath(student_id, testcase_id) / "__stdout__"

    def student_test_executable_fullpath(self, student_id, testcase_id: TestCaseID):
        return self.student_test_folder_fullpath(student_id, testcase_id) / "main.exe"

    # その他
    def iter_student_dynamic_folder_fullpath(self, student_id: StudentID) -> Iterable[Path]:
        # 生徒のプロジェクトデータの最終更新時刻を確認するフォルダのパスをイテレートする
        build_folder_fullpath = self.student_build_folder_fullpath(student_id)
        yield build_folder_fullpath

        test_base_folder_fullpath = self.student_test_base_folder_fullpath(student_id)
        yield test_base_folder_fullpath
        if test_base_folder_fullpath.exists():
            for path in test_base_folder_fullpath.iterdir():
                if path.is_dir():
                    yield path


class ProjectIO:
    _logger = create_logger()

    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def _unlink(self, path: Path) -> None:
        # プロジェクト内のファイルを削除する
        assert path.is_absolute(), path
        assert path.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), path
        self._logger.info(f"unlink {path!s}")
        path.unlink(missing_ok=False)

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def rmtree(self, path: Path) -> None:
        # プロジェクト内のフォルダを削除する
        assert path.is_absolute(), path
        assert path.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), path
        self._logger.info(f"rmtree {path!s}")
        shutil.rmtree(path)

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def _copy_file_into_folder(
            self,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str = None,
    ) -> None:
        # プロジェクト内のファイルをプロジェクト内のフォルダにコピーする
        assert src_file_fullpath.is_absolute(), src_file_fullpath
        assert src_file_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), src_file_fullpath
        assert src_file_fullpath.is_file(), src_file_fullpath
        assert dst_folder_fullpath.is_absolute(), dst_folder_fullpath
        assert dst_folder_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), dst_folder_fullpath
        assert dst_folder_fullpath.is_dir(), dst_folder_fullpath
        if dst_file_name is None:
            dst_file_name = src_file_fullpath.name
        shutil.copy(src_file_fullpath, dst_folder_fullpath / dst_file_name)

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def _copy_files_in_folder_into_folder(
            self,
            src_folder_fullpath: Path,
            dst_folder_fullpath: Path,
    ) -> None:
        # プロジェクト内のフォルダのすべてのファイルをプロジェクト内のフォルダにコピーする
        assert src_folder_fullpath.is_absolute(), src_folder_fullpath
        assert src_folder_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), src_folder_fullpath
        assert src_folder_fullpath.is_file(), src_folder_fullpath
        assert dst_folder_fullpath.is_absolute(), dst_folder_fullpath
        assert dst_folder_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), dst_folder_fullpath
        assert dst_folder_fullpath.is_dir(), dst_folder_fullpath
        for src_fullpath in dst_folder_fullpath.iterdir():
            if src_fullpath.is_file():
                self._copy_file_into_folder(src_fullpath, dst_folder_fullpath)
            elif src_fullpath.is_dir():
                self._copy_files_in_folder_into_folder(src_fullpath,
                                                       dst_folder_fullpath / src_fullpath.name)

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def _copy_folder(self, src_path: Path, dst_path: Path) -> None:
        # プロジェクト内のフォルダをコピーする
        assert src_path.is_absolute(), src_path
        assert src_path.is_relative_to(
            self._project_path_provider.project_folder_fullpath()), src_path
        assert dst_path.is_absolute(), dst_path
        assert dst_path.is_relative_to(
            self._project_path_provider.project_folder_fullpath()), dst_path
        shutil.copytree(src_path, dst_path)

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def _write_json(self, *, json_fullpath: Path, body):
        # プロジェクト内のパスにjsonを書き込む
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

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def _read_json(self, *, json_fullpath: Path) -> Optional:
        # プロジェクト内のパスからjsonを読み出す
        assert json_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), json_fullpath
        with json_fullpath.open(mode="r", encoding="utf-8") as f:
            return json.load(f)

    def create_project_folder(self) -> None:
        # プロジェクトフォルダを作る
        self._project_path_provider.project_folder_fullpath() \
            .mkdir(parents=True, exist_ok=False)

    def write_config(self, *, project_config: ProjectConfig):
        # プロジェクトの構成を永続化する
        project_config_json_fullpath = self._project_path_provider.project_config_json_fullpath()
        self._write_json(
            json_fullpath=project_config_json_fullpath,
            body=project_config.to_json(),
        )

    @functools.cache
    def read_config(self) -> ProjectConfig:
        # プロジェクトの構成を読み込む
        project_config_json_fullpath = self._project_path_provider.project_config_json_fullpath()
        body = self._read_json(
            json_fullpath=project_config_json_fullpath,
        )
        assert body is not None, project_config_json_fullpath
        return ProjectConfig.from_json(body)

    def write_student_master(self, student_master: StudentMaster):
        # 生徒マスターを永続化する
        student_master_json_fullpath = self._project_path_provider.student_master_json_fullpath()
        self._write_json(
            json_fullpath=student_master_json_fullpath,
            body=student_master.to_json(),
        )

    def read_student_master(self) -> StudentMaster:
        # 生徒マスターを読み込む
        student_master_json_fullpath = self._project_path_provider.student_master_json_fullpath()
        body = self._read_json(
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
        # 生徒の提出フォルダにある指定されたファイルの中身を取得する
        student_submission_folder_fullpath \
            = self._project_path_provider.student_submission_folder_fullpath(student_id)
        source_file_fullpath = student_submission_folder_fullpath / relative_path
        with source_file_fullpath.open(mode="rb") as f:
            return f.read()

    def get_student_mtime(self, student_id: StudentID) -> datetime | None:
        # 生徒のプロジェクトデータの最終更新日時を取得する
        mtime_max = None
        for folder_fullpath \
                in self._project_path_provider.iter_student_dynamic_folder_fullpath(student_id):
            if not folder_fullpath.exists():
                continue
            mtime = folder_fullpath.stat().st_mtime
            if mtime_max is None or mtime > mtime_max:
                mtime_max = mtime
        return mtime_max and datetime.fromtimestamp(mtime_max)

    def clear_student(self, student_id: StudentID) -> None:
        # 生徒のすべてのプロジェクトデータを削除する
        for student_dynamic_folder_fullpath in \
                self._project_path_provider.iter_student_dynamic_folder_fullpath(student_id):
            if not student_dynamic_folder_fullpath.exists():
                continue
            self.rmtree(student_dynamic_folder_fullpath)

    def put_student_target_source_file(self, student_id: StudentID, content_str: str) -> None:
        # 生徒のビルドフォルダにソースコードを書きこむ
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
        # 生徒のビルド結果を永続化する
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=student_id,
        )
        self._write_json(
            json_fullpath=result_json_fullpath,
            body=result.to_json(),
        )

    def is_student_build_finished(self, student_id: StudentID) -> bool:
        # 生徒のビルドが終了したかどうかを確認する
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=student_id,
        )
        return result_json_fullpath.exists()

    def read_student_build_result(self, student_id: StudentID) -> BuildResult:
        # 生徒のビルド結果を読み込む
        result_json_fullpath = self._project_path_provider.student_build_result_json_fullpath(
            student_id=student_id,
        )
        result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        body = self._read_json(
            json_fullpath=result_json_fullpath,
        )
        assert body is not None, result_json_fullpath
        return BuildResult.from_json(body)

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

    def write_student_compile_result(self, student_id: StudentID, result: CompileResult) -> None:
        # 生徒のコンパイル結果を永続化する
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=student_id,
        )
        self._write_json(
            json_fullpath=result_json_fullpath,
            body=result.to_json(),
        )

    def is_student_compile_finished(self, student_id: StudentID) -> bool:
        # 生徒のコンパイルが終了したかどうかを確認する
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=student_id,
        )
        return result_json_fullpath.exists()

    def read_student_compile_result(self, student_id: StudentID) -> CompileResult:
        # 生徒のコンパイル結果を読み込む
        result_json_fullpath = self._project_path_provider.student_compile_result_json_fullpath(
            student_id=student_id,
        )
        result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        body = self._read_json(
            json_fullpath=result_json_fullpath,
        )
        assert body is not None, result_json_fullpath
        return CompileResult.from_json(body)

    def write_student_execute_result(
            self,
            student_id: StudentID,
            result: ExecuteResult,
    ) -> None:
        # 生徒の実行結果を永続化する
        result_json_fullpath = self._project_path_provider.student_execute_result_json_fullpath(
            student_id=student_id,
        )
        self._write_json(
            json_fullpath=result_json_fullpath,
            body=result.to_json(),
        )

    def is_student_execute_finished(
            self,
            student_id: StudentID,
    ) -> bool:
        # 生徒の実行が終了したかどうかを確認する
        result_json_fullpath = self._project_path_provider.student_execute_result_json_fullpath(
            student_id=student_id,
        )
        return result_json_fullpath.exists()

    def read_student_execute_result(
            self,
            student_id: StudentID,
    ) -> ExecuteResult:
        # 生徒の実行結果を読み込む
        result_json_fullpath = self._project_path_provider.student_execute_result_json_fullpath(
            student_id=student_id,
        )
        result_json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        body = self._read_json(
            json_fullpath=result_json_fullpath,
        )
        assert body is not None, result_json_fullpath
        return ExecuteResult.from_json(body)
