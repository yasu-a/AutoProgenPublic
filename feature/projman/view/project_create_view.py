from PyQt5.QtCore import *
from PyQt5.QtGui import QIntValidator, QRegExpValidator, QShowEvent
from PyQt5.QtWidgets import *

from feature.projman.handler.interface import IProjectCreateView, IProjectCreateHandler
from feature.projman.handler.interface import NewProjectConfigDto
from shared.view.style.font import get_font
from shared.view.style.icon import get_icon


class ProjectCreateView(QWidget, IProjectCreateView):
    # noinspection PyArgumentList
    project_created = pyqtSignal(NewProjectConfigDto, name="project_created")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._handler: IProjectCreateHandler

        self._init_ui()

    def set_handler(self, handler: IProjectCreateHandler) -> None:
        """Handlerを注入（DI）"""
        # noinspection PyAttributeOutsideInit
        self._handler = handler

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        layout_form = QGridLayout()
        layout.addLayout(layout_form)

        # プロジェクト名
        layout_form.addWidget(QLabel("プロジェクト名", self), 0, 0)
        self._le_project_name = QLineEdit(self)
        self._le_project_name.setPlaceholderText("プロジェクト名を入力してください")
        self._le_project_name.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9_-]+"), self))
        layout_form.addWidget(self._le_project_name, 0, 1)

        # 提出データ
        layout_form.addWidget(QLabel("提出データ"), 1, 0)

        layout_archive = QHBoxLayout()
        self._le_archive_path = QLineEdit(self)
        self._le_archive_path.setReadOnly(True)
        self._le_archive_path.setPlaceholderText(
            "reportlist.xlsxが入ったZIPファイルを選択してください")
        layout_archive.addWidget(self._le_archive_path)

        self._b_select_folder = QPushButton(self)
        self._b_select_folder.setIcon(get_icon("folder"))
        self._b_select_folder.setFixedWidth(30)
        # noinspection PyUnresolvedReferences
        self._b_select_folder.clicked.connect(self._b_select_folder_clicked)
        layout_archive.addWidget(self._b_select_folder)

        layout_form.addLayout(layout_archive, 1, 1)

        # 設問番号
        layout_form.addWidget(QLabel("設問番号"), 2, 0)
        self._le_target_number = QLineEdit(self)
        self._le_target_number.setPlaceholderText("設問番号を入力してください")
        self._le_target_number.setValidator(QIntValidator(0, 99, self))
        layout_form.addWidget(self._le_target_number, 2, 1)

        # ボタンエリア
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

    def showEvent(self, evt: QShowEvent) -> None:
        """表示イベント：Handlerに初期化を通知"""
        super().showEvent(evt)
        self._handler.on_view_initialized()

    @pyqtSlot()
    def _b_select_folder_clicked(self):
        # noinspection PyArgumentList,PyTypeChecker
        fullpath, _ = QFileDialog.getOpenFileName(
            self,
            "manabaからダウンロードしたzipファイルを選択",
            QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
            "Zipファイル (*.zip)",
        )
        if fullpath:
            self._le_archive_path.setText(str(fullpath))

    @pyqtSlot()
    def _b_create_clicked(self):
        """作成ボタンクリック → Handlerに通知"""
        self._handler.on_create_requested()

    # ===== IProjectCreateView実装 =====
    def get_project_name(self) -> str:
        """プロジェクト名を取得"""
        return self._le_project_name.text()

    def set_project_name(self, name: str) -> None:
        """プロジェクト名を設定"""
        self._le_project_name.setText(name)

    def get_target_number(self) -> str:
        """設問番号を取得"""
        return self._le_target_number.text()

    def set_target_number(self, number: str) -> None:
        """設問番号を設定"""
        self._le_target_number.setText(number)

    def get_submission_archive_path(self) -> str:
        """提出アーカイブのパスを取得"""
        return self._le_archive_path.text()

    def set_submission_archive_path(self, path: str) -> None:
        """提出アーカイブのパスを設定"""
        self._le_archive_path.setText(path)

    def show_validation_errors(self, errors: list[str]) -> None:
        """バリデーションエラーを表示"""
        QMessageBox.critical(
            self,
            "プロジェクトを作成",
            "すべての項目を正しく入力してください。\n\n" + "\n".join(
                "◆ " + error for error in errors
            ),
        )

    def notify_project_created(self, config: NewProjectConfigDto) -> None:
        """プロジェクト作成成功を通知（Handlerから呼ばれる）"""
        self.project_created.emit(config)
