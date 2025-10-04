from enum import IntEnum, auto


class ProjectConfigState(IntEnum):
    NORMAL = auto()  # 正常
    META_BROKEN = auto()  # 読み取れない
    INCOMPATIBLE_APP_VERSION = auto()  # バージョンが正しくない
    UNOPENABLE = auto()  # 開けない
