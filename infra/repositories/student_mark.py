from domain.models.student_mark import StudentMark
from domain.models.values import StudentID
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.path_providers.current_project import StudentMarkPathProvider


class StudentMarkRepository:
    def __init__(
            self,
            *,
            student_mark_path_provider: StudentMarkPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_mark_path_provider = student_mark_path_provider
        self._current_project_core_io = current_project_core_io

    def create(self, student_id: StudentID) -> StudentMark:
        mark = StudentMark(
            student_id=student_id,
            score=None,
        )
        self.put(mark=mark)
        return mark

    def put(self, mark: StudentMark) -> StudentMark:
        json_fullpath = self._student_mark_path_provider.student_mark_data_json_fullpath(
            student_id=mark.student_id,
        )
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        self._current_project_core_io.write_json(
            json_fullpath=json_fullpath,
            body=mark.to_json(),
        )
        return mark

    def exists(self, student_id: StudentID):
        json_fullpath = self._student_mark_path_provider.student_mark_data_json_fullpath(
            student_id=student_id,
        )
        return json_fullpath.exists()

    def get(self, student_id: StudentID) -> StudentMark:
        json_fullpath = self._student_mark_path_provider.student_mark_data_json_fullpath(
            student_id=student_id,
        )
        if not json_fullpath.exists():
            raise ValueError(f"Mark data for student {student_id} not found")

        body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
        return StudentMark.from_json(body=body)
