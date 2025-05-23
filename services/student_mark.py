from datetime import datetime

from domain.models.student_mark import StudentMark
from domain.models.values import StudentID
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.path_providers.current_project import StudentMarkPathProvider
from infra.repositories.student_mark import StudentMarkRepository
from services.student import StudentListSubService


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
    def __init__(
            self,
            *,
            student_mark_repo: StudentMarkRepository,
    ):
        self._student_mark_repo = student_mark_repo

    def execute(self, student_mark: StudentMark) -> None:
        self._student_mark_repo.put(student_mark)


class StudentMarkCheckTimestampQueryService:
    # 生徒の採点データの最終更新日時を取得する

    def __init__(
            self,
            *,
            student_mark_path_provider: StudentMarkPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_mark_path_provider = student_mark_path_provider
        self._current_project_core_io = current_project_core_io

    def execute(self, student_id: StudentID) -> datetime | None:  # None if no file exists
        json_fullpath \
            = self._student_mark_path_provider.student_mark_data_json_fullpath(student_id)
        if not json_fullpath.exists():
            return None

        return self._current_project_core_io.get_file_mtime(
            file_fullpath=json_fullpath,
        )


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
