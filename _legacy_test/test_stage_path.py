from datetime import datetime

from pytest_mock import MockerFixture

from app.di.service import get_stage_path_list_sub_service
from shared.domain.value.execute_config_options import ExecuteConfigOptions
from shared.domain.value.input_file import InputFileCollection
from shared.domain.entity.testcase_config import TestCaseConfigEntity
from shared.domain.value.execute_config import TestCaseExecuteConfig
from shared.domain.value.expected_output_file import ExpectedOutputFileCollection
from shared.domain.value.identifier import TestCaseID
from shared.domain.value.stage import BuildStage, CompileStage, ExecuteStage, TestStage
from shared.domain.value.stage_path import StagePath
from shared.domain.value.test_config import TestCaseTestConfig
from shared.domain.value.test_config_options import TestConfigOptions


def test_stage_path_no_testcase_ids(mocker: MockerFixture):
    mocker.patch(
        "infra.repository.testcase_config.TestCaseConfigRepository.list",
        return_value=[],
    )
    stage_path_lst: list[StagePath] \
        = get_stage_path_list_sub_service().execute()
    assert stage_path_lst == [
        StagePath([
            BuildStage(),
            CompileStage(),
        ])
    ]


def test_stage_path_with_testcase_ids(mocker: MockerFixture):
    test_datetime = datetime(2024, 1, 1, 0, 0, 0)
    testcase_configs = [
        TestCaseConfigEntity(
            testcase_id=TestCaseID("testcase-1"),
            execute_config=TestCaseExecuteConfig(
                input_file_collection=InputFileCollection(),
                options=ExecuteConfigOptions(timeout=5.0),
                mtime=test_datetime,
            ),
            test_config=TestCaseTestConfig(
                expected_output_file_collection=ExpectedOutputFileCollection(),
                options=TestConfigOptions(ignore_case=True),
                mtime=test_datetime,
            ),
        ),
        TestCaseConfigEntity(
            testcase_id=TestCaseID("testcase-2"),
            execute_config=TestCaseExecuteConfig(
                input_file_collection=InputFileCollection(),
                options=ExecuteConfigOptions(timeout=5.0),
                mtime=test_datetime,
            ),
            test_config=TestCaseTestConfig(
                expected_output_file_collection=ExpectedOutputFileCollection(),
                options=TestConfigOptions(ignore_case=True),
                mtime=test_datetime,
            ),
        ),
    ]
    mocker.patch(
        "infra.repository.testcase_config.TestCaseConfigRepository.list",
        return_value=testcase_configs,
    )
    stage_path_lst: list[StagePath] = get_stage_path_list_sub_service(
    ).execute()
    assert stage_path_lst == [
        StagePath([
            BuildStage(),
            CompileStage(),
            ExecuteStage(testcase_id=TestCaseID("testcase-1")),
            TestStage(testcase_id=TestCaseID("testcase-1")),
        ]),
        StagePath([
            BuildStage(),
            CompileStage(),
            ExecuteStage(testcase_id=TestCaseID("testcase-2")),
            TestStage(testcase_id=TestCaseID("testcase-2")),
        ])
    ]
