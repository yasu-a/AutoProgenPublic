import zipfile
from pathlib import Path
from typing import List

from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtWidgets import *
from application.state.debug import is_debug

from app.di.system import get_manaba_report_archive_io
from feature.projman.handler.interface import IProjectCreateView, IProjectCreateHandler
from feature.projman.view.dto import NewProjectConfig
from shared.view.style.font import get_font
from shared.view.style.icon import get_icon
from shared.domain.value.identifier import ProjectID


class SubmissionArchiveSelector(QWidget):
    @staticmethod
    def _is_project_zipfile_fullpath(folder_fullpath: Path) -> bool:
        if not folder_fullpath.is_absolute():
            return False
        if not folder_fullpath.exists():
            return False
        if not zipfile.is_zipfile(folder_fullpath):
            return False
        if not get_manaba_report_archive_io(folder_fullpath).validate_master_excel_exists():
            return False
        return True

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._le_fullpath = QLineEdit(self)
        self._le_fullpath.setReadOnly(True)
        self._le_fullpath.setPlaceholderText("reportlist.xlsxが入ったZIPファイルを選択してください")
        if is_debug():
            self._le_fullpath.setText(
                str(Path("~/report_5.zip").expanduser().resolve())
            )
        layout.addWidget(self._le_fullpath)

        self._b_select_folder = QPushButton(self)
        self._b_select_folder.setIcon(get_icon("folder"))
        self._b_select_folder.setFixedWidth(30)
        # noinspection PyUnresolvedReferences
        self._b_select_folder.clicked.connect(self._b_select_folder_clicked)
        layout.addWidget(self._b_select_folder)

    @pyqtSlot()
    def _b_select_folder_clicked(self):
        # noinspection PyArgumentList,PyTypeChecker
        fullpath, _ = QFileDialog.getOpenFileName(
            self,
            "manabaからダウンロードしたzipファイルを選択",
            QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
            "Zipファイル (*.zip)",
        )
        if not fullpath:
            return
        fullpath = Path(fullpath)
        if not self._is_project_zipfile_fullpath(fullpath):
            # noinspection PyTypeChecker
            QMessageBox.critical(
                self,
                "manabaからダウンロードしたzipファイルを選択",
                "選択したファイルの形式には対応していません。"
                "reportlist.xlsxが含まれたzipファイルを選択してください。"
            )
            return
        self._le_fullpath.setText(str(fullpath))

    def get_value(self) -> Path:
        return Path(self._le_fullpath.text())

    def validate_and_get_reason(self) -> str | None:
        if self._is_project_zipfile_fullpath(self.get_value()):
            return None
        else:
            return "選択したZIPファイルの形式には対応していません。reportlist.xlsxが含まれたzipファイルを選択してください。"


class ProjectNameInput(QLineEdit):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setPlaceholderText("プロジェクト名を入力してください")
        self.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9_-]+"), self))

    def showEvent(self, *args, **kwargs):
        if is_debug():
            import random
            self.setText(f"proj-{random.randint(0, 10000)!s}")

    def get_value(self) -> str:
        return self.text()

    def validate_and_get_reason(self) -> str | None:
        project_name = self.get_value().strip()
        if not project_name:
            return "プロジェクト名が入力されていません"
        try:
            ProjectID(project_name)
        except ValueError:
            return "プロジェクト名に使用できない文字が含まれています"
        # プロジェクト名の重複チェックはHandlerが行う（独立性の原則）
        return None


class TargetNumberInput(QLineEdit):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setPlaceholderText("設問番号を入力してください")
        self.setValidator(QIntValidator(0, 99, self))

    def showEvent(self, *args, **kwargs):
        if is_debug():
            self.setText("4")

    def get_value(self) -> int:
        return int(self.text())

    def validate_and_get_reason(self) -> str | None:
        try:
            int(self.text())
        except ValueError:
            return "設問番号には数字を入力してください"
        else:
            return None


