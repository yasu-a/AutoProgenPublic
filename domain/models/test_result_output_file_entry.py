from abc import ABC, abstractmethod

from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.output_file import OutputFile
from domain.models.output_file_test_result import MatchResult
from domain.models.values import FileID


class AbstractTestResultOutputFileEntry(ABC):
    @property
    @abstractmethod
    def file_id(self) -> FileID:
        raise NotImplementedError()

    @property
    @abstractmethod
    def has_actual(self) -> bool:
        # 実行結果の出力ファイルがあったらTrue
        raise NotImplementedError()

    @property
    @abstractmethod
    def has_expected(self) -> bool:
        # テストケースの期待出力ファイルがあったらTrue
        raise NotImplementedError()

    @property
    @abstractmethod
    def actual(self) -> OutputFile:
        # 実行結果の出力ファイルがあったらそれを返し，なかったらエラーを投げる
        raise NotImplementedError()

    @property
    @abstractmethod
    def expected(self) -> ExpectedOutputFile:
        # テストケースの期待出力ファイルがあったらそれを返し，なかったらエラーを投げる
        raise NotImplementedError()

    @property
    @abstractmethod
    def test_result(self) -> MatchResult:
        # テスト結果が存在したらそれを返し，なかったらエラーを投げる
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _get_type_name_str(cls) -> str:
        raise NotImplementedError()

    @abstractmethod
    def _instance_to_json(self) -> dict:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _json_to_instance(cls, body: dict):
        raise NotImplementedError()

    def to_json(self) -> dict:
        return {
            "name": self._get_type_name_str(),
            **self._instance_to_json(),
        }

    @classmethod
    def from_json(cls, body: dict) -> "AbstractTestResultOutputFileEntry":
        for sub_cls in cls.__subclasses__():
            if sub_cls._get_type_name_str() == body["name"]:
                # noinspection PyArgumentList
                return sub_cls._json_to_instance(body)
        assert False, body["name"]

    @property
    def is_test_result_accepted(self) -> bool:  # テストケースが正解かどうか
        # acceptedならTrue, そうでないならFalse, 判定不可ならValueError
        # 実行結果の出力がない
        if self.has_expected and not self.has_actual:
            return False
        # 予期されていない実行結果
        if not self.has_expected and self.has_actual:
            raise ValueError("unexpected output file")
        # テスト結果で判定
        return self.test_result.is_accepted


class TestResultAbsentOutputFileEntry(AbstractTestResultOutputFileEntry):
    @classmethod
    def _get_type_name_str(cls) -> str:
        return "absent"

    def _instance_to_json(self) -> dict:
        return dict(
            file_id=self._file_id.to_json(),
            expected=self._expected.to_json(),
        )

    @classmethod
    def _json_to_instance(cls, body: dict):
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            expected=ExpectedOutputFile.from_json(body["expected"]),
        )

    def __init__(
            self,
            file_id: FileID,
            expected: ExpectedOutputFile,
    ):
        self._file_id = file_id
        self._expected = expected

    @property
    def file_id(self) -> FileID:
        return self._file_id

    @property
    def has_actual(self) -> bool:
        return False

    @property
    def has_expected(self) -> bool:
        return True

    @property
    def actual(self) -> OutputFile:
        raise ValueError("result does not have actual output file")

    @property
    def expected(self) -> ExpectedOutputFile:
        return self._expected

    @property
    def test_result(self) -> MatchResult:
        raise ValueError("result does not have test result")


class TestResultUnexpectedOutputFileEntry(AbstractTestResultOutputFileEntry):
    @classmethod
    def _get_type_name_str(cls) -> str:
        return "unexpected"

    def _instance_to_json(self) -> dict:
        return dict(
            file_id=self._file_id.to_json(),
            actual=self._actual.to_json(),
        )

    @classmethod
    def _json_to_instance(cls, body: dict):
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            actual=OutputFile.from_json(body["actual"]),
        )

    def __init__(
            self,
            file_id: FileID,
            actual: OutputFile,
    ):
        self._file_id = file_id
        self._actual = actual

    @property
    def file_id(self) -> FileID:
        return self._file_id

    @property
    def has_actual(self) -> bool:
        return True

    @property
    def has_expected(self) -> bool:
        return False

    @property
    def actual(self) -> OutputFile:
        return self._actual

    @property
    def expected(self) -> ExpectedOutputFile:
        raise ValueError("result does not have expected output file")

    @property
    def test_result(self) -> MatchResult:
        raise ValueError("result does not have test result")


class TestResultTestedOutputFileEntry(AbstractTestResultOutputFileEntry):
    @classmethod
    def _get_type_name_str(cls) -> str:
        return "tested"

    def _instance_to_json(self) -> dict:
        return dict(
            file_id=self._file_id.to_json(),
            actual=self._actual.to_json(),
            expected=self._expected.to_json(),
            test_result=self._test_result.to_json(),
        )

    @classmethod
    def _json_to_instance(cls, body: dict):
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            actual=OutputFile.from_json(body["actual"]),
            expected=ExpectedOutputFile.from_json(body["expected"]),
            test_result=MatchResult.from_json(body["test_result"]),
        )

    def __init__(
            self,
            file_id: FileID,
            actual: OutputFile,
            expected: ExpectedOutputFile,
            test_result: MatchResult,
    ):
        self._file_id = file_id
        self._actual = actual
        self._expected = expected
        self._test_result = test_result

    @property
    def file_id(self) -> FileID:
        return self._file_id

    @property
    def has_actual(self) -> bool:
        return True

    @property
    def has_expected(self) -> bool:
        return True

    @property
    def actual(self) -> OutputFile:
        return self._actual

    @property
    def expected(self) -> ExpectedOutputFile:
        return self._expected

    @property
    def test_result(self) -> MatchResult:
        return self._test_result
