from feature.scoring.usecase.interface import IStudentMarkGetUseCase, IStudentMarkPutUseCase, \
    IStudentMarkListUseCase
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.service.student_mark_get import StudentMarkEntityGetSubService
from shared.domain.service.student_mark_list import StudentMarkEntityListService
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student_mark import StudentMarkEntityRepository


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
            student_mark_repo: StudentMarkEntityRepository,
    ):
        self._student_mark_repo = student_mark_repo

    def execute(self, student_mark: StudentMarkEntity) -> None:
        self._student_mark_repo.put(student_mark)


class StudentMarkListUseCase(IStudentMarkListUseCase):
    def __init__(
            self,
            *,
            student_mark_list_service: StudentMarkEntityListService,
    ):
        self._student_mark_list_service = student_mark_list_service

    def execute(self) -> list[StudentMarkEntity]:
        return self._student_mark_list_service.execute()
