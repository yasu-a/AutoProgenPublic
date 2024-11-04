import os
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot, QStandardPaths
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, \
    QVBoxLayout, QPlainTextEdit, QPushButton, QLineEdit, QComboBox, \
    QFileDialog, QMessageBox

from app_logging import create_logger
from application.dependency.external_io import get_score_excel_io
from application.dependency.services import get_current_project_get_service
from application.dependency.usecases import get_student_list_id_usecase, \
    get_student_mark_list_usecase, get_global_config_get_usecase
from controls.res.icons import icon
from controls.widget_horizontal_line import HorizontalLineWidget
from domain.models.student_mark import StudentMark
from domain.models.values import StudentID, TargetID


class ScoreExportDialog(QDialog):  # FIXME: usecase化
    _logger = create_logger()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._student_ids: list[StudentID] = get_student_list_id_usecase().execute()
        self._target_id: TargetID = get_current_project_get_service().execute().target_id
        self._student_marks: list[StudentMark] = get_student_mark_list_usecase().execute()

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setWindowTitle("採点結果のエクスポート")
        self.setModal(True)
        self.resize(800, 500)
        self.installEventFilter(self)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)

        layout.addWidget(QLabel("1. エクスポート先のExcelワークブックを選択してください", self))

        layout_path = QHBoxLayout()
        layout.addLayout(layout_path)

        self._le_excel_fullpath = QLineEdit(self)
        layout_path.addWidget(self._le_excel_fullpath)

        self._b_select_excel_fullpath = QPushButton(self)
        self._b_select_excel_fullpath.setIcon(icon("open"))
        self._b_select_excel_fullpath.setFixedWidth(30)
        layout_path.addWidget(self._b_select_excel_fullpath)

        self._te_message = QPlainTextEdit(self)
        self._te_message.setReadOnly(True)
        self._te_message.setEnabled(False)
        layout.addWidget(self._te_message)

        layout.addWidget(HorizontalLineWidget())

        layout.addWidget(QLabel("2. エクスポート先のワークシートを選択してください", self))

        self._dl_sheet_names = QComboBox(self)
        self._dl_sheet_names.setEnabled(False)
        layout.addWidget(self._dl_sheet_names)

        layout.addWidget(HorizontalLineWidget())

        layout.addWidget(QLabel("3. 設問番号を確認してください", self))

        layout.addWidget(QLabel(" 設問番号: " + str(self._target_id), self))

        layout.addWidget(HorizontalLineWidget())

        layout.addWidget(QLabel("4. 書き込む", self))

        self._b_export = QPushButton("エクスポート", self)
        self._b_export.setEnabled(False)
        layout.addWidget(self._b_export)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._le_excel_fullpath.textChanged.connect(self.__le_excel_fullpath_text_changed)
        # noinspection PyUnresolvedReferences
        self._b_select_excel_fullpath.clicked.connect(self.__b_select_excel_fullpath_clicked)
        # noinspection PyUnresolvedReferences
        self._b_export.clicked.connect(self.__b_export_clicked)

    @pyqtSlot()
    def __b_select_excel_fullpath_clicked(self):
        # noinspection PyArgumentList,PyTypeChecker
        fullpath, _ = QFileDialog.getOpenFileName(
            self,
            "エクスポート先のエクセルファイルを選択",
            QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
            "Zipファイル (*.xlsx)",
        )
        if not fullpath:
            return
        fullpath = Path(fullpath)
        self._le_excel_fullpath.setText(str(fullpath))

    def _try_get_excel_fullpath(self) -> Path | None:
        excel_fullpath = Path(self._le_excel_fullpath.text())
        if not excel_fullpath.exists():
            return None
        if not excel_fullpath.is_file():
            return None
        if excel_fullpath.suffix != ".xlsx":
            return None
        return excel_fullpath

    def _has_valid_worksheet_names(self) -> bool:
        return self._dl_sheet_names.count() > 0

    def _clear_and_set_error_state(self):
        self._dl_sheet_names.clear()
        self._dl_sheet_names.setEnabled(False)
        self._te_message.clear()
        self._te_message.setEnabled(False)
        self._le_excel_fullpath.setStyleSheet("background-color: orange")
        self._b_export.setEnabled(False)

    def _update_state(self):
        # 読み込めていたら
        if self._has_valid_worksheet_names():
            # 全部有効化
            self._dl_sheet_names.setEnabled(True)
            self._b_export.setEnabled(True)
            self._le_excel_fullpath.setStyleSheet("background-color: lightgreen")

    @pyqtSlot()
    def __le_excel_fullpath_text_changed(self):
        self._clear_and_set_error_state()

        # エクセルのパスを取得
        excel_fullpath = self._try_get_excel_fullpath()
        if excel_fullpath is None:
            return

        # ワークシートの状態を読み取って正常なら選択肢に追加，そうでなければエラーを表示
        worksheet_stats = get_score_excel_io(excel_fullpath).list_worksheet_stats(
            student_ids=self._student_ids,
        )
        messages = []
        for s in worksheet_stats:
            if s.valid:
                # 正常
                self._dl_sheet_names.addItem(s.name)
            else:
                # エラー
                messages.append(f" [ {s.name} ] \n{s.message}")
        if messages and self._dl_sheet_names.count() == 0:
            messages.insert(
                0,
                "すべてのワークシートが読み込めません。"
                "成績記録用のワークブックを指定しましたか？",
            )
        elif messages:
            messages.insert(
                0,
                "ワークシートの読み込みが完了しました。"
                "ただし次のシートにはエクスポートできません。",
            )
        else:
            messages.insert(
                0,
                "すべてのワークシートを読み込みました",
            )
        self._te_message.setPlainText("\n".join(messages))
        self._te_message.setEnabled(True)

        self._update_state()

    @pyqtSlot()
    def __b_export_clicked(self):
        if not self._has_valid_worksheet_names():
            return

        # エクセルのパスを取得
        excel_fullpath = self._try_get_excel_fullpath()
        if excel_fullpath is None:
            return

        worksheet_name = self._dl_sheet_names.currentText()

        if get_score_excel_io(excel_fullpath).has_data(
                student_ids=self._student_ids,
                worksheet_name=worksheet_name,
                target_id=self._target_id,
        ):
            if QMessageBox.question(
                    self,
                    "点数のエクスポート",
                    f"シート名{worksheet_name}の設問{int(self._target_id)}に入力データが存在しますが上書きしますか？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
            ) == QMessageBox.No:
                return
        try:
            backup_path = get_score_excel_io(excel_fullpath).apply(
                worksheet_name=worksheet_name,
                target_id=self._target_id,
                student_marks=self._student_marks,
                do_backup=get_global_config_get_usecase().execute().backup_before_export,
            )
        except Exception as e:
            self._logger.info("Failed to commit scores to the workbook")
            self._logger.exception(e)
            # noinspection PyTypeChecker
            QMessageBox.critical(
                self,
                "点数のエクスポート",
                "エクスポートに失敗しました。\n" + "\n".join(map(str, e.args)),
            )
        else:
            if QMessageBox.question(
                    self,
                    "点数のエクスポート",
                    (
                            ""
                            if backup_path is None
                            else f"Excelファイルのバックアップを取りました：\n{backup_path!s}\n\n"
                    )
                    + "エクスポートが完了しました。ワークブックを開いて確認しますか？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
            ) == QMessageBox.Yes:
                os.startfile(excel_fullpath)
