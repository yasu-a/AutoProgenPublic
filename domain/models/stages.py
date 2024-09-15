import functools
from enum import IntEnum


class StudentProgressStage(IntEnum):
    BUILD = 1
    COMPILE = 2
    EXECUTE = 3
    TEST = 4

    def get_next_stage(self) -> "StudentProgressStage | None":
        try:
            return StudentProgressStage(self.value + 1)
        except ValueError:
            return None

    @classmethod
    @functools.cache
    def list_stages(cls) -> tuple["StudentProgressStage", ...]:
        return tuple(sorted(cls, key=lambda x: x.value))

    @classmethod
    def get_first_stage(cls) -> "StudentProgressStage":
        return cls.list_stages()[0]

    @classmethod
    def get_last_stage(cls):
        return cls.list_stages()[-1]

    # def __contains__(self, other) -> bool:
    #     if not isinstance(other, StudentProgressStage):
    #         return NotImplemented
    #     if self.value < other.value:
    #         return False
    #     return True
