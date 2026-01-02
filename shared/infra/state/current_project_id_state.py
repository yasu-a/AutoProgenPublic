import warnings

from shared.domain.interface.state import ICurrentProjectIDState
from shared.domain.value.identifier import ProjectID
from util.app_logging import create_logger

_logger = create_logger()


class CurrentProjectIDState(ICurrentProjectIDState):
    """
    現在開かれているプロジェクトIDを管理する
    """

    def __init__(self):
        self._project_id: ProjectID | None = None

    def get(self) -> ProjectID | None:
        return self._project_id

    def update(self, project_id: ProjectID) -> None:
        if self._project_id is not None:
            warnings.warn(
                f"Current ProjectID is already set. (old: {self._project_id!s}, new: {project_id!s})")
        _logger.info(f"Current ProjectID is updated. (new: {project_id!s})")
        self._project_id = project_id

    def clear(self) -> None:
        self._project_id = None
        _logger.info("Current ProjectID is cleared.")
