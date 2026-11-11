import zipfile
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QRegExpValidator, QShowEvent
from PyQt5.QtWidgets import *

from autoprogen.control.dto.new_project_config import NewProjectConfig
from autoprogen.domain.model.value import ProjectID
from autoprogen.res.font import get_font
from autoprogen.res.icon import get_icon
from autoprogen.usecase.manaba_report_archive import ManabaReportArchiveValidateMasterExcelExistsUseCase
from autoprogen.usecase.project import ProjectCheckExistByNameUseCase


class ProjectZipFileSelectorWidget(QWidget):
    """提出アーカイブの選択と形式検証を提供する。"""

    def __init__(
            self,
            parent: QObject = None,
            *,
            initial_fullpath: Path | None,
            manaba_report_archive_validate_master_excel_exists_usecase: ManabaReportArchiveValidateMasterExcelExistsUseCase,
    ) -> None:
        """提出アーカイブの初期パスと検証ユースケースを受け取る。"""
        super().__init__(parent)
        self._initial_fullpath = initial_fullpath
        self._manaba_report_archive_validate_master_excel_exists_usecase = (
            manaba_report_archive_validate_master_excel_exists_usecase
        )
        self._init_ui()

    def _is_project_zipfile_fullpath(self, folder_fullpath: Path) -> bool:
        if not folder_fullpath.is_absolute():
            return False
        if not folder_fullpath.exists():
            return False
        if not zipfile.is_zipfile(folder_fullpath):
            return False
        if not self._manaba_report_archive_validate_master_excel_exists_usecase.execute(folder_fullpath):
            return False
        return True

    def _init_ui(self) -> None:
        """提出アーカイブを選択する入力欄を構築する。"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._le_fullpath = QLineEdit(self)
        self._le_fullpath.setReadOnly(True)
        self._le_fullpath.setPlaceholderText("reportlist.xlsxが入ったZIPファイルを選択してください")
        if self._initial_fullpath is not None:
            self._le_fullpath.setText(str(self._initial_fullpath))
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


class ProjectNameLineEdit(QLineEdit):
    """プロジェクト名の入力と重複検証を提供する。"""

    def __init__(
            self,
            parent: QObject = None,
            *,
            auto_generate_project_name: bool,
            project_check_exist_by_name_usecase: ProjectCheckExistByNameUseCase,
    ) -> None:
        """自動生成の有無とプロジェクト名の検証処理を受け取る。"""
        super().__init__(parent)

        self._auto_generate_project_name = auto_generate_project_name
        self._project_check_exist_by_name_usecase = project_check_exist_by_name_usecase
        self._init_ui()

    def _init_ui(self) -> None:
        """プロジェクト名の入力規則を設定する。"""
        self.setPlaceholderText("プロジェクト名を入力してください")
        self.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9_-]+"), self))

    def showEvent(self, event: QShowEvent) -> None:
        """初回表示時に指定されていればプロジェクト名を自動生成する。"""
        super().showEvent(event)
        if self._auto_generate_project_name and not self.text():
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
        # noinspection PyTypeChecker
        if self._project_check_exist_by_name_usecase.execute(project_name):
            return "プロジェクト名はすでに存在します"
        return None


class TargetNumberLineEdit(QLineEdit):
    """設問番号の入力と形式検証を提供する。"""

    def __init__(
            self,
            parent: QObject = None,
            *,
            initial_value: int | None,
    ) -> None:
        """設問番号として表示する任意の初期値を受け取る。"""
        super().__init__(parent)

        self._initial_value = initial_value
        self._init_ui()

    def _init_ui(self) -> None:
        """設問番号の入力規則と初期値を設定する。"""
        self.setPlaceholderText("設問番号を入力してください")
        self.setValidator(QIntValidator(0, 99, self))
        if self._initial_value is not None:
            self.setText(str(self._initial_value))

    def get_value(self) -> int:
        return int(self.text())

    def validate_and_get_reason(self) -> str | None:
        try:
            int(self.text())
        except ValueError:
            return "設問番号には数字を入力してください"
        else:
            return None


class NewProjectWidget(QWidget):
    """新規プロジェクト作成に必要な入力欄と開始操作を提供する。"""

    # noinspection PyArgumentList
    accepted = pyqtSignal(NewProjectConfig)

    def __init__(
            self,
            parent: QObject = None,
            *,
            auto_generate_project_name: bool,
            initial_report_archive_fullpath: Path | None,
            initial_target_number: int | None,
            project_check_exist_by_name_usecase: ProjectCheckExistByNameUseCase,
            manaba_report_archive_validate_master_excel_exists_usecase: ManabaReportArchiveValidateMasterExcelExistsUseCase,
    ) -> None:
        """画面の初期値とプロジェクト作成前の検証処理を受け取る。"""
        super().__init__(parent)

        self._auto_generate_project_name = auto_generate_project_name
        self._initial_report_archive_fullpath = initial_report_archive_fullpath
        self._initial_target_number = initial_target_number
        self._project_check_exist_by_name_usecase = project_check_exist_by_name_usecase
        self._manaba_report_archive_validate_master_excel_exists_usecase = (
            manaba_report_archive_validate_master_excel_exists_usecase
        )
        self._init_ui()

    def _init_ui(self) -> None:
        """新規プロジェクト作成画面を構築する。"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        if "form":
            layout_form = QGridLayout()
            layout.addLayout(layout_form)

            layout_form.addWidget(QLabel("プロジェクト名", self), 0, 0)

            # noinspection PyTypeChecker
            self._w_project_id = ProjectNameLineEdit(
                self,
                auto_generate_project_name=self._auto_generate_project_name,
                project_check_exist_by_name_usecase=self._project_check_exist_by_name_usecase,
            )
            layout_form.addWidget(self._w_project_id, 0, 1)

            layout_form.addWidget(QLabel("提出データ"), 1, 0)

            # noinspection PyTypeChecker
            self._w_project_zipfile_selector = ProjectZipFileSelectorWidget(
                self,
                initial_fullpath=self._initial_report_archive_fullpath,
                manaba_report_archive_validate_master_excel_exists_usecase=(
                    self._manaba_report_archive_validate_master_excel_exists_usecase
                ),
            )
            layout_form.addWidget(self._w_project_zipfile_selector, 1, 1)

            layout_form.addWidget(QLabel("設問番号"), 2, 0)

            # noinspection PyTypeChecker
            self._w_target_number_input = TargetNumberLineEdit(
                self,
                initial_value=self._initial_target_number,
            )
            layout_form.addWidget(self._w_target_number_input, 2, 1)

        if "button":
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
        validation_results = [
            self._w_project_id.validate_and_get_reason(),
            self._w_project_zipfile_selector.validate_and_get_reason(),
            self._w_target_number_input.validate_and_get_reason(),
        ]
        is_ok = all(validation_result is None for validation_result in validation_results)
        if not is_ok:
            # noinspection PyTypeChecker
            QMessageBox.critical(
                self,
                "プロジェクトを作成",
                "すべての項目を正しく入力してください。\n\n" + "\n".join(
                    "◆ " + validation_result
                    for validation_result in validation_results
                    if validation_result is not None
                ),
            )
            return
        self.accepted.emit(
            NewProjectConfig(
                project_name=self._w_project_id.get_value(),
                manaba_report_archive_fullpath=self._w_project_zipfile_selector.get_value(),
                target_number=self._w_target_number_input.get_value(),
            )
        )
