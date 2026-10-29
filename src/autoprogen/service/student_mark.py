from datetime import datetime

from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.student_mark import StudentMarkRepository
from autoprogen.service.student import StudentListSubService


class StudentMarkGetSubService:
    def __init__(
            self,
            *,
            student_mark_repo: StudentMarkRepository,
    ):
        self._student_mark_repo = student_mark_repo

    def execute(self, student_id: StudentID) -> StudentMark:
        if not self._student_mark_repo.exists(student_id):
            return self._student_mark_repo.create(student_id)
        return self._student_mark_repo.get(student_id)


class StudentMarkPutService:
    """採点結果を保存し、対象学生の変更を通知する。"""

    def __init__(
            self,
            *,
            student_mark_repo: StudentMarkRepository,
            student_change_event_bus: StudentChangeEventBus,
    ):
        """保存先と通知先を受け取る。"""
        self._student_mark_repo = student_mark_repo
        self._student_change_event_bus = student_change_event_bus

    def execute(self, student_mark: StudentMark) -> None:
        """採点結果を保存し、成功した場合だけ変更を通知する。"""
        self._student_mark_repo.put(student_mark)
        self._student_change_event_bus.notify(student_mark.student_id)


class StudentMarkCheckTimestampQueryService:
    # 生徒の採点データの最終更新日時を取得する

    def __init__(
            self,
            *,
            student_mark_repo: StudentMarkRepository,
    ):
        self._student_mark_repo = student_mark_repo

    def execute(self, student_id: StudentID) -> datetime | None:  # None if no file exists
        return self._student_mark_repo.get_timestamp(student_id)


class StudentMarkListService:
    def __init__(
            self,
            *,
            student_list_sub_service: StudentListSubService,
            student_mark_get_sub_service: StudentMarkGetSubService,
    ):
        self._student_list_sub_service = student_list_sub_service
        self._student_mark_get_sub_service = student_mark_get_sub_service

    def execute(self) -> list[StudentMark]:
        student_marks = []
        for student in self._student_list_sub_service.execute():
            student_mark = self._student_mark_get_sub_service.execute(student.student_id)
            student_marks.append(student_mark)
        return student_marks
