from unittest.mock import Mock

import pytest

from autoprogen.application.container.project import ProjectContainer
from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.domain.model.stage import BuildStage
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import ProjectID, StudentID
from autoprogen.service.student_mark import StudentMarkGetSubService, StudentMarkPutService
from autoprogen.service.student_stage_path_result import (
    StudentPutStageResultService,
    StudentStagePathResultPutService,
    StudentStageResultClearService,
)
from autoprogen.usecase.student_run_next_stage import StudentRunNextStageUseCase


@pytest.fixture
def student_id() -> StudentID:
    """通知テストで使う学生IDを返す。"""
    return StudentID("21D5109047B")


def test_stage_result_notifies_only_after_successful_save(student_id: StudentID) -> None:
    """ステージ結果の保存成功後にのみ通知する。"""
    bus = StudentChangeEventBus()
    events: list[StudentID] = []
    bus.subscribe(student_id, events.append)
    repository = Mock()
    result = Mock(student_id=student_id)
    service = StudentStagePathResultPutService(
        student_stage_path_result_repo=repository,
        student_change_event_bus=bus,
    )

    service.execute(result)
    repository.put.assert_called_once_with(result)
    assert events == [student_id]

    repository.put.side_effect = RuntimeError("save failed")
    with pytest.raises(RuntimeError, match="save failed"):
        service.execute(result)
    assert events == [student_id]


def test_stage_run_uses_common_save_service(student_id: StudentID) -> None:
    """通常のステージ結果が共通の保存サービスを通る。"""
    repository = Mock()
    result = Mock(student_id=student_id)
    stage_path_result = repository.get.return_value
    put_service = Mock()
    service = StudentPutStageResultService(
        student_stage_path_result_repo=repository,
        student_stage_path_result_put_service=put_service,
    )

    service.execute(StagePath([BuildStage()]), result)

    stage_path_result.put_result.assert_called_once_with(result)
    put_service.execute.assert_called_once_with(stage_path_result)
    repository.put.assert_not_called()


def test_clear_uses_common_save_service_for_each_path(student_id: StudentID) -> None:
    """一括クリアは各パスの保存を共通サービスへ委ねる。"""
    paths = [StagePath([BuildStage()]), StagePath([BuildStage()])]
    repository = Mock()
    results = [Mock(student_id=student_id), Mock(student_id=student_id)]
    repository.get.side_effect = results
    path_list_service = Mock()
    path_list_service.execute.return_value = paths
    put_service = Mock()
    service = StudentStageResultClearService(
        stage_path_list_sub_service=path_list_service,
        student_stage_path_result_repo=repository,
        student_stage_path_result_put_service=put_service,
    )

    service.execute(student_id=student_id)

    for result in results:
        result.delete_all_results.assert_called_once_with()
    assert [call.args[0] for call in put_service.execute.call_args_list] == results
    repository.put.assert_not_called()


def test_rollback_uses_common_save_service(student_id: StudentID) -> None:
    """ロールバック時にもリポジトリを直接保存しない。"""
    repository = Mock()
    put_service = Mock()
    rollback_check = Mock()
    rollback_check.execute.return_value = BuildStage
    path = StagePath([BuildStage()])
    result = repository.get.return_value
    usecase = StudentRunNextStageUseCase(
        stage_path_list_sub_service=Mock(),
        student_stage_path_result_get_service=Mock(),
        student_stage_path_result_repo=repository,
        student_stage_path_result_put_service=put_service,
        student_run_build_stage_usecase=Mock(),
        student_run_compile_stage_usecase=Mock(),
        student_run_execute_stage_usecase=Mock(),
        student_run_test_stage_usecase=Mock(),
        student_stage_path_result_check_rollback_service=rollback_check,
    )

    assert usecase._StudentRunNextStageUseCase__rollback(
        student_id=student_id,
        stage_path_result=Mock(),
        stage_paths=[path],
    )

    put_service.execute.assert_called_once_with(result)
    repository.put.assert_not_called()


def test_mark_save_notifies_but_lazy_creation_does_not(student_id: StudentID) -> None:
    """実際の採点保存のみ通知し、取得時の空レコード作成は通知しない。"""
    bus = StudentChangeEventBus()
    events: list[StudentID] = []
    bus.subscribe(student_id, events.append)
    repository = Mock()
    repository.exists.return_value = False
    get_service = StudentMarkGetSubService(student_mark_repo=repository)
    put_service = StudentMarkPutService(
        student_mark_repo=repository,
        student_change_event_bus=bus,
    )
    mark = StudentMark(student_id=student_id, score=50)

    get_service.execute(student_id)
    assert events == []
    put_service.execute(mark)
    assert events == [student_id]

    repository.put.side_effect = RuntimeError("save failed")
    with pytest.raises(RuntimeError, match="save failed"):
        put_service.execute(mark)
    assert events == [student_id]


def test_project_containers_have_independent_event_buses(student_id: StudentID) -> None:
    """各プロジェクトの通知が別プロジェクトへ漏れない。"""

    def create_container(project_id: str) -> ProjectContainer:
        """通知の所有範囲を確認するためのコンテナを作る。"""
        return ProjectContainer(
            project_id=ProjectID(project_id),
            match_get_best_service=Mock(),
            project_repository=Mock(),
            global_settings_repository=Mock(),
            test_source_repository=Mock(),
            project_path_layout=Mock(),
            project_core_io=Mock(),
            readonly_excel_worksheet_gateway=Mock(),
        )

    first = create_container("first")
    second = create_container("second")
    received: list[StudentID] = []
    first.student_change_event_bus.subscribe(student_id, received.append)

    assert first.student_change_event_bus is first.student_change_event_bus
    assert first.student_change_event_bus is not second.student_change_event_bus
    second.student_change_event_bus.notify(student_id)
    assert received == []
    first.student_change_event_bus.notify(student_id)
    assert received == [student_id]


def test_partial_clear_notifies_for_already_saved_result(student_id: StudentID) -> None:
    """一括クリアの途中で失敗しても保存済みの変更は通知済みとなる。"""
    bus = StudentChangeEventBus()
    received: list[StudentID] = []
    bus.subscribe(student_id, received.append)
    repository = Mock()
    repository.get.side_effect = [Mock(student_id=student_id), Mock(student_id=student_id)]
    repository.put.side_effect = [None, RuntimeError("second save failed")]
    paths = [StagePath([BuildStage()]), StagePath([BuildStage()])]
    path_list_service = Mock()
    path_list_service.execute.return_value = paths
    put_service = StudentStagePathResultPutService(
        student_stage_path_result_repo=repository,
        student_change_event_bus=bus,
    )
    clear_service = StudentStageResultClearService(
        stage_path_list_sub_service=path_list_service,
        student_stage_path_result_repo=repository,
        student_stage_path_result_put_service=put_service,
    )

    with pytest.raises(RuntimeError, match="second save failed"):
        clear_service.execute(student_id=student_id)

    assert received == [student_id]
