from dataclasses import dataclass

from domain.models.result_base import AbstractResult
from domain.models.values import TestCaseID, FileID
from dto.testcase_execute_config_mapping import TestCaseExecuteConfigMapping, \
    TestCaseExecuteConfigHashMapping
from utils.json_util import bytes_to_jsonable, jsonable_to_bytes


# noinspection DuplicatedCode
class OutputFile:
    def __init__(
            self,
            *,
            file_id: FileID,
            content: bytes | str,
    ):
        self._file_id = file_id
        if isinstance(content, str):
            self._content = bytes(content, encoding="utf-8")
        else:
            self._content = content

    def to_json(self) -> dict:
        return dict(
            file_id=self._file_id.to_json(),
            content_bytes=bytes_to_jsonable(self._content),
        )

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            content=jsonable_to_bytes(body["content_bytes"]),
        )

    @property
    def file_id(self) -> FileID:
        return self._file_id

    @property
    def content_bytes(self) -> bytes:
        return self._content

    @property
    def content_string(self) -> str | None:  # None if encoding unsupported
        try:
            return self._content.decode("utf-8")
        except UnicodeDecodeError:
            return None


# noinspection DuplicatedCode
class OutputFileMapping(dict[FileID, OutputFile]):
    # TODO: frozendictを導入してこのクラスのインスタンスを持つクラスをすべてdataclass(frozen=True)にする

    def __validate(self):
        # キーとしてのFileIDと値の中のFileIDは一致する
        for file_id, output_file in self.items():
            assert file_id == output_file.file_id, (file_id, output_file)
            # 特殊ファイルは標準出力しかありえない
            if file_id.is_special:
                assert file_id in [FileID.STDOUT], file_id

    def to_json(self) -> dict[str, dict]:
        self.__validate()
        return {
            file_id.to_json(): output_file.to_json()
            for file_id, output_file in self.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        obj = cls({
            FileID.from_json(file_id_str): OutputFile.from_json(output_file_body)
            for file_id_str, output_file_body in body.items()
        })
        obj.__validate()
        return obj


class TestCaseExecuteResult:
    def __init__(
            self,
            *,
            testcase_id: TestCaseID,
            execute_config_hash: int | None,  # None if failed
            output_files: OutputFileMapping,
            reason: str | None = None,
    ):
        self._testcase_id = testcase_id
        self._execute_config_hash = execute_config_hash
        self._output_files = output_files
        self._reason = reason

    def to_json(self) -> dict:
        return dict(
            testcase_id=self._testcase_id.to_json(),
            execute_config_hash=self._execute_config_hash,
            output_files=self._output_files.to_json(),
            reason=self._reason,
        )

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            testcase_id=TestCaseID.from_json(body["testcase_id"]),
            execute_config_hash=body.get("execute_config_hash"),
            output_files=OutputFileMapping.from_json(body["output_files"]),
            reason=body.get("reason"),
        )

    @classmethod
    def error(
            cls,
            *,
            testcase_id: TestCaseID,
            reason: str,
    ) -> "TestCaseExecuteResult":
        return cls(
            testcase_id=testcase_id,
            execute_config_hash=None,
            output_files=OutputFileMapping(),
            reason=reason,
        )

    @classmethod
    def success(
            cls,
            *,
            testcase_id: TestCaseID,
            execute_config_hash: int,
            output_files: OutputFileMapping,
    ) -> "TestCaseExecuteResult":
        return cls(
            testcase_id=testcase_id,
            execute_config_hash=execute_config_hash,
            output_files=output_files,
            reason=None,
        )

    @property
    def testcase_id(self) -> TestCaseID:
        return self._testcase_id

    @property
    def execute_config_hash(self) -> int | None:
        return self._execute_config_hash

    @property
    def output_files(self) -> OutputFileMapping:
        return self._output_files

    @property
    def reason(self) -> str | None:
        return self._reason


class TestCaseExecuteResultMapping(dict[TestCaseID, TestCaseExecuteResult]):
    # TODO: frozendictを導入してこのクラスのインスタンスを持つクラスをすべてdataclass(frozen=True)にする

    def __validate(self):
        for testcase_id, testcase_execute_result in self.items():
            # キーとしてのTestCaseIDと値の中のTestCaseIDは一致する
            assert testcase_id == testcase_execute_result.testcase_id, \
                (testcase_id, testcase_execute_result)

    def to_json(self) -> dict[str, dict]:
        self.__validate()
        return {
            testcase_id.to_json(): testcase_execute_result.to_json()
            for testcase_id, testcase_execute_result in self.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        obj = cls({
            TestCaseID.from_json(testcase_id_str): TestCaseExecuteResult.from_json(
                testcase_execute_result_body
            )
            for testcase_id_str, testcase_execute_result_body in body.items()
        })
        obj.__validate()
        return obj


@dataclass(slots=True)
class ExecuteResult(AbstractResult):
    testcase_result_mapping: TestCaseExecuteResultMapping

    @classmethod
    def error(cls, reason: str) -> "ExecuteResult":
        return cls(reason=reason, testcase_result_mapping=TestCaseExecuteResultMapping())

    @classmethod
    def success(cls, testcase_result_set: TestCaseExecuteResultMapping) -> "ExecuteResult":
        return cls(reason=None, testcase_result_mapping=testcase_result_set)

    def to_json(self) -> dict:
        return dict(
            reason=self.reason,
            testcase_result_set=self.testcase_result_mapping.to_json(),
        )

    @classmethod
    def from_json(cls, body: dict) -> "ExecuteResult":
        return cls(
            reason=body["reason"],
            testcase_result_mapping=TestCaseExecuteResultMapping.from_json(
                body["testcase_result_set"]),
        )

    def get_testcase_execute_config_mapping(self) -> TestCaseExecuteConfigHashMapping:
        testcase_execute_config_hash_mapping = {}
        for testcase_id, testcase_result in self.testcase_result_mapping.items():
            execute_config_hash = testcase_result.execute_config_hash
            if execute_config_hash is not None:
                testcase_execute_config_hash_mapping[testcase_id] = execute_config_hash
        return TestCaseExecuteConfigHashMapping(testcase_execute_config_hash_mapping)

    def has_same_hash_of_testcase_execute_config(
            self,
            testcase_execute_config_mapping: TestCaseExecuteConfigMapping,
    ) -> bool:
        this_hash = self.get_testcase_execute_config_mapping().calculate_hash()
        other_hash = testcase_execute_config_mapping.calculate_hash()
        return this_hash == other_hash
