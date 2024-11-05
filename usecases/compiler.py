import collections
from pathlib import Path
from typing import Iterable, Callable

from infra.external.compiler_location import is_compiler_location


class CompilerSearchUseCase:
    def __init__(
            self,
    ):
        pass

    @classmethod
    def __iter_start_locations(cls) -> Iterable[Path]:
        yield Path(r"C:\Program Files\Microsoft Visual Studio")

    def execute(
            self,
            progress_callback: Callable[[Path], None],  # 探索中のパスが更新されたらそのパスを通知する
            stop_producer: Callable[[], bool],  # 停止するときTrueを受け取る
    ) -> list[Path]:
        stack: collections.deque[Path] = collections.deque()
        results: list[Path] = []

        stack.clear()
        results.clear()
        for path_start in self.__iter_start_locations():
            assert path_start.is_dir(), path_start
            stack.append(path_start)

        while True:
            if stop_producer():
                break

            if not stack:
                break

            path_dir = stack.pop()
            progress_callback(path_dir)
            for path_child in path_dir.iterdir():
                if path_child.is_dir():
                    stack.append(path_child)
                elif path_child.is_file():
                    if is_compiler_location(path_child):
                        results.append(path_child)

        return results
