from autoprogen.domain.error.stage.build import (
    BuildStageError,
    MultipleSourceFilesError,
    SourceEncodingUnknownError,
    SourceFilenameMultipleNumbersError,
    SourceFilenameNoNumberError,
    SubmissionNotFoundError,
    SubmissionSourceNotFoundError,
)
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student_stage_result import BuildSuccessStudentStageResult, \
    BuildFailureStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.service.student_dynamic import StudentDynamicSetSourceCodeService, \
    StudentDynamicClearService
from autoprogen.service.student_stage_path_result import StudentPutStageResultService
from autoprogen.service.student_submission import StudentSubmissionGetSourceCodeService, \
    StudentSubmissionGetChecksumService


def _format_build_stage_error(error: BuildStageError) -> str:
    """BUILDの構造化エラーを従来の保存用メッセージへ変換する。"""
    if isinstance(error, SubmissionNotFoundError):
        return "未提出の学生です。"
    if isinstance(error, SourceFilenameMultipleNumbersError):
        return (
            f"提出フォルダからソースファイルを抽出中にエラーが発生しました。\n"
            f"ファイル名{error.file_relative_path!s}から設問番号を判別できません。\n"
            f"ファイル名に数字が複数含まれています: {', '.join(error.numbers)}"
        )
    if isinstance(error, SourceFilenameNoNumberError):
        return (
            f"提出フォルダからソースファイルを抽出中にエラーが発生しました。\n"
            f"ファイル名{error.file_relative_path!s}から設問番号を判別できません。\n"
            "ファイル名に数字が含まれていません。"
        )
    if isinstance(error, MultipleSourceFilesError):
        paths = "\n".join(map(str, error.file_relative_paths))
        return f"提出物に複数のソースファイルが見つかりました。\n{paths}"
    if isinstance(error, SubmissionSourceNotFoundError):
        return "提出物にソースファイルが見つかりませんでした。"
    if isinstance(error, SourceEncodingUnknownError):
        return (
            "ソースファイルの文字コードが判定できません。\n"
            f"ファイル名: {error.file_relative_path!s}\n"
        )
    raise TypeError(f"未対応のBUILDエラーです: {type(error).__name__}")


class StudentRunBuildStageUseCase:
    """提出物から対象ソースを抽出し、学生の動的データへ保存する。"""

    def __init__(
            self,
            *,
            student_submission_get_source_code_service: StudentSubmissionGetSourceCodeService,
            student_dynamic_clear_service: StudentDynamicClearService,
            student_dynamic_set_source_code_service: StudentDynamicSetSourceCodeService,
            student_submission_get_checksum_service: StudentSubmissionGetChecksumService,
            student_put_stage_result_service: StudentPutStageResultService,
    ):
        """BUILDステージに必要なServiceを受け取る。"""
        self._student_submission_get_source_code_service = student_submission_get_source_code_service
        self._student_dynamic_clear_service = student_dynamic_clear_service
        self._student_dynamic_set_source_code_service = student_dynamic_set_source_code_service
        self._student_submission_get_checksum_service = student_submission_get_checksum_service
        self._student_put_stage_result_service = student_put_stage_result_service

    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
        """学生一人分のBUILDステージを実行して結果を保存する。"""
        # 動的データをクリアする
        self._student_dynamic_clear_service.execute(
            student_id=student_id,
        )

        # ソースコードを探してくる
        try:
            source_code = self._student_submission_get_source_code_service.execute(
                student_id=student_id,
            )
        except BuildStageError as e:
            # 失敗したら異常終了の結果を書きこむ
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=BuildFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason=_format_build_stage_error(e),
                )
            )
        else:
            # ソースコードを動的データに配置
            self._student_dynamic_set_source_code_service.execute(
                student_id=student_id,
                source_code=source_code,
            )

            # 正常終了の結果を書きこんで終了
            submission_folder_checksum = self._student_submission_get_checksum_service.execute(
                student_id=student_id,
            )
            self._student_put_stage_result_service.execute(
                stage_path=stage_path,
                result=BuildSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    submission_folder_checksum=submission_folder_checksum,
                )
            )
