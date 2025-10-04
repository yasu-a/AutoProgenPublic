from domain.model.value import ProjectID

_project_id: ProjectID | None = None


def set_current_project_id(project_id: ProjectID):
    global _project_id
    assert _project_id is None, _project_id
    _project_id = project_id


def get_current_project_id() -> ProjectID:
    return _project_id
