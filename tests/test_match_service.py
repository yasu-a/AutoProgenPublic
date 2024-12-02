from datetime import timedelta
from typing import Any

import pytest

from application.dependency.services import get_match_get_best_service
from domain.models.output_file_test_result import MatchedToken, NonmatchedToken
from domain.models.pattern import PatternList, TextPattern, FloatPattern, AbstractPattern, \
    SpaceOrEOLPattern
from domain.models.test_config_options import TestConfigOptions
from services.dto.match_result import MatchServiceResult


class _TestCaseBuilder:
    def __init__(self):
        self._test_name: str | None = None
        self._test_config_options: TestConfigOptions | None = None
        self._patterns: list[AbstractPattern] = []
        self._input_and_outputs: dict[str, Any] = {}

        self._tests: dict[str, dict] = {}

    def begin_test(self, name: str):
        self._test_name = name
        return self

    def set_options(self, **fields):
        self._test_config_options = TestConfigOptions(**fields)
        return self

    def add_pattern(self, pattern_type: type[AbstractPattern], **fields):
        # noinspection PyArgumentList
        self._patterns.append(
            pattern_type(index=len(self._patterns), **fields)
        )
        return self

    def add_input_and_output(
            self,
            name: str,
            /,
            *,
            content_text: str,
            matched_tokens: list[tuple[int, int, int]],  # pattern-index, begin, end
            nonmatched_tokens: list[int],  # pattern-index
    ):
        self._input_and_outputs[name] = {
            "content_text": content_text,
            "expected_match_result": MatchServiceResult(
                matched_tokens=[
                    MatchedToken(pattern=self._patterns[index], begin=begin, end=end)
                    for index, begin, end in matched_tokens
                ],
                nonmatched_tokens=[
                    NonmatchedToken(pattern=self._patterns[index])
                    for index in nonmatched_tokens
                ],
                test_execution_timedelta=timedelta(0),
            )
        }
        return self

    def end_test(self):
        assert self._test_name is not None
        assert self._test_config_options is not None
        assert self._patterns
        assert self._input_and_outputs
        self._tests[self._test_name] = dict(
            test_config_options=self._test_config_options,
            patterns=PatternList(self._patterns),
            input_and_outputs=self._input_and_outputs,
        )
        self._test_name = None
        self._test_config_options = None
        self._patterns = []
        self._input_and_outputs = {}
        return self

    def build(self):
        return self._tests


