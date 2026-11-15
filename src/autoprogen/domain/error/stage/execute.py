from typing import ClassVar

from autoprogen.domain.error.stage.base import StageError


class ExecuteStageError(StageError):
    """EXECUTEステージで発生するエラーの基底クラス。"""

    error_group_id: ClassVar[str] = "execute"


class ExecutableNotFoundError(ExecuteStageError):
    """実行対象のファイルが存在しない。"""

    error_type_id: ClassVar[str] = "executable_not_found"


class ExecutionTimeoutError(ExecuteStageError):
    """学生プログラムの実行が制限時間を超えた。"""

    error_type_id: ClassVar[str] = "timeout"
