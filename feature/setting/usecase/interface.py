from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

from feature.setting.usecase.dto import TestCompileStageResult
from shared.domain.value.setting import Setting


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
    def execute(self, compiler_tool_fullpath: Path) -> "TestCompileStageResult":
        raise NotImplementedError()