_TESTCASES = (
    _TestCaseBuilder()
    .begin_test("test")
    .set_options(
        float_tolerance=0.0001,
    )
    .add_pattern(TextPattern, is_expected=True, text="a")
    .add_pattern(TextPattern, is_expected=True, text="b")
    .add_pattern(TextPattern, is_expected=True, text="c")
    .add_input_and_output(
        "case-1",
        content_text="abc",
        matched_tokens=[
            (0, 0, 1),
            (1, 1, 2),
            (2, 2, 3),
        ],
        nonmatched_tokens=[],
    )
    .end_test()
    .begin_test("test-1")
    .set_options(
        float_tolerance=0.0001,
    )
    .add_pattern(TextPattern, is_expected=True, text="num1")
    .add_pattern(FloatPattern, is_expected=True, value=1)
    .add_pattern(TextPattern, is_expected=True, text="num2")
    .add_pattern(FloatPattern, is_expected=True, value=2)
    .add_pattern(TextPattern, is_expected=True, text="num3")
    .add_pattern(FloatPattern, is_expected=True, value=3)
    .add_input_and_output(
        "case-1",
        content_text="ｎum1: 1\nnum2: 2\nnum3: 3",
        matched_tokens=[
            (0, 0, 4),
            (1, 6, 7),
            (2, 8, 12),
            (3, 14, 15),
            (4, 16, 20),
            (5, 22, 23),
        ],
        nonmatched_tokens=[],
    )
    .end_test()
    .begin_test("test-2")
    .set_options(
        float_tolerance=0.0001,
    )
    .add_pattern(TextPattern, is_expected=True, text="*")
    .add_pattern(TextPattern, is_expected=True, text="**")
    .add_pattern(TextPattern, is_expected=True, text="***")
    .add_input_and_output(
        "case-1",
        content_text="n:*\n**\n***",
        matched_tokens=[
            (0, 2, 3),
            (1, 4, 6),
            (2, 7, 10),
        ],
        nonmatched_tokens=[],
    )
    .add_input_and_output(
        "case-2",
        content_text="n:*\n**\n***\n****",
        matched_tokens=[
            (0, 2, 3),
            (1, 4, 6),
            (2, 7, 10),
        ],
        nonmatched_tokens=[],
    )
    .add_input_and_output(
        "case-3",
        content_text="n:**\n*\n***\n****",
        matched_tokens=[
            (0, 2, 3),
            (1, 7, 9),
            (2, 11, 14),
        ],
        nonmatched_tokens=[],
    )
    .add_input_and_output(
        "case-4",
        content_text="n:**\n*\n***\n",
        matched_tokens=[
            (1, 2, 4),
            (2, 7, 10),
        ],
        nonmatched_tokens=[
            0,
        ],
    )
    .end_test()
    .begin_test("test-3")
    .set_options(
        float_tolerance=0.0001,
    )
    .add_pattern(TextPattern, is_expected=True, text="*")
    .add_pattern(TextPattern, is_expected=True, text="**")
    .add_pattern(TextPattern, is_expected=True, text="***")
    .add_pattern(TextPattern, is_expected=True, text="*")
    .add_input_and_output(
        "case-1",
        content_text="n:*\n**\n***",
        matched_tokens=[
            (0, 2, 3),
            (1, 4, 6),
            (2, 7, 10),
        ],
        nonmatched_tokens=[
            3,
        ],
    )
    .add_input_and_output(
        "case-2",
        content_text="n:*\n**\n***\n****",
        matched_tokens=[
            (0, 2, 3),
            (1, 4, 6),
            (2, 7, 10),
            (3, 11, 12),
        ],
        nonmatched_tokens=[],
    )
    .end_test()
    .begin_test("test-4")
    .set_options(
        float_tolerance=0.0001,
    )
    .add_pattern(TextPattern, is_expected=True, text="*")
    .add_pattern(SpaceOrEOLPattern, is_expected=True)
    .add_pattern(TextPattern, is_expected=True, text="**")
    .add_pattern(SpaceOrEOLPattern, is_expected=True)
    .add_pattern(TextPattern, is_expected=True, text="***")
    .add_pattern(SpaceOrEOLPattern, is_expected=True)
    .add_input_and_output(
        "case-1",
        content_text="n:*\n**\n***",
        matched_tokens=[
            (0, 2, 3),
            (1, 3, 4),
            (2, 4, 6),
            (3, 6, 7),
            (4, 7, 10),
            (5, 10, 10),
        ],
        nonmatched_tokens=[],
    )
    .add_input_and_output(
        "case-2",
        content_text="n:*\n**\n***\n",
        matched_tokens=[
            (0, 2, 3),
            (1, 3, 4),
            (2, 4, 6),
            (3, 6, 7),
            (4, 7, 10),
            (5, 10, 11),
        ],
        nonmatched_tokens=[],
    )
    .end_test()
    .begin_test("test-5")
    .set_options(
        float_tolerance=0.0001,
    )
    .add_pattern(TextPattern, is_expected=True, text="*")
    .add_pattern(SpaceOrEOLPattern, is_expected=True)
    .add_pattern(TextPattern, is_expected=True, text="**")
    .add_pattern(SpaceOrEOLPattern, is_expected=True)
    .add_pattern(TextPattern, is_expected=True, text="***")
    .add_pattern(SpaceOrEOLPattern, is_expected=True)
    .add_pattern(TextPattern, is_expected=False, text="*")
    .add_input_and_output(
        "case-1",
        content_text="n:*\n**\n***",
        matched_tokens=[
            (0, 2, 3),
            (1, 3, 4),
            (2, 4, 6),
            (3, 6, 7),
            (4, 7, 10),
            (5, 10, 10),
        ],
        nonmatched_tokens=[
            6,
        ],
    )
    .add_input_and_output(
        "case-2",
        content_text="n:*\n**\n***\n",
        matched_tokens=[
            (0, 2, 3),
            (1, 3, 4),
            (2, 4, 6),
            (3, 6, 7),
            (4, 7, 10),
            (5, 10, 11),
        ],
        nonmatched_tokens=[
            6,
        ],
    )
    .add_input_and_output(
        "case-2",
        content_text="n:*\n**\n***\n****",
        matched_tokens=[
            (0, 2, 3),
            (1, 3, 4),
            (2, 4, 6),
            (3, 6, 7),
            (4, 7, 10),
            (5, 10, 11),
            (6, 11, 12),
        ],
        nonmatched_tokens=[],
    )
    .end_test()
    .build()
)


@pytest.mark.parametrize(
    [
        "test_config_options",
        "patterns",
        "content_text",
        "expected_match_result",
    ],
    [
        pytest.param(
            testcase["test_config_options"],
            testcase["patterns"],
            input_and_output["content_text"],
            input_and_output["expected_match_result"],
            id=f"{test_name}::{case_name}",
        )
        for test_name, testcase in _TESTCASES.items()
        for case_name, input_and_output in testcase["input_and_outputs"].items()
    ]

)
def test_match_service(
        test_config_options: TestConfigOptions,
        patterns: PatternList,
        content_text: str,
        expected_match_result: MatchServiceResult,
):
    match_get_best_service = get_match_get_best_service()
    match_result = match_get_best_service.execute(
        patterns=patterns,
        test_config_options=test_config_options,
        content_string=content_text,
    )
    assert match_result.matched_tokens == expected_match_result.matched_tokens
    assert match_result.nonmatched_tokens == expected_match_result.nonmatched_tokens
