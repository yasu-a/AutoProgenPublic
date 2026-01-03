from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from shared.domain.value.setting import Setting


# DTOはinterfaceの直上に定義
@dataclass(frozen=True)
class TestCompileStageResultDto:
    """テストコンパイルステージ実行UseCaseの結果を表すDTO"""
    is_success: bool
    output: str


class ISettingGetUseCase(ABC):
    @abstractmethod
    def execute(self) -> Setting:
        raise NotImplementedError()


class ISettingPutUseCase(ABC):
    @abstractmethod
    def execute(self, setting: Setting) -> None:
        raise NotImplementedError()


class ICompilerSearchUseCase(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            progress_callback: Callable[[Path], None] | None = None,
            stop_producer: Callable[[], bool] | None = None,
    ) -> list[Path]:
        raise NotImplementedError()


class ITestCompileStageUseCase(ABC):
    @abstractmethod
    def execute(self, compiler_tool_fullpath: Path) -> "TestCompileStageResultDto":
        raise NotImplementedError()
