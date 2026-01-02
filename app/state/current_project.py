from app.di.repository import get_current_project_id_state
from shared.domain.value.identifier import ProjectID

# TODO: 廃止！

def set_current_project_id(project_id: ProjectID):
    """Deprecated: Use get_current_project_id_state().update() instead"""
    state = get_current_project_id_state()
    assert state.get() is None, state.get()
    state.update(project_id)


def get_current_project_id() -> ProjectID | None:
    """Deprecated: Use get_current_project_id_state().get() instead"""
    return get_current_project_id_state().get()
