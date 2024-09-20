from pathlib import Path

from domain.models.file_item import SourceFileItem, ExecutableFileItem, StudentDynamicFileItemType
from domain.models.values import StudentID
from files.core.project import ProjectCoreIO
from files.path_providers.project_dynamic import StudentDynamicPathProvider
from transaction import transactional_with


class StudentDynamicRepository:
    def __init__(
            self,
            *,
            student_dynamic_path_provider: StudentDynamicPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._student_dynamic_path_provider = student_dynamic_path_provider
        self._project_core_io = project_core_io

    def __get_file_item_fullpath(
            self,
            *,
            student_id: StudentID,
            file_item_type: type[StudentDynamicFileItemType],
    ) -> Path:
        if file_item_type is SourceFileItem:
            filename = "main.c"
        elif file_item_type is ExecutableFileItem:
            filename = "main.exe"
        else:
            assert False, file_item_type
        base_folder_fullpath = self._student_dynamic_path_provider.base_folder_fullpath(student_id)
        return base_folder_fullpath / filename

    @transactional_with("student_id")
    def put(self, student_id: StudentID, file_item: StudentDynamicFileItemType) -> None:
        file_fullpath = self.__get_file_item_fullpath(
            student_id=student_id,
            file_item_type=type(file_item),
        )
        file_fullpath.mkdir(parents=True, exist_ok=True)
        self._project_core_io.write_file_content_bytes(
            file_fullpath=file_fullpath,
            content_bytes=file_item.content_bytes,
        )

    @transactional_with("student_id")
    def get(self, student_id: StudentID, file_item_type: type[StudentDynamicFileItemType]) \
            -> StudentDynamicFileItemType:
        file_fullpath = self.__get_file_item_fullpath(
            student_id=student_id,
            file_item_type=file_item_type,
        )
        if not file_fullpath.exists():
            raise FileNotFoundError()
        content_bytes = self._project_core_io.read_file_content_bytes(
            file_fullpath=file_fullpath,
        )
        if file_item_type is SourceFileItem:
            return SourceFileItem(
                content_text=content_bytes.decode("utf-8"),
            )
        elif file_item_type is ExecutableFileItem:
            return ExecutableFileItem(
                content_bytes=content_bytes,
            )
        else:
            assert False, file_item_type

    @transactional_with("student_id")
    def list(self, student_id: StudentID) -> list[StudentDynamicFileItemType]:
        lst = []
        for file_item_type in (
                SourceFileItem,
                ExecutableFileItem,
        ):
            try:
                file_item = self.get(student_id, file_item_type)
            except FileNotFoundError:
                pass
            else:
                lst.append(file_item)
        return lst

    @transactional_with("student_id")
    def delete(
            self,
            student_id: StudentID,
            file_item_type: type[StudentDynamicFileItemType],
    ) -> None:
        file_fullpath = self.__get_file_item_fullpath(
            student_id=student_id,
            file_item_type=file_item_type,
        )
        if not file_fullpath.exists():
            raise FileNotFoundError()
        self._project_core_io.unlink(file_fullpath)