class ProjectCreateView(QWidget, IProjectCreateView):
    # noinspection PyArgumentList
    project_created = pyqtSignal(NewProjectConfig, name="project_created")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._handler: IProjectCreateHandler | None = None

        self._init_ui()

    def set_handler(self, handler: IProjectCreateHandler) -> None:
        """Handlerを注入（DI）"""
        self._handler = handler

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        layout_form = QGridLayout()
        layout.addLayout(layout_form)

        layout_form.addWidget(QLabel("プロジェクト名", self), 0, 0)

        # noinspection PyTypeChecker
        self._w_project_name = ProjectNameInput(self)
        layout_form.addWidget(self._w_project_name, 0, 1)

        layout_form.addWidget(QLabel("提出データ"), 1, 0)

        # noinspection PyTypeChecker
        self._w_submission_archive_selector = SubmissionArchiveSelector(self)
        layout_form.addWidget(self._w_submission_archive_selector, 1, 1)

        layout_form.addWidget(QLabel("設問番号"), 2, 0)

        # noinspection PyTypeChecker
        self._w_target_number = TargetNumberInput(self)
        layout_form.addWidget(self._w_target_number, 2, 1)

        layout_button = QHBoxLayout()
        layout.addLayout(layout_button)

        layout_button.addStretch(1)

        self._b_create = QPushButton("START", self)
        self._b_create.setMinimumWidth(200)
        self._b_create.setMinimumHeight(30)
        self._b_create.setFont(get_font(bold=True, monospace=True))
        # noinspection PyUnresolvedReferences
        self._b_create.clicked.connect(self._b_create_clicked)
        layout_button.addWidget(self._b_create)

        layout_button.addStretch(1)

        layout.addStretch(1)

    @pyqtSlot()
    def _b_create_clicked(self):
        """作成ボタンクリック → Handlerに通知"""
        if self._handler:
            self._handler.on_create_requested()
        else:
            # Handler未設定時のフォールバック（旧実装互換）
            errors = self.validate_and_get_errors()
            if errors:
                self.show_validation_errors(errors)
                return
            config = self.get_create_result()
            if config:
                self.project_created.emit(config)

    # ===== IProjectCreateView実装 =====
    def get_project_name(self) -> str:
        """プロジェクト名を取得"""
        return self._w_project_name.get_value()

    def get_target_number(self) -> int:
        """設問番号を取得"""
        return self._w_target_number.get_value()

    def get_submission_archive_path(self) -> Path:
        """提出アーカイブのパスを取得"""
        return self._w_submission_archive_selector.get_value()

    def validate_and_get_errors(self) -> List[str]:
        """バリデーション実行（戻り値: エラーリスト、空ならOK）"""
        errors = []

        # 各フィールドのバリデーション
        project_name_error = self._w_project_name.validate_and_get_reason()
        if project_name_error:
            errors.append(project_name_error)

        archive_error = self._w_submission_archive_selector.validate_and_get_reason()
        if archive_error:
            errors.append(archive_error)

        target_number_error = self._w_target_number.validate_and_get_reason()
        if target_number_error:
            errors.append(target_number_error)

        return errors

    def show_validation_errors(self, errors: List[str]) -> None:
        """バリデーションエラーを表示"""
        QMessageBox.critical(
            self,
            "プロジェクトを作成",
            "すべての項目を正しく入力してください。\n\n" + "\n".join(
                "◆ " + error for error in errors
            ),
        )

    def get_create_result(self) -> NewProjectConfig | None:
        """作成結果を取得（バリデーション済み）"""
        errors = self.validate_and_get_errors()
        if errors:
            return None

        return NewProjectConfig(
            project_name=self.get_project_name(),
            manaba_report_archive_fullpath=self.get_submission_archive_path(),
            target_number=self.get_target_number(),
        )

    def notify_project_created(self, config: NewProjectConfig) -> None:
        """プロジェクト作成成功を通知（Handlerから呼ばれる）"""
        self.project_created.emit(config)
