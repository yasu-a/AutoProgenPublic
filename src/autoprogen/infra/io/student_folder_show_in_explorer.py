"""学生の展開済み提出フォルダをファイルマネージャで開く。"""

import os

from autoprogen.domain.model.value import StudentID
from autoprogen.infra.path_layout import ProjectPathLayout


class StudentFolderShowInExplorerIO:
    """学生の提出フォルダをWindowsエクスプローラーで開く。"""

    def __init__(self, *, project_path_layout: ProjectPathLayout) -> None:
        """学生の提出フォルダを特定するレイアウトを保持する。"""
        self._project_path_layout = project_path_layout

    def show_submission_folder(self, student_id: StudentID) -> None:
        """フォルダが存在しない場合は無言で成功扱いにせず例外とする。"""
        folder = self._project_path_layout.student_submission_dir(student_id)
        if not folder.is_dir():
            raise FileNotFoundError(f"提出フォルダが存在しません: {folder}")
        os.startfile(folder)
