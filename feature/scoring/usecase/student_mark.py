from feature.scoring.usecase.interface import IStudentMarkGetUseCase, IStudentMarkPutUseCase, \
    IStudentScoreListUseCase
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.interface.event import IEventBus
from shared.domain.service.student_mark_get import StudentMarkEntityGetSubService
from shared.domain.service.student_mark_list import StudentMarkEntityListService
from shared.domain.value.event import StudentResultUpdateEvent
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student_mark import StudentScoreRepository


class StudentMarkGetUseCase(IStudentMarkGetUseCase):
    def __init__(
            self,
            *,
            student_mark_get_sub_service: StudentMarkEntityGetSubService,
    ):
        self._student_mark_get_sub_service = student_mark_get_sub_service

    def execute(self, student_id: StudentID) -> StudentMarkEntity:
        return self._student_mark_get_sub_service.execute(student_id)


class StudentMarkPutUseCase(IStudentMarkPutUseCase):
    def __init__(
            self,
            *,
            student_mark_repo: StudentScoreRepository,
            event_bus: IEventBus,
    ):
        self._student_mark_repo = student_mark_repo
        self._event_bus = event_bus

    def execute(self, student_mark: StudentMarkEntity) -> None:
        self._student_mark_repo.put(student_mark)
        self._event_bus.publish(StudentResultUpdateEvent(student_mark.student_id))


class StudentScoreListUseCase(IStudentScoreListUseCase):
    def __init__(
            self,
            *,
            student_mark_list_service: StudentMarkEntityListService,
    ):
        self._student_mark_list_service = student_mark_list_service

    def execute(self) -> list[StudentMarkEntity]:
        return self._student_mark_list_service.execute()
