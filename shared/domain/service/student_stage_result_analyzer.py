from collections import OrderedDict

from shared.domain.interface.service import IStudentStagePathResultAnalyzerService
from shared.domain.model.stage import StageElement
from shared.domain.model.student_result import AbstractStageResultEntity, CompileStageResultEntity, \
    TestStageResultEntity


class StudentStageResultAnalyzerService(IStudentStagePathResultAnalyzerService):
    """学生のステージ結果マップを分析し、次のステージや失敗理由などを判定するサービス。"""

    def get_next_stage(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> StageElement | None:
        if not stage_path:
            return None

        last_executed_element = None
        last_executed_result = None

        # Find the last executed stage
        for element in stage_path:
            result = results_map.get(element)
            if result is None:
                break
            last_executed_element = element
            last_executed_result = result

        if last_executed_element is None:
            # Nothing executed yet, return first stage
            return stage_path[0]

        if not last_executed_result.is_success:
            # Last stage failed, retry it
            return last_executed_element

        # Last stage succeeded, find next
        try:
            current_index = stage_path.index(last_executed_element)
            if current_index + 1 < len(stage_path):
                return stage_path[current_index + 1]
            else:
                return None  # All finished
        except ValueError:
            return None  # Should not happen

    def is_all_finished(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> bool:
        return self.get_next_stage(stage_path, results_map) is None

    def get_last_failure_detailed_reason(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> str | None:
        last_executed_result = self._get_last_executed_result(stage_path, results_map)
        if last_executed_result is None:
            return None

        if last_executed_result.is_success:
            return None

        # ステージごとに詳細情報を取得
        if isinstance(last_executed_result, CompileStageResultEntity):
            return last_executed_result.output or last_executed_result.error_summary
        elif isinstance(last_executed_result, TestStageResultEntity):
            return last_executed_result.failure_reason or last_executed_result.error_summary
        else:
            return last_executed_result.error_summary

    def get_last_failure_main_reason(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> str | None:
        last_executed_result = self._get_last_executed_result(stage_path, results_map)
        if last_executed_result is None:
            return None

        if last_executed_result.is_success:
            return None

        return last_executed_result.error_summary

    def get_stage_statuses(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> OrderedDict[StageElement, str]:
        result_states = OrderedDict()
        for element in stage_path:
            result = results_map.get(element)
            if result is None:
                result_states[element] = "unfinished"
            else:
                if result.is_success:
                    result_states[element] = "success"
                else:
                    result_states[element] = "failure"
        return result_states

    def is_last_stage_success(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> bool | None:
        last_executed_result = self._get_last_executed_result(stage_path, results_map)
        if last_executed_result is None:
            return None
        return last_executed_result.is_success

    def _get_last_executed_result(
            self,
            stage_path: list[StageElement],
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None]
    ) -> AbstractStageResultEntity | None:
        last_executed_result = None
        for element in stage_path:
            result = results_map.get(element)
            if result is None:
                break
            last_executed_result = result
        return last_executed_result
