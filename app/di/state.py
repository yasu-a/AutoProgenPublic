from functools import cache

from shared.domain.interface.state import ICurrentProjectIDState, IDebugModeState
from shared.infra.state.current_project_id_state import CurrentProjectIDState
from shared.infra.state.debug_mode import DebugModeState


@cache  # アプリケーション全体で共有するState
def get_current_project_id_state() -> ICurrentProjectIDState:
    return CurrentProjectIDState()


@cache  # アプリケーション全体で共有するState
def get_debug_mode_state() -> IDebugModeState:
    return DebugModeState()
