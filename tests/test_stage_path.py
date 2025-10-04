from pytest_mock import MockerFixture

from application.dependency.service import get_stage_path_list_sub_service
from domain.model.stage_path import StagePath
from domain.model.stage import BuildStage, CompileStage, ExecuteStage, TestStage
from domain.model.value import TestCaseID


def test_stage_path_no_testcase_ids(mocker: MockerFixture):
    mocker.patch(
        "service.testcase_config.TestCaseConfigListIDSubService.execute",
        return_value=[],
    )
    stage_path_lst: list[StagePath] = get_stage_path_list_sub_service().execute()
    assert stage_path_lst == [
        StagePath([
            BuildStage(),
            CompileStage(),
        ])
    ]


def test_stage_path_with_testcase_ids(mocker: MockerFixture):
    mocker.patch(
        "service.testcase_config.TestCaseConfigListIDSubService.execute",
        return_value=[TestCaseID("testcase-1"), TestCaseID("testcase-2")],
    )
    stage_path_lst: list[StagePath] = get_stage_path_list_sub_service().execute()
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
