from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from autoprogen.domain.model.project_settings import (
    ProjectSettings,
    SourceCodeCheckIdentifier,
    SourceCodeCheckSkip,
)
from autoprogen.domain.model.source_code_check import SourceCodeCheckCatalog


class ProjectSettingsEditWidget(QTabWidget):
    """静的チェック規則と除外するソースコードを編集するビュー。"""

    def __init__(
            self,
            parent: QWidget = None,
            *,
            catalog: SourceCodeCheckCatalog,
    ) -> None:
        """規則カタログを受け取り、見出しなしの2表を構築する。"""
        super().__init__(parent)
        self._catalog = catalog
        self._rule_ids: list[SourceCodeCheckIdentifier] = []
        self._unknown_suppressed_ids: frozenset[SourceCodeCheckIdentifier] = frozenset()
        self._skips: list[SourceCodeCheckSkip] = []
        self._init_ui()

    def _init_ui(self) -> None:
        """チェック項目と除外項目を別タブへ表示する。"""
        rules_page = QWidget(self)
        rules_layout = QVBoxLayout(rules_page)
        self._rules_table = QTableWidget(0, 4, rules_page)
        self._rules_table.setObjectName("sourceCodeCheckTable")
        self._rules_table.horizontalHeader().hide()
        self._rules_table.verticalHeader().hide()
        self._rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._rules_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._rules_table.setAlternatingRowColors(True)
        self._rules_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self._rules_table.setColumnWidth(0, 55)
        self._rules_table.setColumnWidth(1, 215)
        self._rules_table.setColumnWidth(2, 205)
        self._rules_table.verticalHeader().setDefaultSectionSize(34)
        rules_layout.addWidget(self._rules_table)
        self.addTab(rules_page, "ソースコードの静的セキュリティチェック")

        for group in self._catalog.groups:
            for entry in group.entries:
                row = self._rules_table.rowCount()
                self._rules_table.insertRow(row)
                identifier = SourceCodeCheckIdentifier(
                    group_id=group.group_id,
                    check_id=entry.check_id,
                )
                self._rule_ids.append(identifier)
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox.setCheckState(Qt.Checked)
                checkbox.setToolTip("チェックすると、この規則を適用します")
                self._rules_table.setItem(row, 0, checkbox)
                self._set_readonly_item(
                    self._rules_table, row, 1,
                    f"{group.group_id}.{entry.check_id}", group.name,
                )
                self._set_readonly_item(
                    self._rules_table, row, 2, entry.name, group.name,
                )
                self._set_readonly_item(
                    self._rules_table, row, 3, entry.description, entry.description,
                )

        skips_page = QWidget(self)
        skips_layout = QHBoxLayout(skips_page)
        self._skips_table = QTableWidget(0, 2, skips_page)
        self._skips_table.setObjectName("sourceCodeCheckSkipsTable")
        self._skips_table.horizontalHeader().hide()
        self._skips_table.verticalHeader().hide()
        self._skips_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._skips_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._skips_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._skips_table.setAlternatingRowColors(True)
        self._skips_table.setColumnWidth(0, 160)
        self._skips_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        skips_layout.addWidget(self._skips_table, 1)

        side_layout = QVBoxLayout()
        self._delete_button = QPushButton("削除", skips_page)
        self._delete_button.setObjectName("deleteSourceCodeCheckSkip")
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._remove_selected_skip)
        side_layout.addWidget(self._delete_button)
        side_layout.addStretch(1)
        skips_layout.addLayout(side_layout)
        self._skips_table.itemSelectionChanged.connect(self._update_delete_button)
        self.addTab(skips_page, "セキュリティチェックから除外するソースコード")

    @staticmethod
    def _set_readonly_item(
            table: QTableWidget, row: int, column: int,
            value: str, tooltip: str,
    ) -> None:
        """編集不可のテキストセルを追加する。"""
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setToolTip(tooltip)
        table.setItem(row, column, item)

    def set_data(self, settings: ProjectSettings) -> None:
        """保存済みの設定を両タブへ反映する。"""
        if not isinstance(settings, ProjectSettings):
            raise TypeError("settingsにはProjectSettingsを指定してください")
        known_ids = frozenset(self._rule_ids)
        self._unknown_suppressed_ids = settings.suppressed_source_code_checks - known_ids
        for row, identifier in enumerate(self._rule_ids):
            checkbox = self._rules_table.item(row, 0)
            checkbox.setCheckState(
                Qt.Unchecked if identifier in settings.suppressed_source_code_checks
                else Qt.Checked
            )

        self._skips = sorted(
            settings.source_code_check_skips,
            key=lambda skip: (str(skip.student_id), skip.source_sha256),
        )
        self._skips_table.setRowCount(0)
        for row, skip in enumerate(self._skips):
            self._skips_table.insertRow(row)
            self._set_readonly_item(
                self._skips_table, row, 0, str(skip.student_id), "学籍番号",
            )
            self._set_readonly_item(
                self._skips_table, row, 1, skip.source_sha256, "ソースコードのSHA-256",
            )
        self._skips_table.clearSelection()
        self._update_delete_button()

    def get_data(self) -> ProjectSettings:
        """現在のチェック状態と残った除外情報を設定モデルへ変換する。"""
        suppressed_ids = set(self._unknown_suppressed_ids)
        for row, identifier in enumerate(self._rule_ids):
            if self._rules_table.item(row, 0).checkState() != Qt.Checked:
                suppressed_ids.add(identifier)
        return ProjectSettings(
            suppressed_source_code_checks=frozenset(suppressed_ids),
            source_code_check_skips=frozenset(self._skips),
        )

    def _update_delete_button(self) -> None:
        """削除対象の行がある場合のみボタンを有効化する。"""
        self._delete_button.setEnabled(bool(self._skips_table.selectionModel().selectedRows()))

    def _remove_selected_skip(self) -> None:
        """選択した除外設定を画面上から削除する（保存までは確定しない）。"""
        selection = self._skips_table.selectionModel().selectedRows()
        if not selection:
            return
        row = selection[0].row()
        self._skips.pop(row)
        self._skips_table.removeRow(row)
        self._skips_table.clearSelection()
        self._update_delete_button()
