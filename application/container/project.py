from functools import cached_property
from typing import TYPE_CHECKING

from application.dependency.usecase import create_current_project_summary_get_usecase
from domain.model.value import ProjectID

if TYPE_CHECKING:
    from application.container.app import AppContainer


class ProjectContainer:
    def __init__(self, *, app_container: "AppContainer", project_id: ProjectID) -> None:
        self._app = app_container
        self._project_id = project_id

    @property
    def project_id(self) -> ProjectID:
        return self._project_id

    @cached_property
    def current_project_summary_get_usecase(self):
        return create_current_project_summary_get_usecase(self._project_id)
