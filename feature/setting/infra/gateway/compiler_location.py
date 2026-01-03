import os
from pathlib import Path
from typing import Iterable, Sequence

from feature.setting.domain.interface.gateway import IFindCompilerPathGateway


class VSFindCompilerPathGateway(IFindCompilerPathGateway):
    """Visual Studioのコンパイラパスを検索するGateway"""

    def __init__(self, *, start_locations: Sequence[Path]):
        """
        Args:
            start_locations: 検索開始パスのリスト
        """
        self._start_locations = start_locations
        self._it: Iterable[Path] | None = None
        self._current_dir_path: Path | None = None
        self._is_reset = False  # reset()が呼ばれたかどうか
        self._is_finished = False  # 検索が終了したかどうか

    @staticmethod
    def _is_compiler_location(path: Path) -> bool:
        return path.is_file() and path.name == "VsDevCmd.bat"

    @staticmethod
    def _walk_file_in_location(location: Path) -> Iterable[Path]:
        for root, _, filenames in os.walk(str(location)):
            for filename in filenames:
                yield Path(root) / filename

    def _walk_file_in_multiple_location(self, locations: Sequence[Path]) -> Iterable[Path]:
        for start_location in locations:
            yield from self._walk_file_in_location(start_location)

    def reset(self) -> None:
        """検索をリセットして最初から検索できるようにする"""
        self._it = self._walk_file_in_multiple_location(self._start_locations)
        self._current_dir_path = None
        self._is_reset = True
        self._is_finished = False

    _SEARCH_MAX_FILES_PER_CALL = 100

    def search_next(self) -> list[Path]:
        """
        次の100個くらいのファイルを調べて、見つかったらそのリストを返す
        見つからなかったら空のリストを返す
        """
        if not self._is_reset:
            raise RuntimeError("reset() must be called before search_next()")

        if self._is_finished:
            return []

        found_locations: list[Path] = []
        
        for _ in range(self._SEARCH_MAX_FILES_PER_CALL):
            try:
                path = next(self._it)
                if self._is_compiler_location(path):
                    found_locations.append(path)
                self._current_dir_path = path.parent
            except StopIteration:
                self._is_finished = True
                break
            
        return found_locations

    def has_next(self) -> bool:
        """まだ検索すべきファイルがあるかどうか"""
        if not self._is_reset:
            raise RuntimeError("reset() must be called before has_next()")
        return not self._is_finished

    def get_current_dir(self) -> Path | None:
        """現在調べているディレクトリを取得（進捗コールバック用）"""
        return self._current_dir_path

