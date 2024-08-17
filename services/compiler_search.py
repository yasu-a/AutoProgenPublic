import collections
from pathlib import Path
from typing import Iterable


class CompilerLocationSequentialSearchService:
    def __init__(self):
        self._stack: collections.deque[Path] = collections.deque()
        self._results: list[Path] = []

    @classmethod
    def is_compiler_location(cls, path: Path) -> bool:
        return path.is_file() and path.name == "VsDevCmd.bat"

    @classmethod
    def _iter_start_locations(cls) -> Iterable[Path]:
        yield Path(r"C:\Program Files\Microsoft Visual Studio")

    def reset_search(self) -> None:
        self._stack.clear()
        self._results.clear()
        for path_start in self._iter_start_locations():
            assert path_start.is_dir(), path_start
            self._stack.append(path_start)

    def search_next(self) -> bool:  # return False if search ends
        if self._stack:
            path_dir = self._stack.pop()
            for path_child in path_dir.iterdir():
                if path_child.is_dir():
                    self._stack.append(path_child)
                elif path_child.is_file():
                    if self.is_compiler_location(path_child):
                        self._results.append(path_child)
        return len(self._stack) > 0

    def get_current_search_location(self) -> Path:
        # プログレス表示用
        if self._stack:
            return self._stack[-1]
        else:
            return Path()

    def get_paths_found(self) -> list[Path]:
        return self._results.copy()
