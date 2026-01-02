from feature.export.usecase.interface import IGetSimpleScoreExportDataUseCase
from feature.export.domain.model.data import SimpleScoreExportRow
from shared.infra.repository.student import StudentRepository
from shared.domain.service.student_mark_get import StudentMarkEntityGetSubService


class GetSimpleScoreExportDataUseCase(IGetSimpleScoreExportDataUseCase):
    def __init__(
        self,
        *,
        student_repo: StudentRepository,
        student_mark_get_sub_service: StudentMarkEntityGetSubService,
    ):
        self._student_repo = student_repo
        self._student_mark_get_sub_service = student_mark_get_sub_service
    
    def execute(self) -> list[SimpleScoreExportRow]:
        """単純エクスポート用のデータを取得"""
        rows: list[SimpleScoreExportRow] = []
        
        # 全生徒を取得
        students = self._student_repo.list()
        
        # 各生徒の採点結果を取得
        for student in students:
            student_mark = self._student_mark_get_sub_service.execute(student.student_id)
            
            row = SimpleScoreExportRow(
                student_id=student.student_id,
                student_name=student.name,
                score=student_mark.score if student_mark.is_marked else None,
            )
            rows.append(row)
        
        return rows

