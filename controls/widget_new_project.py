import zipfile
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtWidgets import *

from controls.dto.new_project_config import NewProjectConfig
from domain.models.values import TargetID, ProjectName
from icons import icon
from service_provider import get_project_list_service, is_debug


class ProjectZipFileSelectorWidget(QWidget):
    @staticmethod
    def _is_project_zipfile_fullpath(folder_fullpath: Path) -> bool:
        if not folder_fullpath.is_absolute():
            return False
        if not folder_fullpath.exists():
            return False
        if not zipfile.is_zipfile(folder_fullpath):
            return False
        with zipfile.ZipFile(folder_fullpath, "r") as zf:
            if "reportlist.xlsx" not in zf.namelist():
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
        layout.addWidget(self._le_fullpath)

        self._b_select_folder = QPushButton(self)
        self._b_select_folder.setIcon(icon("open"))
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

    def showEvent(self, *args, **kwargs):
        if is_debug():
            self._le_fullpath.setText(
                str(Path("~/report_5.zip").expanduser().resolve())
            )


class ProjectNameLineEdit(QLineEdit):
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

    def get_value(self) -> ProjectName:
        return ProjectName(self.text())

    def validate_and_get_reason(self) -> str | None:
        name = self.get_value()
        # noinspection PyTypeChecker
        if get_project_list_service().name_exists(name):
            return "プロジェクト名はすでに存在します"
        return None


class TargetNumberLineEdit(QLineEdit):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setPlaceholderText("設問番号を入力してください")
        self.setValidator(QIntValidator(0, 99, self))

    def showEvent(self, *args, **kwargs):
        if is_debug():
            self.setText("4")

    def get_value(self) -> TargetID:
        return TargetID(self.text())

    def validate_and_get_reason(self) -> str | None:
        try:
            TargetID(self.text())
        except ValueError:
            return "設問番号には数字を入力してください"
        else:
            return None


class NewProjectWidget(QGroupBox):
    # noinspection PyArgumentList
    accepted = pyqtSignal(NewProjectConfig)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setTitle("新しいプロジェクト")

        layout = QGridLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("プロジェクト名", self), 0, 0)

        # noinspection PyTypeChecker
        self._w_project_name = ProjectNameLineEdit(self)
        layout.addWidget(self._w_project_name, 0, 1)

        layout.addWidget(QLabel("提出データ"), 1, 0)

        # noinspection PyTypeChecker
        self._w_project_zipfile_selector = ProjectZipFileSelectorWidget(self)
        layout.addWidget(self._w_project_zipfile_selector, 1, 1)

        layout.addWidget(QLabel("設問番号"), 2, 0)

        # noinspection PyTypeChecker
        self._w_target_number_input = TargetNumberLineEdit(self)
        layout.addWidget(self._w_target_number_input, 2, 1)

        layout_button = QVBoxLayout()
        layout.addLayout(layout_button, 3, 0, 1, 2)

        self._b_create = QPushButton("プロジェクトを作成", self)
        # noinspection PyUnresolvedReferences
        self._b_create.clicked.connect(self._b_create_clicked)
        layout_button.addWidget(self._b_create)

    @pyqtSlot()
    def _b_create_clicked(self):
        validation_results = [
            self._w_project_name.validate_and_get_reason(),
            self._w_project_zipfile_selector.validate_and_get_reason(),
            self._w_target_number_input.validate_and_get_reason(),
        ]
        is_ok = all(validation_result is None for validation_result in validation_results)
        if not is_ok:
            # noinspection PyTypeChecker
            QMessageBox.critical(
                self,
                "プロジェクトを作成",
                "すべての項目を正しく入力してください。\n" + "\n".join(
                    validation_result
                    for validation_result in validation_results
                    if validation_result is not None
                ),
            )
            return
        self.accepted.emit(
            NewProjectConfig(
                project_name=self._w_project_name.get_value(),
                manaba_report_archive_fullpath=self._w_project_zipfile_selector.get_value(),
                target_id=self._w_target_number_input.get_value(),
            )
        )
