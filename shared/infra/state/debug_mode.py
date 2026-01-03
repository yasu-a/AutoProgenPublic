from shared.domain.interface.state import IDebugModeState


class DebugModeState(IDebugModeState):
    def __init__(self):
        self._is_debug_mode: bool = False

    def get(self) -> bool:
        return self._is_debug_mode

    def update(self, is_debug_mode: bool) -> None:
        self._is_debug_mode = is_debug_mode
