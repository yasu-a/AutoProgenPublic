import io
import json
import os
import shutil
from pathlib import Path
from typing import Optional, TextIO

from app_logging import create_logger
from domain.models.testcase import TestCaseConfig
from domain.models.values import TestCaseID, StudentID
from files.project import ProjectPathProvider


class TestCaseIO:
    _logger = create_logger()

    def __init__(self, *, project_path_provider: ProjectPathProvider):
        self._project_path_provider = project_path_provider

    def open_in_explorer(self) -> None:
        testcase_folder_fullpath \
            = self._project_path_provider.testcase_folder_fullpath()
        testcase_folder_fullpath.mkdir(parents=True, exist_ok=True)
        os.startfile(testcase_folder_fullpath)

    def list_ids(self) -> list[TestCaseID]:
        testcase_folder_fullpath \
            = self._project_path_provider.testcase_folder_fullpath()
        testcase_folder_fullpath.mkdir(parents=True, exist_ok=True)
        id_lst = []
        for path in testcase_folder_fullpath.iterdir():
            if path.is_file() and path.suffix == ".json":
                id_lst.append(TestCaseID(path.stem))
        return id_lst

    # TODO: move ProjectCoreIO methods in ProjectIO and use that instead
    def _unlink(self, path: Path) -> None:
        # プロジェクト内のファイルを削除する
        assert path.is_absolute(), path
        assert path.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), path
        self._logger.info(f"unlink {path!s}")
        path.unlink(missing_ok=False)

    # TODO: move ProjectCoreIO methods in ProjectIO and use that instead
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

    # TODO: move ProjectCoreIO methods in ProjectIO and use that instead
    def _read_json(self, *, json_fullpath: Path) -> Optional:
        # プロジェクト内のパスからjsonを読み出す
        assert json_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), json_fullpath
        with json_fullpath.open(mode="r", encoding="utf-8") as f:
            return json.load(f)

    # TODO: move ProjectCoreIO methods in ProjectIO and use that instead
    def _touch(self, *, fullpath: Path, content: bytes = b""):
        # プロジェクト内のパスにファイルを作る
        assert fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), fullpath
        fullpath.parent.mkdir(parents=True, exist_ok=True)
        with fullpath.open(mode="wb") as f:
            f.write(content)

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

    def _read_file_content(self, *, filepath: Path) -> str:
        # プロジェクト内のテキストファイルを読み出す
        assert filepath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), filepath
        with filepath.open(mode="r", encoding="utf-8") as f:
            return f.read()

    def read_config(self, testcase_id: TestCaseID) -> TestCaseConfig:
        json_fullpath = self._project_path_provider.testcase_config_json_fullpath(
            testcase_id=testcase_id,
        )
        json_body = self._read_json(json_fullpath=json_fullpath)
        return TestCaseConfig.from_json(json_body)

    def create_config(self, testcase_id: TestCaseID) -> None:
        config = TestCaseConfig.create_new()
        self.write_config(testcase_id=testcase_id, config=config)

    def delete_config(self, testcase_id: TestCaseID) -> None:
        json_fullpath = self._project_path_provider.testcase_config_json_fullpath(
            testcase_id=testcase_id,
        )
        self._unlink(path=json_fullpath)

    def write_config(self, testcase_id: TestCaseID, config: TestCaseConfig) -> None:
        json_fullpath = self._project_path_provider.testcase_config_json_fullpath(
            testcase_id=testcase_id,
        )
        self._write_json(json_fullpath=json_fullpath, body=config.to_json())

    def clone_student_executable_to_test_folder(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> None:
        """
        生徒の実行ファイルをテスト用のフォルダにコピーする

        :param student_id: 生徒ID
        :param testcase_id: テストケースID
        """

        # 生徒の実行ファイルのフルパス
        student_executable_fullpath = self._project_path_provider.student_executable_fullpath(
            student_id=student_id,
        )
        # 生徒のテストフォルダの実行ファイルのフルパス
        student_test_executable_fullpath = self._project_path_provider.student_test_executable_fullpath(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        # テストフォルダがない場合は生成する
        student_test_executable_fullpath.parent.mkdir(parents=True, exist_ok=True)
        # コピーする
        self._copy_file_into_folder(
            src_file_fullpath=student_executable_fullpath,
            dst_folder_fullpath=student_test_executable_fullpath.parent,
            dst_file_name=student_test_executable_fullpath.name,
        )

    def create_input_files_to_test_folder(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> None:
        """
        テストケースの入力ファイルを生徒のテスト用フォルダに生成する

        :param student_id: 生徒ID
        :param testcase_id: テストケースID
        """

        # 生徒のテストフォルダのフルパス
        student_test_folder_fullpath = self._project_path_provider.student_test_folder_fullpath(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        # テストフォルダがない場合は生成する
        student_test_folder_fullpath.mkdir(parents=True, exist_ok=True)
        # テストケースの入力ファイルを生成する
        config = self.read_config(testcase_id=testcase_id)
        for filename in config.execute_config.iter_normal_filenames():
            content_bytes = config.execute_config.input_files[filename]
            self._touch(
                fullpath=student_test_folder_fullpath / filename,
                content=content_bytes,
            )
        # 標準入力があればファイルとして作成する
        if config.execute_config.has_stdin():
            student_test_stdin_fullpath = self._project_path_provider.student_test_stdin_fullpath(
                student_id=student_id,
                testcase_id=testcase_id,
            )
            self._touch(
                fullpath=student_test_stdin_fullpath,
                content=config.execute_config.input_files[None],
            )

    def get_stdin_fp(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> TextIO:
        """
        標準入力を開いてファイルポインタを返す

        :param student_id: 生徒ID
        :param testcase_id: テストケースID
        :return: 標準入力のI/O，存在しなければNone
        """

        # 標準入力のパス
        stdin_fullpath = self._project_path_provider.student_test_stdin_fullpath(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        # 存在しなければ空のストリームを返す
        if not stdin_fullpath.exists():
            return io.TextIOWrapper(io.BytesIO(b""), encoding='utf-8')
        # ファイルを開いて返す
        return stdin_fullpath.open(mode="r", encoding="utf-8")

    def get_executable_fullpath_if_exists(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> Path | None:
        """
        実行可能ファイルのフルパスを返す

        :param student_id: 生徒ID
        :param testcase_id: テストケースID
        :return: 実行可能ファイルのパス，存在しなければNone
        """

        # 生徒のテストフォルダのフルパス
        executable_fullpath = self._project_path_provider.student_test_executable_fullpath(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        # 存在しなければNoneを返す
        if not executable_fullpath.exists():
            return None
        # 存在する場合は実行可能ファイルのパスを返す
        return executable_fullpath

    def dump_stdout(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
            stdout_text: str,
    ) -> None:
        """
        stdoutのテキストをダンプする

        :param student_id: 生徒ID
        :param testcase_id: テストケースID
        :param stdout_text: stdoutのテキスト
        """

        # 生徒のテストフォルダの標準出力のフルパス
        stdout_fullpath = self._project_path_provider.student_test_stdout_fullpath(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        # 生徒のテストフォルダがない場合は生成する
        stdout_fullpath.parent.mkdir(parents=True, exist_ok=True)
        # stdoutのテキストをファイルに書き出す
        with stdout_fullpath.open(mode="w", encoding="utf-8") as f:
            f.write(stdout_text)

# class TestCaseConfigError(ValueError):
#     def __init__(
#             self,
#             fetal: bool,
#             reason: str,
#             target_index: int | None,
#             testcase_index: int | None,
#     ):
#         self.fetal = fetal
#         self.reason = reason
#         self.target_index = target_index
#         self.testcase_index = testcase_index
#
#
# @dataclass
# class _TestCaseDefinitionFileFullpathSet:
#     input_fullpath: str | None
#     output_fullpath: str
#     config_fullpath: str | None
#
#     def __iter__(self):
#         yield self.input_fullpath
#         yield self.output_fullpath
#         yield self.config_fullpath
#
#
# class TestCaseIO:
#     def __init__(self, *, testcase_dir_fullpath):
#         self.__testcase_dir_fullpath = testcase_dir_fullpath
#
#     @property
#     def _testcase_dir_fullpath(self):
#         os.makedirs(self.__testcase_dir_fullpath, exist_ok=True)
#         return self.__testcase_dir_fullpath
#
#     def list_target_numbers(self) -> list[int]:
#         indexes = []
#         for name in os.listdir(self._testcase_dir_fullpath):
#             if re.fullmatch(r"\d+", name):
#                 indexes.append(int(name))
#         return indexes
#
#     def _target_fullpath(self, index: int) -> str:
#         return os.path.join(self._testcase_dir_fullpath, str(index))
#
#     def get_expected_new_target_index(self) -> int:
#         target_indexes = self.list_target_numbers()
#         for i in range(1, 100):
#             if i not in target_indexes:
#                 return i
#         return 0
#
#     def add_target_index(self, index: int) -> bool:
#         target_fullpath = self._target_fullpath(index)
#         if os.path.exists(target_fullpath):
#             return False
#         os.makedirs(target_fullpath, exist_ok=False)
#         return True
#
#     def get_expected_new_testcase_index(self, target_index: int) -> int:
#         testcases = self.validate_and_list_testcases(target_index)
#         testcase_numbers = {testcase.number for testcase in testcases}
#         for i_testcase in itertools.count():
#             if i_testcase == 0:
#                 continue
#             if i_testcase not in testcase_numbers:
#                 return i_testcase
#
#     def add_testcase_index(self, target_number: int, testcase_number: int):
#         testcase = TestCase.create_empty(testcase_number)
#         self.set_testcase(
#             target_number=target_number,
#             testcase_number=testcase_number,
#             testcase=testcase,
#             context="create"
#         )
#
#     def _get_testcase_definition_file_fullpath_mapping_with_errors(self, target_index: int) \
#             -> dict[int, _TestCaseDefinitionFileFullpathSet]:  # testcase_index -> fullpath set
#         input_fullpath_mapping: dict[int, str] = {}  # testcase_index -> fullpath
#         output_fullpath_mapping: dict[int, str] = {}  # testcase_index -> fullpath
#         config_fullpath_mapping: dict[int, str] = {}  # testcase_index -> fullpath
#
#         target_fullpath = self._target_fullpath(target_index)
#         for filename in os.listdir(target_fullpath):
#             filename_except_ext, ext = os.path.splitext(filename)
#             testcase_fullpath = os.path.join(target_fullpath, filename)
#
#             # config .json or testcase .txt
#             is_json = ext == ".json"
#
#             # input or output
#             is_input = "input" in filename.lower()
#             is_output = "output" in filename.lower()
#             if not is_json and (not is_input and not is_output):
#                 raise TestCaseConfigError(
#                     fetal=True,
#                     reason=f"設問{target_index:02}のテストケース定義ファイル\"{filename}\"の種別を認識できません",
#                     target_index=target_index,
#                     testcase_index=None,
#                 )
#
#             # testcase index
#             numbers = re.findall(r"\d+", filename)
#             if len(numbers) == 0:
#                 raise TestCaseConfigError(
#                     fetal=True,
#                     reason=f"設問{target_index:02}のテストケース定義ファイルの名前\"{filename}\"はテストケース番号として1つだけ数字を含んでいる必要があります",
#                     target_index=target_index,
#                     testcase_index=None,
#                 )
#             testcase_number = int(numbers[0])
#
#             if is_json:
#                 dct = config_fullpath_mapping
#                 filetype_text = "テストケースの構成記述ファイル"
#             else:
#                 if is_input:
#                     dct = input_fullpath_mapping
#                     filetype_text = "テストケースの入力定義ファイル"
#                 else:
#                     dct = output_fullpath_mapping
#                     filetype_text = "テストケースの出力定義ファイル"
#
#             if testcase_number in dct:
#                 raise TestCaseConfigError(
#                     fetal=True,
#                     reason=f"テストケース番号 {testcase_number} に {filetype_text} が2個以上定義されています",
#                     target_index=target_index,
#                     testcase_index=testcase_number,
#                 )
#
#             dct[testcase_number] = testcase_fullpath
#
#         fullpath_mapping: dict[int, _TestCaseDefinitionFileFullpathSet] \
#             = {}  # target_number -> TestCaseDefinitionFileFullpathSet
#         for testcase_number in list(output_fullpath_mapping.keys()):
#             # output
#             output_fullpath = output_fullpath_mapping.pop(testcase_number)
#
#             # input
#             input_fullpath = input_fullpath_mapping.get(testcase_number)
#             if input_fullpath is not None:
#                 input_fullpath_mapping.pop(testcase_number)
#
#             # config
#             config_fullpath = config_fullpath_mapping.get(testcase_number)
#             if config_fullpath is not None:
#                 config_fullpath_mapping.pop(testcase_number)
#
#             fullpath_set = _TestCaseDefinitionFileFullpathSet(
#                 output_fullpath=output_fullpath,
#                 input_fullpath=input_fullpath,
#                 config_fullpath=config_fullpath,
#             )
#             fullpath_mapping[testcase_number] = fullpath_set
#
#         for testcase_number, fullpath in input_fullpath_mapping.items():
#             raise TestCaseConfigError(
#                 fetal=False,
#                 reason=f"出力が定義されていないテストケースを無視しました：{fullpath}",
#                 target_index=target_index,
#                 testcase_index=testcase_number,
#             )
#
#         for testcase_number, fullpath in config_fullpath_mapping.items():
#             raise TestCaseConfigError(
#                 fetal=False,
#                 reason=f"出力が定義されていないテストケースを無視しました：{fullpath}",
#                 target_index=target_index,
#                 testcase_index=testcase_number,
#             )
#
#         assert not output_fullpath_mapping, output_fullpath_mapping
#
#         return fullpath_mapping
#
#     def _get_testcase_definition_file_fullpath_mapping_ignore_errors(self, target_index: int) \
#             -> dict[int, _TestCaseDefinitionFileFullpathSet]:
#         try:
#             fullpath_mapping = self._get_testcase_definition_file_fullpath_mapping_with_errors(
#                 target_index=target_index,
#             )
#         except TestCaseConfigError:
#             return {}
#         else:
#             return fullpath_mapping
#
#     def _get_testcase_definition_file_fullpath_ignore_errors(
#             self,
#             target_index: int,
#             testcase_index: int,
#     ) -> _TestCaseDefinitionFileFullpathSet:
#         fullpath_mapping = self._get_testcase_definition_file_fullpath_mapping_ignore_errors(
#             target_index=target_index,
#         )
#         return fullpath_mapping[testcase_index]
#
#     # TODO: 廃止→TestSessionを返すやつに乗りかえないとおかしい
#     def validate_and_list_testcases(self, target_index: int) -> list[TestCase]:
#         fullpath_mapping = self._get_testcase_definition_file_fullpath_mapping_with_errors(
#             target_index=target_index,
#         )
#
#         testcases: dict[int, TestCase] = {}
#         for testcase_number, fullpath_set in fullpath_mapping.items():
#             testcase = TestCase.create_empty(testcase_number)
#
#             # output
#             fullpath = fullpath_set.output_fullpath
#             with codecs.open(fullpath, "r", "utf-8") as f:
#                 testcase.expected_output = f.read()
#
#             # input
#             fullpath = fullpath_set.input_fullpath
#             if fullpath is not None:
#                 with codecs.open(fullpath, "r", "utf-8") as f:
#                     testcase.expected_input = f.read()
#
#             # config
#             fullpath = fullpath_set.config_fullpath
#             if fullpath is not None:
#                 with codecs.open(fullpath, "r", "utf-8") as f:
#                     try:
#                         body = json.load(f)
#                     except json.decoder.JSONDecodeError as e:
#                         raise TestCaseConfigError(
#                             fetal=True,
#                             reason=f"構成定義ファイルのJSONに構文エラーがあります：{e.msg}",
#                             target_index=target_index,
#                             testcase_index=testcase_number,
#                         )
#                 try:
#                     testcase.config = TestCaseConfig.from_json(body)
#                 except (TypeError, ValueError, KeyError) as e:
#                     raise TestCaseConfigError(
#                         fetal=True,
#                         reason=f"構成定義ファイルのJSONに不正なデータが存在します：{e} {''.join(e.args)}",
#                         target_index=target_index,
#                         testcase_index=testcase_number,
#                     )
#
#             testcases[testcase_number] = testcase
#
#         return [v for k, v in sorted(testcases.items(), key=lambda x: x[0])]
#
#     def validate_and_get_test_session(self, target_index: int) -> TestSession:
#         testcases = self.validate_and_list_testcases(target_index)
#         test_session = TestSession(
#             testcases=testcases,
#         )
#         return test_session
#
#     def get_testcase(self, target_number: int, testcase_number: int) -> TestCase | None:
#         test_session = self.validate_and_get_test_session(target_number)
#         return test_session.get_testcase_by_number(testcase_number)
#
#     def set_testcase(
#             self,
#             target_number: int,
#             testcase_number: int,
#             testcase: TestCase,
#             context: Literal["create", "replace"],
#     ):
#         target_fullpath = self._target_fullpath(target_number)
#
#         fullpath_set = _TestCaseDefinitionFileFullpathSet(
#             output_fullpath=os.path.join(target_fullpath, f"output-{testcase_number}.txt"),
#             input_fullpath=os.path.join(target_fullpath, f"input-{testcase_number}.txt"),
#             config_fullpath=os.path.join(target_fullpath, f"config-{testcase_number}.json"),
#         )
#         if context == "create":
#             for fullpath in fullpath_set:
#                 assert not os.path.exists(fullpath), fullpath
#         elif context == "add":
#             assert os.path.exists(fullpath_set.output_fullpath), fullpath_set.output_fullpath
#
#         with codecs.open(fullpath_set.input_fullpath, "w", "utf-8") as f:
#             f.write(testcase.expected_input)
#         with codecs.open(fullpath_set.output_fullpath, "w", "utf-8") as f:
#             f.write(testcase.expected_output)
#         with codecs.open(fullpath_set.config_fullpath, "w", "utf-8") as f:
#             json.dump(testcase.config.to_json(), f, indent=2, ensure_ascii=False)
#
#     def get_revision_hash(self) -> int | None:
#         mtime_mapping: dict[str, float] = {}  # fullpath -> mtime
#         for dirpath, dirnames, filenames in os.walk(self._testcase_dir_fullpath):
#             for name in itertools.chain(dirnames, filenames):
#                 fullpath: str = os.path.join(dirpath, name)  # type: ignore
#                 mtime = os.path.getmtime(fullpath)
#                 mtime_mapping[fullpath] = mtime
#         if mtime_mapping:
#             sorted_mtime_mapping = tuple(sorted(mtime_mapping.items(), key=lambda x: x[0]))
#             revision_hash = hash(sorted_mtime_mapping)
#             return revision_hash
#         else:
#             return None
#
#     def open_target_in_explorer(self, target_index: int):
#         os.startfile(self._target_fullpath(target_index))
#
#     def delete_target(self, target_index: int):
#         target_fullpath = self._target_fullpath(target_index)
#         shutil.rmtree(target_fullpath)
#
#     def delete_testcase(self, target_number: int, testcase_number: int):
#         fullpath_set = self._get_testcase_definition_file_fullpath_ignore_errors(
#             target_index=target_number,
#             testcase_index=testcase_number,
#         )
#         for definition_file_fullpath in fullpath_set:
#             if definition_file_fullpath is not None:
#                 os.remove(definition_file_fullpath)
