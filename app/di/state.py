from functools import cache

from shared.domain.interface.state import ICurrentProjectIDState
from shared.infra.state.current_project_id_state import CurrentProjectIDState


@cache  # アプリケーション全体で共有するState
def get_current_project_id_state() -> ICurrentProjectIDState:
    return CurrentProjectIDState()
