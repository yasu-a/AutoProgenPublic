from domain.models.values import ProjectName

_project_name: ProjectName | None = None


def set_current_project_name(project_name: ProjectName):
    global _project_name
    assert _project_name is None, _project_name
    _project_name = project_name


def get_current_project_name() -> ProjectName:
    return _project_name
