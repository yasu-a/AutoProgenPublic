from pathlib import Path
from typing import Callable

from feature.setting.domain.interface.gateway import IFindCompilerPathGateway
from feature.setting.usecase.interface import ICompilerSearchUseCase


class CompilerSearchUseCase(ICompilerSearchUseCase):
    def __init__(
            self,
            *,
            find_compiler_path_gateway: IFindCompilerPathGateway,
    ):
        self._find_compiler_path_gateway = find_compiler_path_gateway

    def execute(
            self,
            *,
            progress_callback: Callable[[Path], None] | None = None,
            stop_producer: Callable[[], bool] | None = None,
    ) -> list[Path]:
        # 検索をリセット
        self._find_compiler_path_gateway.reset()

        results: list[Path] = []

        while self._find_compiler_path_gateway.has_next():
            if stop_producer and stop_producer():
                break

            found_paths = self._find_compiler_path_gateway.search_next()
            results.extend(found_paths)

            # 進捗コールバック: 現在調べているディレクトリを報告
            if progress_callback:
                current_dir = self._find_compiler_path_gateway.get_current_dir()
                if current_dir:
                    progress_callback(current_dir)

        return results
