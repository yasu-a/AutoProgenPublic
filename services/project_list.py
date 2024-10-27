from app_logging import create_logger
from domain.models.project import Project
from infra.repositories.project import ProjectRepository


class ProjectListService:
    _logger = create_logger()

    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self) -> list[Project]:
        return self._project_repo.list()
