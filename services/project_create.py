from datetime import datetime

from domain.models.project import Project
from domain.models.values import TargetID, ProjectID
from files.repositories.project import ProjectRepository


class ProjectCreateService:
    # プロジェクトIDと設問IDから新規にプロジェクトを生成する

    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self, project_id: ProjectID, target_id: TargetID):
        project = Project(
            project_id=project_id,
            target_id=target_id,
            created_at=datetime.now(),
            open_at=datetime.now(),
        )
        self._project_repo.put(project)
