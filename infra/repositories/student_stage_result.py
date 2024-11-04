from domain.models.student_stage_result import *
from domain.models.values import StudentID
from infra.core.current_project import CurrentProjectCoreIO
from infra.path_providers.current_project import StudentStageResultPathProvider


class StudentStageResultRepository:
    def __init__(
            self,
            *,
            student_stage_result_path_provider: StudentStageResultPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._student_stage_result_path_provider = student_stage_result_path_provider
        self._current_project_core_io = current_project_core_io

    @classmethod
    def __get_type_name_of_result_type(
            cls,
            result_type: type[AbstractStudentStageResult],
    ) -> str:
        return result_type.__name__

    RESULT_TYPES = (
        BuildSuccessStudentStageResult,
        BuildFailureStudentStageResult,
        CompileSuccessStudentStageResult,
        CompileFailureStudentStageResult,
        ExecuteSuccessStudentStageResult,
        ExecuteFailureStudentStageResult,
        TestSuccessStudentStageResult,
        TestFailureStudentStageResult,
    )

    @classmethod
    def __get_result_type_from_type_name(
            cls,
            result_type_name: str,
    ) -> type[AbstractStudentStageResult]:
        for sub_cls in cls.RESULT_TYPES:
            if result_type_name == cls.__get_type_name_of_result_type(sub_cls):
                return sub_cls
        assert False, result_type_name

    def put(
            self,
            result: AbstractStudentStageResult,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.result_json_fullpath(
                student_id=result.student_id,
                stage=result.stage,
            )
        )
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)

        self._current_project_core_io.write_json(
            json_fullpath=json_fullpath,
            body={
                "__type__": self.__get_type_name_of_result_type(type(result)),
                **result.to_json(),
            },
        )

    def exists(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> bool:
        json_fullpath = (
            self._student_stage_result_path_provider.result_json_fullpath(
                student_id=student_id,
                stage=stage,
            )
        )
        return json_fullpath.exists()

    def get(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> BuildStageResultType:
        json_fullpath = (
            self._student_stage_result_path_provider.result_json_fullpath(
                student_id=student_id,
                stage=stage,
            )
        )
        if not json_fullpath.exists():
            raise ValueError(f"Build result for student {student_id} not found")

        body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
        type_name = body.pop("__type__")
        result_type = self.__get_result_type_from_type_name(type_name)
        return result_type.from_json(body)

    def delete(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> None:
        json_fullpath = (
            self._student_stage_result_path_provider.result_json_fullpath(
                student_id=student_id,
                stage=stage,
            )
        )
        if not json_fullpath.exists():
            raise ValueError(f"Build result for student {student_id} not found")

        self._current_project_core_io.unlink(
            path=json_fullpath,
        )
