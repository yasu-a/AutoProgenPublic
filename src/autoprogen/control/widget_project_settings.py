from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from autoprogen.control.widget_source_code_text_edit import SourceCodeTextEdit
from autoprogen.domain.model.project_settings import (
    ProjectSettings,
    SourceCodeCheckIdentifier,
    SourceCodeCheckSkip,
    SourceCodeCheckSuppressions,
)
from autoprogen.domain.model.source_code_check import SourceCodeCheckCatalog, SourceCodeCheckEntry
from autoprogen.res.font import get_font


class ProjectSettingsEditWidget(QTabWidget):
    """静的チェック規則と除外するソースコードを編集するビュー。"""

    _TARGET_STRINGS_ROW_MAX_WIDTH = 300
    _TARGET_STRING_SPACING = 4

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
        self._rule_entries: list[SourceCodeCheckEntry] = []
        self._rule_target_labels: list[QLabel] = []
        self._rule_target_rows: list[QWidget] = []
        self._unknown_suppressed_ids: frozenset[SourceCodeCheckIdentifier] = frozenset()
        self._skips: list[SourceCodeCheckSkip] = []
        self._init_ui()

    def _init_ui(self) -> None:
        """チェック項目と除外項目を別タブへ表示する。"""
        rules_page = QWidget(self)
        rules_layout = QVBoxLayout(rules_page)
        rules_description = QLabel(
            "学生のソースコードに適用するチェック規則を選択します。"
            "チェックした規則に該当する操作が検出された場合、その学生のソースコードは"
            "コンパイルされません。チェックを外した規則は、このプロジェクトでは検査しません。",
            rules_page,
        )
        rules_description.setWordWrap(True)
        rules_layout.addWidget(rules_description)

        rules_content_layout = QHBoxLayout()
        rules_table_layout = QVBoxLayout()
        self._rule_search = QLineEdit(rules_page)
        self._rule_search.setObjectName("sourceCodeCheckSearch")
        self._rule_search.setPlaceholderText("規則を検索")
        self._rule_search.setClearButtonEnabled(True)
        self._rule_search.textChanged.connect(self._search_rules)
        rules_table_layout.addWidget(self._rule_search)
        self._rules_table = QTableWidget(0, 3, rules_page)
        self._rules_table.setObjectName("sourceCodeCheckTable")
        self._rules_table.horizontalHeader().hide()
        self._rules_table.verticalHeader().hide()
        self._rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._rules_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._rules_table.setColumnWidth(0, 55)
        self._rules_table.setColumnWidth(1, 215)
        self._rules_table.verticalHeader().setDefaultSectionSize(23)
        self._rules_table.itemSelectionChanged.connect(self._show_selected_rule_detail)
        rules_table_layout.addWidget(self._rules_table, 1)
        rules_content_layout.addLayout(rules_table_layout, 3)

        rule_detail_layout = QVBoxLayout()
        detail_title = QLabel("規則の説明", rules_page)
        detail_title.setStyleSheet("font-weight: bold;")
        rule_detail_layout.addWidget(detail_title)
        self._rule_description = QLabel(rules_page)
        self._rule_description.setObjectName("sourceCodeCheckDescription")
        self._rule_description.setWordWrap(True)
        self._rule_description.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        rule_detail_layout.addWidget(self._rule_description)
        target_strings_title = QLabel("検出する単語", rules_page)
        target_strings_title.setStyleSheet("font-weight: bold;")
        rule_detail_layout.addWidget(target_strings_title)
        self._rule_target_strings_layout = QVBoxLayout()
        self._rule_target_strings_layout.setContentsMargins(0, 0, 0, 0)
        self._rule_target_strings_layout.setSpacing(self._TARGET_STRING_SPACING)
        rule_detail_layout.addLayout(self._rule_target_strings_layout)
        rule_detail_layout.addStretch(1)
        example_title = QLabel("代表的なソースコード", rules_page)
        example_title.setStyleSheet("font-weight: bold;")
        rule_detail_layout.addWidget(example_title)
        self._rule_example = SourceCodeTextEdit(rules_page)
        self._rule_example.setObjectName("sourceCodeCheckExample")
        self._rule_example.setReadOnly(True)
        self._rule_example.setFixedHeight(250)
        self._rule_example.setPlaceholderText("コード例は準備中です。")
        rule_detail_layout.addWidget(self._rule_example)
        rules_content_layout.addLayout(rule_detail_layout, 2)
        rules_layout.addLayout(rules_content_layout, 1)
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
                self._rule_entries.append(entry)
                checkbox = QTableWidgetItem()
                checkbox.setFlags(
                    Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
                )
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

        if self._rules_table.rowCount() > 0:
            self._rules_table.selectRow(0)

        skips_page = QWidget(self)
        skips_layout = QVBoxLayout(skips_page)
        skips_description = QLabel(
            "安全性を確認して個別に許可したソースコードの一覧です。"
            "削除すると、次回のコンパイル時から安全性チェックを再び実行します。",
            skips_page,
        )
        skips_description.setWordWrap(True)
        skips_layout.addWidget(skips_description)

        skips_content_layout = QHBoxLayout()
        self._skips_table = QTableWidget(0, 2, skips_page)
        self._skips_table.setObjectName("sourceCodeCheckSkipsTable")
        self._skips_table.setHorizontalHeaderLabels(("学籍番号", "ソースコード SHA-256"))
        self._skips_table.verticalHeader().hide()
        self._skips_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._skips_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._skips_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._skips_table.setAlternatingRowColors(True)
        self._skips_table.setColumnWidth(0, 160)
        self._skips_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        skips_content_layout.addWidget(self._skips_table, 1)

        side_layout = QVBoxLayout()
        self._delete_button = QPushButton("削除", skips_page)
        self._delete_button.setObjectName("deleteSourceCodeCheckSkip")
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._remove_selected_skip)
        side_layout.addWidget(self._delete_button)
        side_layout.addStretch(1)
        skips_content_layout.addLayout(side_layout)
        skips_layout.addLayout(skips_content_layout, 1)
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
        self._unknown_suppressed_ids = frozenset(
            identifier
            for identifier in settings.suppressed_source_code_checks
            if identifier not in known_ids
        )
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
            suppressed_source_code_checks=SourceCodeCheckSuppressions(suppressed_ids),
            source_code_check_skips=frozenset(self._skips),
        )

    def _update_delete_button(self) -> None:
        """削除対象の行がある場合のみボタンを有効化する。"""
        self._delete_button.setEnabled(bool(self._skips_table.selectionModel().selectedRows()))

    def _show_selected_rule_detail(self) -> None:
        """選択行に対応する規則の説明とソースコード例を表示する。"""
        selected_rows = self._rules_table.selectionModel().selectedRows()
        if not selected_rows:
            self._rule_description.clear()
            self._show_rule_target_strings(())
            self._rule_example.clear()
            self._rule_example.setExtraSelections([])
            return
        entry = self._rule_entries[selected_rows[0].row()]
        self._rule_description.setText(entry.description)
        self._show_rule_target_strings(entry.target_strings)
        self._rule_example.setPlainText(entry.example_source_code)
        self._rule_example.set_highlighted_lines(
            entry.example_highlighted_line_numbers,
        )

    def _show_rule_target_strings(self, target_strings: tuple[str, ...]) -> None:
        """選択した規則が検出する文字列を個別のラベルで表示する。"""
        for row in self._rule_target_rows:
            self._rule_target_strings_layout.removeWidget(row)
            row.deleteLater()
        self._rule_target_labels.clear()
        self._rule_target_rows.clear()

        row_layout: QHBoxLayout | None = None
        row_width = 0
        for target_string in target_strings:
            label = QLabel(target_string, self)
            label.setObjectName("sourceCodeCheckTargetString")
            label.setFont(get_font(monospace=True, small=True))
            label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            label.setStyleSheet(
                "QLabel {"
                "color: white;"
                "background-color: #0033aa;"
                "border: 1px solid #00298a;"
                "border-radius: 4px;"
                "padding: 2px 5px;"
                "}"
            )
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label_width = label.sizeHint().width()
            required_width = label_width
            if row_layout is not None:
                required_width += self._TARGET_STRING_SPACING

            # 300pxを超える場合は次の行を作り、各行を左端から詰めて表示する。
            if row_layout is None or row_width + required_width > self._TARGET_STRINGS_ROW_MAX_WIDTH:
                row = QWidget(self)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(self._TARGET_STRING_SPACING)
                row_layout.addStretch(1)
                self._rule_target_strings_layout.addWidget(row)
                self._rule_target_rows.append(row)
                row_width = 0

            row_layout.insertWidget(row_layout.count() - 1, label)
            row_width += label_width
            if row_layout.count() > 2:
                row_width += self._TARGET_STRING_SPACING
            self._rule_target_labels.append(label)

    def _search_rules(self, query: str) -> None:
        """カタログの検索結果に含まれない規則行を非表示にする。"""
        matching_catalog = self._catalog.search(query)
        matching_ids = {
            SourceCodeCheckIdentifier(group.group_id, entry.check_id)
            for group in matching_catalog.groups
            for entry in group.entries
        }
        first_visible_row: int | None = None
        selected_row_is_visible = False
        current_row = self._rules_table.currentRow()
        for row, identifier in enumerate(self._rule_ids):
            is_visible = identifier in matching_ids
            self._rules_table.setRowHidden(row, not is_visible)
            if is_visible and first_visible_row is None:
                first_visible_row = row
            if is_visible and row == current_row:
                selected_row_is_visible = True

        if selected_row_is_visible:
            return
        self._rules_table.clearSelection()
        if first_visible_row is not None:
            self._rules_table.selectRow(first_visible_row)

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
