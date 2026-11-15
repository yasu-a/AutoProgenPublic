from contextlib import contextmanager
from collections.abc import Generator

from PyQt5.QtCore import QMutex

from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.infra.io.files.current_project import CurrentProjectCoreIO
from autoprogen.infra.path_layout import ProjectPathLayout


class ProjectSettingsRepository:
    """現在のプロジェクトに属する設定を読み書きする。"""

    def __init__(
            self,
            *,
            project_path_layout: ProjectPathLayout,
            current_project_core_io: CurrentProjectCoreIO,
    ) -> None:
        """プロジェクト固有のパス構成とファイル操作を受け取る。"""
        self._project_path_layout = project_path_layout
        self._current_project_core_io = current_project_core_io
        self._model: ProjectSettings | None = None
        self._mutex = QMutex()

    @contextmanager
    def _lock(self) -> Generator[None, None, None]:
        """同じRepositoryに対する設定の読み書きを直列化する。"""
        self._mutex.lock()
        try:
            yield
        finally:
            self._mutex.unlock()

    def _get_model_unlocked(self) -> ProjectSettings:
        """必要な場合だけプロジェクト設定をファイルから読み込む。"""
        if self._model is None:
            json_fullpath = self._project_path_layout.settings_json
            if json_fullpath.exists():
                self._model = ProjectSettings.from_json(
                    self._current_project_core_io.read_json(
                        json_fullpath=json_fullpath,
                    )
                )
            else:
                self._model = ProjectSettings.create_default()
        return self._model

    def get(self) -> ProjectSettings:
        """現在のプロジェクト設定を返す。"""
        with self._lock():
            return self._get_model_unlocked()

    def put(self, model: ProjectSettings) -> None:
        """現在のプロジェクト設定をキャッシュとJSONへ保存する。"""
        if not isinstance(model, ProjectSettings):
            raise TypeError("modelにはProjectSettingsを指定してください")
        with self._lock():
            self._current_project_core_io.write_json(
                json_fullpath=self._project_path_layout.settings_json,
                body=model.to_json(),
            )
            self._model = model
