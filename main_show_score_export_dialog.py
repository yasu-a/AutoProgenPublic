"""
ScoreExportDialogを表示するテストスクリプト
仮データでダイアログを表示します。
メモリ上で動作するため、実際のファイルを汚しません。
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication

from app.di.state import get_current_project_id_state
from shared.domain.entity.student import StudentEntity
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.value.identifier import StudentID, TargetID, ProjectID
from shared.infra.repository.student import InMemoryStudentRepository
from shared.infra.repository.student_mark import InMemoryStudentScoreRepository


def load_master_data() -> list[dict]:
    """static/test/master.jsonからマスターデータを読み込む"""
    master_json_path = Path("static/test/master.json")
    if not master_json_path.exists():
        raise FileNotFoundError(f"マスターデータが見つかりません: {master_json_path}")

    with open(master_json_path, encoding="utf-8") as f:
        return json.load(f)


def create_student_entities(master_data: list[dict]) -> list[StudentEntity]:
    """マスターデータからStudentEntityのリストを作成"""
    students = []
    for data in master_data:
        submitted_at = None
        if data.get("submitted_at"):
            submitted_at = datetime.fromtimestamp(data["submitted_at"])

        student = StudentEntity(
            student_id=StudentID(data["student_id"]),
            name=data["name"],
            name_en=data["name_en"],
            email_address=data["email_address"],
            submitted_at=submitted_at,
            num_submissions=data.get("num_submissions", 0),
            submission_folder_name=data.get("submission_folder_name"),
        )
        students.append(student)
    return students


def create_test_scores(students: list[StudentEntity]) -> list[StudentMarkEntity]:
    """適当な点数データを作成"""
    marks = []
    # 一部の生徒に点数を付与（採点済み）
    scored_students = students[:6]  # 最初の6人に点数を付与
    scores = [85, 90, 75, 95, 80, 88]  # 適当な点数

    for student, score in zip(scored_students, scores):
        mark = StudentMarkEntity(
            student_id=student.student_id,
            score=score,
        )
        marks.append(mark)

    # 残りの生徒は未採点（score=None）
    for student in students[6:]:
        mark = StudentMarkEntity(
            student_id=student.student_id,
            score=None,
        )
        marks.append(mark)

    return marks


def main():
    """メイン処理"""
    # QApplicationを作成（main.pyと同じスタイルを適用）
    from app.qt_style import apply_qt_style

    app = QApplication(sys.argv)
    apply_qt_style(app, set_app_info=False)

    # テスト用のプロジェクトIDを設定（メモリ上で動作するため実際のプロジェクトは使用しない）
    test_project_id = ProjectID("test_project")
    get_current_project_id_state().update(test_project_id)

    # マスターデータを読み込んでエンティティを作成
    master_data = load_master_data()
    students = create_student_entities(master_data)
    marks = create_test_scores(students)

    # メモリベースのリポジトリを作成（初期データをコンストラクタで設定）
    student_repo = InMemoryStudentRepository(students=students)
    student_score_repo = InMemoryStudentScoreRepository(marks=marks)

    # テスト用のtarget_id（mock用）
    test_target_id = TargetID("3")

    # CurrentProjectSummaryGetUseCaseをmockしてtarget_idを返すようにする
    from feature.projman.usecase.interface import ICurrentProjectSummaryGetUseCase
    from unittest.mock import MagicMock
    from feature.projman.usecase.interface import NormalProjectSummary

    mock_project_summary = NormalProjectSummary(
        project_id=test_project_id,
        target_number=int(test_target_id),
        zip_name="test.zip",
        open_at=datetime.now(),
    )
    mock_current_project_summary_get_usecase = MagicMock(spec=ICurrentProjectSummaryGetUseCase)
    mock_current_project_summary_get_usecase.execute.return_value = mock_project_summary

    # DI関数をパッチしてメモリベースのリポジトリとmock UseCaseを返すようにする
    with patch('app.di.repository.get_student_repository', return_value=student_repo), \
            patch('app.di.repository.get_student_mark_repository', return_value=student_score_repo), \
            patch('app.di.usecase.get_current_project_summary_get_usecase',
                  return_value=mock_current_project_summary_get_usecase):
        # Navigatorを使ってダイアログを開く
        from app.di.app import get_navigator

        navigator = get_navigator()
        navigator.open_score_export_dialog(parent=None, target_id=test_target_id)


if __name__ == "__main__":
    main()
