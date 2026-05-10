from functools import cached_property

from application.dependency.usecase import create_app_version_check_is_stable_usecase, \
    create_resource_usage_get_usecase
from application.container.project import ProjectContainer
from domain.model.value import ProjectID


class AppContainer:
    def create_project_container(self, project_id: ProjectID) -> "ProjectContainer":
        return ProjectContainer(
            project_id=project_id,
        )

    @cached_property
    def app_version_check_is_stable_usecase(self):
        return create_app_version_check_is_stable_usecase()

    @cached_property
    def resource_usage_get_usecase(self):
        return create_resource_usage_get_usecase()
