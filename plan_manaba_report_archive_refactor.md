# ManabaReportArchiveIO Refactor Plan

## 目的

`infra/io/report_archive.py` の `ManabaReportArchiveIO` を廃止し、manaba提出ZIP・reportlist.xlsx・提出フォルダ検証・提出物展開の責務を明確に分離する。

現在の `ManabaReportArchiveIO` は次を同時に担当している。

- manaba提出ZIPを開く
- `reportlist.xlsx` を探す
- `reportlist.xlsx` の親フォルダを基準に提出フォルダを列挙する
- reportlist由来の提出フォルダ集合とarchive内の提出フォルダ集合を照合する
- 学生ごとの提出フォルダ内ファイルを列挙する
- 入れ子ZIPを1段だけ展開する
- ZIP破損や `reportlist.xlsx` 不在を `ManabaReportArchiveIOError` に変換する

また、`service/student_master_create.py` には `_StudentMasterExcelReader` があり、以下の責務を持っている。

- `openpyxl.Workbook` からワークシートを取り出す
- ワークシートが1つだけか検証する
- reportlistのテーブル開始行・終了行を検出する
- ヘッダー形式を検証する
- ロール、学籍番号、フォルダ列を検証する
- `pandas.DataFrame` を作る
- `Student` 生成に必要な情報を抽出する

このリファクタリングでは、これらを以下に分解する。

```text
ManabaReportArchiveGateway
  Path -> bytes -> ManabaReportArchive

ManabaReportArchive
  manaba提出ZIPの論理構造を遅延評価で読む

ReadonlyExcelWorksheetGateway
  Excel binary -> ReadonlyExcelWorksheet

ReadonlyExcelWorksheet
  openpyxlに依存しない読み取り専用の表

ManabaReportListParser
  ReadonlyExcelWorksheet -> ManabaReportList

ManabaReportList
  reportlist.xlsxから読み取った履修生行モデル

ManabaReportListArchiveValidateService
  ManabaReportList と ManabaReportArchive の提出フォルダ整合性を検証する
```

## 基本方針

- `from __future__ import annotations` は使わない。
- 基本機能クラスの抽象クラスは定義しない。
- `OpenpyxlReadonlyExcelWorksheetGateway` のような実装技術名つきクラスは作らない。
  - `ReadonlyExcelWorksheetGateway` という具象クラスの内部で `openpyxl` を使う。
- `ManabaReportArchiveGateway` は具象クラスとして定義する。
- `ManabaReportArchiveIO` は最終的に削除する。
- `ManabaReportArchiveIOError` は最終的に削除または非参照化し、用途別のエラーへ置換する。
- `ReadonlyExcelWorksheet` と `ManabaReportList` は内部行データをprivateに持つ普通のクラスにする。
- `ReadonlyExcelCell` は `NamedTuple` にする。
- `ReadonlyExcelWorksheet` に `iter_rows()` は定義しない。
- `ManabaReportList` に `iter_submitted_rows()` や `get_submission_folder_paths()` は定義しない。
- 利用側は `row_count()` と `get_row()` / `cell_at()` を使ってfor文で処理する。
- `ManabaReportArchive` はZIP全体のbytesを持ち、必要なときに遅延的にZIP内容を読む。
- 提出ファイル本体は `iter_submission_files()` を呼んだときに1ファイルずつbytesとして読む。
- 入れ子ZIPは現在と同じく1段だけ展開する。再帰展開にはしない。

## 最終的な責務分担

### `ManabaReportArchiveGateway`

責務:

- 指定された `archive_fullpath: Path` からbytesを読む。
- `ManabaReportArchive(archive_bytes=...)` を返す。

やらないこと:

- ZIP構造の検証。
- reportlist.xlsxの解析。
- 提出フォルダ集合の検証。
- 学生マスタ生成。

### `ManabaReportArchive`

責務:

- manaba提出ZIPのbytesを保持する。
- ZIP構造を必要なときに遅延的に読む。
- `reportlist.xlsx` の相対パスを取得する。
- `reportlist.xlsx` の親フォルダを取得する。
- `reportlist.xlsx` のbytesを返す。
- archive内の提出フォルダ集合を返す。
- 指定提出フォルダ内のファイルを列挙する。
- 入れ子ZIPを1段だけ展開して列挙する。

やらないこと:

- Excel binaryを解析する。
- manaba reportlistの形式検証をする。
- reportlist由来のexpected folder setとarchive内actual folder setを比較する。
- `Student` を生成する。

### `ReadonlyExcelWorksheetGateway`

責務:

- Excel binaryを `openpyxl` で読む。
- ワークシートが1つだけであることを検証する。
- セルの値を `ReadonlyExcelCell.text` に変換する。
- 空セルは必ず `""` に正規化する。
- セルのハイパーリンク先を `ReadonlyExcelCell.hyperlink_target` に変換する。
- `ReadonlyExcelWorksheet` を返す。

やらないこと:

- manaba reportlist形式の検証。
- ヘッダー検証。
- 学籍番号検証。
- 提出フォルダパス検証。

### `ReadonlyExcelWorksheet`

責務:

- 2次元セル表をprivateに保持する。
- `row_count()` を返す。
- `column_count()` を返す。
- `cell_at(row_index=..., column_index=...)` でセルを返す。

やらないこと:

- 行イテレータ提供。
- Excelファイル形式に関する処理。
- manaba形式に関する処理。

### `ManabaReportListParser`

責務:

- `ReadonlyExcelWorksheet` をmanabaの `reportlist.xlsx` として解釈する。
- テーブル開始行が8行目であることを検証する。
- `#end` 行が存在し、開始行より後にあることを検証する。
- ヘッダーが期待ラベルを含むことを検証する。
- ロールが既知のものだけであることを検証する。
- 履修生行だけを `ManabaReportListRow` に変換する。
- 学籍番号を `StudentID` として検証・保持する。
- フォルダ列の形式を検証する。
- 各履修生行が必ず次のどちらかに分類できることを検証する。
  - 提出済み・有効な提出フォルダあり
  - 未提出・提出フォルダなし

やらないこと:

- ZIP構造を読む。
- archive内に提出フォルダが実在するか検証する。
- `Student` をRepositoryへ保存する。

### `ManabaReportList`

責務:

- 履修生行をprivateに保持する。
- `row_count()` を返す。
- `get_row(row_index=...)` で行を返す。

やらないこと:

- 提出済み行の抽出メソッド提供。
- 提出フォルダ集合の抽出メソッド提供。
- Archiveとの整合性検証。

### `ManabaReportListArchiveValidateService`

責務:

- `ManabaReportList` と `ManabaReportArchive` を突き合わせる。
- reportlist上で提出済みの履修生が持つ提出フォルダ集合を作る。
- archive内に存在する提出フォルダ集合を取得する。
- 両者が完全一致することを検証する。

この検証により、以下を保証する。

- 提出済みの生徒は有効な提出フォルダを持つ。
- 提出済みの生徒の提出フォルダはarchive内にも存在する。
- 未提出の生徒は提出フォルダを持たない。
- archive内に、未提出者またはreportlistに存在しない提出フォルダがない。
- すべての履修生が提出済み・未提出のどちらかに分類済みである。

やらないこと:

- Excelの物理読み込み。
- reportlist形式の解析。
- 学生提出物の展開。

## 追加・変更するファイル

### 追加

```text
domain/model/readonly_excel_worksheet.py
domain/model/manaba_report_list.py
domain/model/manaba_report_archive.py
infra/gateway/manaba_report_archive.py
infra/gateway/readonly_excel_worksheet.py
service/manaba_report_list_parser.py
service/manaba_report_list_archive_validate.py
```

### 変更

```text
domain/error/__init__.py
service/student_master_create.py
service/student_submission.py
usecase/current_project.py
usecase/manaba_report_archive.py
application/container/app.py
application/container/project.py
tests/helpers/*
tests/workflows/test_project_initialize_from_archive.py
```

### 最終的に削除

```text
infra/io/report_archive.py
```

## 追加するモデル・機能クラスの骨格

### `domain/model/readonly_excel_worksheet.py`

```python
from typing import NamedTuple


class ReadonlyExcelCell(NamedTuple):
    text: str
    # セルの文字列表現。
    # 空セルは必ず "" に正規化する。
    # None は使わない。

    hyperlink_target: str | None
    # セルに設定されたハイパーリンクのリンク先文字列。
    # ハイパーリンクがない場合は None。
    # openpyxl の cell.hyperlink.target に相当する値を想定する。


class ReadonlyExcelWorksheet:
    _rows: tuple[tuple[ReadonlyExcelCell, ...], ...]
    # ワークシート全体のセルを行優先で保持する。
    # 外部から直接変更・参照させない。
    # index は 0-based。

    def __init__(
            self,
            *,
            rows: tuple[tuple[ReadonlyExcelCell, ...], ...],
    ) -> None:
        """読み取り専用ワークシートを生成する。"""
        ...

    def row_count(self) -> int:
        """ワークシートの行数を返す。"""
        ...

    def column_count(self) -> int:
        """ワークシート内の最大列数を返す。"""
        ...

    def cell_at(
            self,
            *,
            row_index: int,
            column_index: int,
    ) -> ReadonlyExcelCell:
        """指定した 0-based の行・列位置にあるセルを返す。"""
        ...
```

### `domain/model/manaba_report_list.py`

```python
from dataclasses import dataclass
from pathlib import PurePosixPath

from domain.model.value import StudentID


@dataclass(frozen=True)
class ManabaSubmissionFolderPath:
    value: PurePosixPath
    # reportlist.xlsx の「フォルダ」列のハイパーリンクから得られる提出フォルダパス。
    # reportlist.xlsx の親フォルダから見た相対パスとして扱う。
    # ZIP内部のパスなので PurePosixPath を使う。


@dataclass(frozen=True)
class ManabaReportListRow:
    row_index: int
    # ReadonlyExcelWorksheet 上の 0-based 行番号。
    # エラー表示やデバッグ用に保持する。

    student_id: StudentID
    # 学籍番号。
    # ManabaReportList には履修生行だけを格納する。

    name: str
    # 氏名。

    name_en: str
    # 氏名（英語）。

    email_address: str
    # メールアドレス。

    is_submitted: bool
    # reportlist.xlsx 上で提出済みとして扱うかどうか。
    # True の場合、submission_folder_path は必ず None ではない。
    # False の場合、submission_folder_path は必ず None。

    submitted_at_text: str
    # 提出日時列の文字列表現。
    # 未提出の場合は ""。

    num_submissions_text: str
    # 提出回数列の文字列表現。
    # 未提出の場合は ""。

    submission_folder_path: ManabaSubmissionFolderPath | None
    # 提出フォルダへの相対パス。
    # is_submitted が True の場合は必ず ManabaSubmissionFolderPath。
    # is_submitted が False の場合は必ず None。


class ManabaReportList:
    _rows: tuple[ManabaReportListRow, ...]
    # reportlist.xlsx から読み取った履修生行の一覧。
    # 担当教員・授業補助者の行は含めない。
    # 外部から直接参照させない。

    def __init__(
            self,
            *,
            rows: tuple[ManabaReportListRow, ...],
    ) -> None:
        """manaba reportlist の履修生行一覧を保持するモデルを生成する。"""
        ...

    def row_count(self) -> int:
        """履修生行の数を返す。"""
        ...

    def get_row(
            self,
            *,
            row_index: int,
    ) -> ManabaReportListRow:
        """指定した 0-based index の履修生行を返す。"""
        ...
```

### `domain/model/manaba_report_archive.py`

```python
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterator

from domain.model.manaba_report_list import ManabaSubmissionFolderPath


@dataclass(frozen=True)
class ManabaSubmissionFile:
    relative_path: PurePosixPath
    # 学生提出フォルダから見た相対ファイルパス。
    # 入れ子ZIP内のファイルの場合は、ZIPファイル名を仮想フォルダとして含める。
    # 例: submit.zip/prog01.c

    content_bytes: bytes
    # ファイル本体のbytes。
    # ManabaReportArchive.iter_submission_files() で列挙された時点で読み込む。


class ManabaReportArchive:
    _MASTER_EXCEL_FILENAME: str
    # manaba提出ZIP内のマスターExcelファイル名。
    # 値は "reportlist.xlsx"。

    _archive_bytes: bytes
    # manabaからダウンロードした提出ZIP全体のbytes。
    # reportlist.xlsx、提出フォルダ一覧、提出ファイル内容はこのbytesから遅延的に読む。

    _report_list_excel_path_cache: PurePosixPath | None
    # reportlist.xlsx のZIP内相対パスのキャッシュ。
    # 未解決の場合は None。

    _report_list_base_folder_path_cache: PurePosixPath | None
    # reportlist.xlsx の親フォルダパスのキャッシュ。
    # 未解決の場合は None。

    def __init__(
            self,
            *,
            archive_bytes: bytes,
    ) -> None:
        """manaba提出ZIPのbytesから、遅延読み込み可能なアーカイブモデルを生成する。"""
        ...

    def get_report_list_excel_path(self) -> PurePosixPath:
        """アーカイブ内の reportlist.xlsx の相対パスを返す。存在しない場合はエラーにする。"""
        ...

    def get_report_list_base_folder_path(self) -> PurePosixPath:
        """reportlist.xlsx が存在する親フォルダの相対パスを返す。"""
        ...

    def read_report_list_excel_bytes(self) -> bytes:
        """アーカイブ内の reportlist.xlsx をbytesとして読み込んで返す。"""
        ...

    def list_submission_folder_paths(self) -> frozenset[ManabaSubmissionFolderPath]:
        """reportlist.xlsx の親フォルダ配下にある提出フォルダパス集合を返す。"""
        ...

    def iter_submission_files(
            self,
            *,
            submission_folder_path: ManabaSubmissionFolderPath,
    ) -> Iterator[ManabaSubmissionFile]:
        """指定した提出フォルダ内のファイルを順に返す。入れ子ZIPがある場合は1段展開して返す。"""
        ...
```

### `infra/gateway/manaba_report_archive.py`

```python
from pathlib import Path

from domain.model.manaba_report_archive import ManabaReportArchive


class ManabaReportArchiveGateway:
    def read(
            self,
            *,
            archive_fullpath: Path,
    ) -> ManabaReportArchive:
        """manaba提出ZIPファイルを読み込み、ManabaReportArchive を返す。"""
        ...
```

### `infra/gateway/readonly_excel_worksheet.py`

```python
from domain.model.readonly_excel_worksheet import ReadonlyExcelWorksheet


class ReadonlyExcelWorksheetGateway:
    def read(
            self,
            *,
            excel_bytes: bytes,
    ) -> ReadonlyExcelWorksheet:
        """Excel binaryを読み込み、openpyxl依存を含まない ReadonlyExcelWorksheet に変換する。"""
        ...
```

### `service/manaba_report_list_parser.py`

```python
from domain.model.manaba_report_list import ManabaReportList, ManabaSubmissionFolderPath
from domain.model.readonly_excel_worksheet import ReadonlyExcelCell, ReadonlyExcelWorksheet


class ManabaReportListParser:
    EXPECTED_HEADER_JP_CONTAINS: tuple[str, ...] = (
        "内部コースID",
        "コース名",
        "リンク情報",
        "ロール",
        "ユーザID",
        "学籍番号",
        "氏名",
        "氏名（英語）",
        "メールアドレス",
        "合計点",
        "評価",
        "講評",
        "提出",
        "提出日時",
        "提出回数",
        "フォルダ",
    )
    # manaba reportlist.xlsx のヘッダーに含まれているべき日本語ラベル。

    def parse(
            self,
            *,
            worksheet: ReadonlyExcelWorksheet,
    ) -> ManabaReportList:
        """ReadonlyExcelWorksheet を manaba reportlist として解釈し、ManabaReportList を返す。"""
        ...

    def _parse_submission_folder_path(
            self,
            *,
            folder_cell: ReadonlyExcelCell,
    ) -> ManabaSubmissionFolderPath | None:
        """フォルダ列のセルから提出フォルダパスを読み取る。未提出の場合は None を返す。"""
        ...

    def _validate_submission_status(
            self,
            *,
            is_submitted: bool,
            submission_folder_path: ManabaSubmissionFolderPath | None,
            row_index: int,
    ) -> None:
        """提出済みなら提出フォルダあり、未提出なら提出フォルダなし、という行内整合性を検証する。"""
        ...
```

### `service/manaba_report_list_archive_validate.py`

```python
from domain.model.manaba_report_archive import ManabaReportArchive
from domain.model.manaba_report_list import ManabaReportList, ManabaSubmissionFolderPath


class ManabaReportListArchiveValidateService:
    def execute(
            self,
            *,
            report_list: ManabaReportList,
            archive: ManabaReportArchive,
    ) -> None:
        """reportlist上で提出済みの履修生の提出フォルダがarchive内に過不足なく存在することを検証する。"""
        ...

    def _collect_expected_submission_folder_paths(
            self,
            *,
            report_list: ManabaReportList,
    ) -> frozenset[ManabaSubmissionFolderPath]:
        """reportlist上で提出済みの履修生が持つ提出フォルダパス集合を返す。"""
        ...

    def _validate_folder_path_sets(
            self,
            *,
            expected_folder_paths: frozenset[ManabaSubmissionFolderPath],
            actual_folder_paths: frozenset[ManabaSubmissionFolderPath],
    ) -> None:
        """期待される提出フォルダ集合と実際の提出フォルダ集合が一致することを検証する。"""
        ...
```

## エラー設計

`domain/error/__init__.py` に以下を追加する。

```python
class ManabaReportArchiveError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class ReadonlyExcelWorksheetGatewayError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class ManabaReportListParserError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason


class ManabaReportListArchiveValidateServiceError(RuntimeError):
    def __init__(self, *, reason: str):
        self.reason = reason
```

最終的に `ManabaReportArchiveIOError` は削除または参照ゼロにする。

ただし、移行途中で既存Serviceのエラー変換を維持する必要がある場合は、短期的に残してもよい。

## validationの置き場所

### `ManabaReportArchiveGateway`

実施するvalidation:

- `archive_fullpath` からbytesを読めること。

実施しないvalidation:

- ZIPとして妥当か。
- `reportlist.xlsx` が存在するか。
- 提出フォルダ集合が正しいか。

### `ManabaReportArchive`

実施するvalidation:

- ZIPとして読めること。
- `reportlist.xlsx` がarchive内に存在すること。
- `reportlist.xlsx` がファイルであること。
- `reportlist.xlsx` の親フォルダを決定できること。
- archive内の提出フォルダ集合を決定できること。
- 指定提出フォルダの中身を読めること。
- 入れ子ZIPがある場合、それがZIPとして読めること。

実施しないvalidation:

- Excel workbookとして妥当か。
- reportlistのヘッダーが正しいか。
- 提出済み・未提出の行内整合性。
- reportlist由来の提出フォルダ集合とarchive内提出フォルダ集合の一致。

### `ReadonlyExcelWorksheetGateway`

実施するvalidation:

- Excel binaryをopenpyxlで開けること。
- workbook内のworksheetが1つだけであること。

実施しないvalidation:

- manaba reportlist形式かどうか。

### `ManabaReportListParser`

実施するvalidation:

- テーブル開始行が8行目であること。
- テーブル終了行 `#end` が存在すること。
- テーブル終了行が開始行より後にあること。
- ヘッダーが期待ラベルを含むこと。
- ロールが `履修生` / `担当教員` / `授業補助者...` のいずれかであること。
- 履修生の学籍番号が `StudentID` として有効であること。
- フォルダ列が未提出形式または提出済み形式のどちらかであること。
- 提出済み行は有効な提出フォルダを持つこと。
- 未提出行は提出フォルダを持たないこと。
- すべての履修生行が提出済み・未提出のどちらか一方に分類できること。

提出状態の判定方針:

```text
folder_cell.hyperlink_target is not None
  -> 提出済み

folder_cell.text == "" and folder_cell.hyperlink_target is None
  -> 未提出

その他
  -> 不正形式
```

既存実装互換として、提出済みの場合は `folder_cell.text == "開く"` を期待してよい。
ただし、manabaの表示文字列揺れを避けたい場合は、提出済み判定の主根拠は `hyperlink_target` にする。

フォルダパス検証方針:

```text
hyperlink_target が None
  -> 未提出として None

hyperlink_target が str かつ末尾が "\\"
  -> 末尾 "\\" を除去
  -> "\\" を "/" に正規化
  -> PurePosixPath に変換
  -> ManabaSubmissionFolderPath にする

hyperlink_target が str だが末尾が "\\" でない
  -> エラー
```

### `ManabaReportListArchiveValidateService`

実施するvalidation:

- reportlist上で提出済みの履修生の提出フォルダ集合をexpectedとして作る。
- archive内の提出フォルダ集合をactualとして取得する。
- `expected == actual` を検証する。

エラー条件:

- `expected - actual` が非空。
  - reportlist上で提出済みなのにarchive内に提出フォルダがない。
- `actual - expected` が非空。
  - archive内に存在しないはずの提出フォルダがある。

このvalidationにより、未提出の生徒の提出フォルダがarchive内に存在しないことも保証される。

### `StudentMasterCreateService`

実施するvalidation:

- 原則として、新しい構造では独自validationを持たない。
- `ManabaReportListParser` の結果を信用して `Student` を作る。
- `submitted_at_text` と `num_submissions_text` の変換で失敗した場合だけ `StudentMasterServiceError` に変換する。

### `StudentSubmissionExtractService`

実施するvalidation:

- `student_repo.exists_any()` が真であること。
- `ManabaReportListArchiveValidateService` が通過済みであることを前提にしてもよい。
- 防御的にService内で再度validate serviceを呼んでもよい。

推奨:

- 初期化UseCase内で、学生マスタ作成前または直後に1回だけ `ManabaReportListArchiveValidateService` を呼ぶ。
- `StudentSubmissionExtractService` は提出物展開に集中する。

## 新しい初期化フロー

現在:

```text
ProjectContainer.create_current_project_initialize_static_usecase(path)
  -> ManabaReportArchiveIO(path) を生成
  -> StudentMasterCreateService(manaba_report_archive_io)
  -> StudentSubmissionExtractService(manaba_report_archive_io)
```

変更後:

```text
ProjectContainer.current_project_initialize_static_usecase
  -> Gateway / Parser / ValidateService / Student services をDI済みにする

CurrentProjectInitializeStaticUseCase.execute(manaba_report_archive_fullpath=path, progress_callback=...)
  -> archive = ManabaReportArchiveGateway.read(path)
  -> excel_bytes = archive.read_report_list_excel_bytes()
  -> worksheet = ReadonlyExcelWorksheetGateway.read(excel_bytes)
  -> report_list = ManabaReportListParser.parse(worksheet)
  -> ManabaReportListArchiveValidateService.execute(report_list, archive)
  -> StudentMasterCreateService.execute(report_list)
  -> StudentSubmissionExtractService.execute(report_list, archive)
  -> CurrentProjectSetInitializedService.execute()
```

ただし、既存UIとの接続を小さくするため、最初は `ProjectContainer.create_current_project_initialize_static_usecase(manaba_report_archive_fullpath=...)` を残し、その内部で新方式のUseCaseを返してもよい。

最終形では、archive pathはDI対象ではなく、`CurrentProjectInitializeStaticUseCase.execute(...)` の実行時引数にする。

## Serviceの変更方針

### `StudentMasterCreateService`

変更前:

```text
StudentMasterCreateService
  - ManabaReportArchiveIO に依存
  - open_master_excel() を呼ぶ
  - openpyxl.open() を呼ぶ
  - _StudentMasterExcelReader でDataFrame化
  - DataFrameからStudentを生成
```

変更後:

```text
StudentMasterCreateService
  - ManabaReportList に依存してexecuteする
  - openpyxlを知らない
  - pandasを使わない
  - ManabaReportArchiveを知らない
```

新しいメソッド形:

```python
def execute(self, *, report_list: ManabaReportList) -> None:
    ...
```

処理:

- 既にstudent_repoに学生が存在する場合はreturn。
- `range(report_list.row_count())` でループする。
- `report_list.get_row(row_index=i)` を取得する。
- `row.is_submitted` に基づいて `submitted_at` / `num_submissions` / `submission_folder_name` を作る。
- `Student` を作る。
- `student_repo.create_all(students)` を呼ぶ。

### `StudentSubmissionExtractService`

変更前:

```text
StudentSubmissionExtractService
  - ManabaReportArchiveIO に依存
  - student_repoから student_id -> submission_folder_name を作る
  - validate_master_excel_exists()
  - validate_archive_contents(...)
  - iter_student_submission_archive_contents(...) で展開
```

変更後:

```text
StudentSubmissionExtractService
  - ManabaReportArchive に依存してexecuteする
  - ManabaReportListArchiveValidateServiceは基本的にUseCase側で実行済み
  - student_repoから提出済み学生を取得する
  - 各学生の submission_folder_name から ManabaSubmissionFolderPath を作る
  - archive.iter_submission_files(...) で展開する
```

新しいメソッド形:

```python
def execute(self, *, archive: ManabaReportArchive) -> None:
    ...
```

または、reportlistから直接展開したいなら以下でもよい。

```python
def execute(self, *, report_list: ManabaReportList, archive: ManabaReportArchive) -> None:
    ...
```

推奨は前者。
理由は、学生マスタ作成後は `StudentRepository` が正であり、既存の設計にも合うため。

ただし、`ManabaSubmissionFolderPath` を作るために、`student.submission_folder_name` が現在 `str | None` である点に注意する。
既存DBとの互換性を優先し、`Student.submission_folder_name` は当面 `str | None` のままでよい。

## 実装手順

### Phase 1: モデルとエラーを追加する

1. `domain/model/readonly_excel_worksheet.py` を追加する。
   - `ReadonlyExcelCell`
   - `ReadonlyExcelWorksheet`
2. `domain/model/manaba_report_list.py` を追加する。
   - `ManabaSubmissionFolderPath`
   - `ManabaReportListRow`
   - `ManabaReportList`
3. `domain/model/manaba_report_archive.py` を追加する。
   - `ManabaSubmissionFile`
   - `ManabaReportArchive`
4. `domain/error/__init__.py` に新エラーを追加する。
   - `ManabaReportArchiveError`
   - `ReadonlyExcelWorksheetGatewayError`
   - `ManabaReportListParserError`
   - `ManabaReportListArchiveValidateServiceError`

このPhaseでは既存コードからはまだ参照しない。

### Phase 2: GatewayとParserを追加する

1. `infra/gateway/manaba_report_archive.py` を追加する。
   - `ManabaReportArchiveGateway.read(...)`
2. `infra/gateway/readonly_excel_worksheet.py` を追加する。
   - `ReadonlyExcelWorksheetGateway.read(...)`
3. `service/manaba_report_list_parser.py` を追加する。
   - `_StudentMasterExcelReader` のロジックを移植する。
   - pandas DataFrameは使わない。
   - openpyxlは使わない。
4. `service/manaba_report_list_archive_validate.py` を追加する。

このPhaseでは、まだ既存の初期化フローは変更しない。
単体テストを先に書けるならここで書く。

### Phase 3: `usecase/manaba_report_archive.py` を新Gatewayに置換する

現在の `ManabaReportArchiveValidateMasterExcelExistsUseCase` は `ManabaReportArchiveIO` を直接生成している。

変更後:

- `ManabaReportArchiveGateway` をDIする。
- `execute(manaba_report_archive_fullpath: Path) -> bool` の中で以下を行う。
  - `archive = gateway.read(archive_fullpath=...)`
  - `archive.get_report_list_excel_path()` または `archive.read_report_list_excel_bytes()` を呼ぶ。
  - 成功したらTrue。
  - `ManabaReportArchiveError` ならFalse。

`application/container/app.py` で `ManabaReportArchiveGateway` を生成し、UseCaseに注入する。

### Phase 4: `CurrentProjectInitializeStaticUseCase` を新フローに寄せる

最初は破壊的変更を避けるため、以下のどちらかで進める。

#### 案A: UseCaseにpathを渡す最終形へ一気に寄せる

`CurrentProjectInitializeStaticUseCase.execute(...)` を以下に変更する。

```python
def execute(
        self,
        *,
        manaba_report_archive_fullpath: Path,
        progress_callback: ProgressCallback | None = None,
) -> ProjectInitializeResult:
    ...
```

`ProjectContainer.create_current_project_initialize_static_usecase(...)` は廃止し、`current_project_initialize_static_usecase` のcached propertyにする。

#### 案B: 既存の呼び出し形を一時的に維持する

`ProjectContainer.create_current_project_initialize_static_usecase(manaba_report_archive_fullpath=...)` を残す。
ただし、その中で `ManabaReportArchiveIO` は生成しない。
`CurrentProjectInitializeStaticUseCase` に `manaba_report_archive_fullpath` を渡す一時フィールドを持たせる。

推奨は案A。
理由は、archive pathはDI対象ではなく、実行時入力だから。

### Phase 5: `StudentMasterCreateService` を `ManabaReportList` 入力に変更する

1. `service/student_master_create.py` から `_StudentMasterExcelReader` を削除する。
2. `openpyxl` importを削除する。
3. `pandas` importを削除する。
4. `ManabaReportArchiveIO` importを削除する。
5. `StudentMasterCreateService.__init__` から `manaba_report_archive_io` を削除する。
6. `execute(self, *, report_list: ManabaReportList) -> None` に変更する。
7. `ManabaReportListRow` から `Student` を作る。
8. 日付変換と提出回数変換の例外を `StudentMasterServiceError` に変換する。

注意:

- `row.is_submitted == False` の場合は、既存挙動と同じく `submitted_at=None`, `num_submissions=0`, `submission_folder_name=None`。
- `row.is_submitted == True` の場合は、`dateutil.parser.parse(row.submitted_at_text)` と `int(row.num_submissions_text)` を使う。
- `submission_folder_name` は当面 `str(row.submission_folder_path.value)` を保存する。

### Phase 6: `StudentSubmissionExtractService` を `ManabaReportArchive` 入力に変更する

1. `service/student_submission.py` から `ManabaReportArchiveIO` importを削除する。
2. `ManabaReportArchiveIOError` importを削除する。
3. `StudentSubmissionExtractService.__init__` から `manaba_report_archive_io` を削除する。
4. `execute(self, *, archive: ManabaReportArchive) -> None` に変更する。
5. `validate_master_excel_exists()` と `validate_archive_contents(...)` 呼び出しを削除する。
6. 提出済み学生ごとに `ManabaSubmissionFolderPath(PurePosixPath(student.submission_folder_name))` を作る。
7. `archive.iter_submission_files(submission_folder_path=...)` を呼ぶ。
8. `ManabaSubmissionFile.relative_path` と `content_bytes` を使ってファイルを展開する。
9. `ManabaReportArchiveError` を捕捉して `StudentSubmissionServiceError` に変換する。

既存のパスstrip処理は維持する。

```python
content_relative_path = PurePosixPath(
    *map(str.strip, content_relative_path.parts)
)
```

パストラバーサル防止の `assert dst_file_fullpath.parent.is_relative_to(extract_base_folder_fullpath)` も維持する。

### Phase 7: `CurrentProjectInitializeStaticUseCase` で統合する

`execute(...)` 内で以下を順に実行する。

1. progress: `"提出アーカイブを読み込んでいます"`
2. `archive = ManabaReportArchiveGateway.read(...)`
3. `excel_bytes = archive.read_report_list_excel_bytes()`
4. progress: `"生徒マスタExcelを読み込んでいます"`
5. `worksheet = ReadonlyExcelWorksheetGateway.read(excel_bytes=excel_bytes)`
6. `report_list = ManabaReportListParser.parse(worksheet=worksheet)`
7. `ManabaReportListArchiveValidateService.execute(report_list=report_list, archive=archive)`
8. progress: `"生徒マスタを生成しています"`
9. `StudentMasterCreateService.execute(report_list=report_list)`
10. progress: `"生徒の提出ファイルを展開しています"`
11. `StudentSubmissionExtractService.execute(archive=archive)`
12. progress: `"初期化を完了しています"`
13. `CurrentProjectSetInitializedService.execute()`
14. success resultを返す。

エラー変換:

- `ManabaReportArchiveError`
- `ReadonlyExcelWorksheetGatewayError`
- `ManabaReportListParserError`
- `ManabaReportListArchiveValidateServiceError`
- `StudentMasterServiceError`
- `StudentSubmissionServiceError`

これらを `ProjectInitializeResult.create_error(message=...)` に変換する。

### Phase 8: Container配線を更新する

`application/container/app.py`:

- `manaba_report_archive_gateway` を追加する。
- `manaba_report_archive_validate_master_excel_exists_usecase` にgatewayを注入する。

`application/container/project.py`:

- `ManabaReportArchiveIO` importを削除する。
- `StudentMasterCreateService` 生成時に `manaba_report_archive_io` を渡さない。
- `StudentSubmissionExtractService` 生成時に `manaba_report_archive_io` を渡さない。
- `ReadonlyExcelWorksheetGateway` を追加する。
- `ManabaReportListParser` を追加する。
- `ManabaReportListArchiveValidateService` を追加する。
- `CurrentProjectInitializeStaticUseCase` に必要依存を注入する。

### Phase 9: `ManabaReportArchiveIO` を削除する

以下の参照がゼロになったことを確認する。

```bash
grep -R "ManabaReportArchiveIO" -n .
grep -R "ManabaReportArchiveIOError" -n .
```

参照ゼロになったら削除する。

```text
infra/io/report_archive.py
```

### Phase 10: テストを追加・更新する

#### 追加したい単体テスト

1. `ReadonlyExcelWorksheetGateway`
   - 空セルが `""` になる。
   - ハイパーリンクなしが `None` になる。
   - ハイパーリンクありのtargetが取得される。
   - ワークシートが複数ある場合エラー。

2. `ManabaReportListParser`
   - 正常なreportlistを `ManabaReportList` に変換できる。
   - 履修生だけがrowsに入る。
   - 担当教員・授業補助者は除外される。
   - テーブル開始行が8行目でなければエラー。
   - `#end` がなければエラー。
   - ヘッダーが違えばエラー。
   - 不明ロールがあればエラー。
   - 不正学籍番号があればエラー。
   - 提出済みなのにフォルダリンクなしならエラー。
   - 未提出なのにフォルダリンクありならエラー。
   - フォルダリンク末尾が `\` でなければエラー。

3. `ManabaReportArchive`
   - `reportlist.xlsx` を検出できる。
   - `reportlist.xlsx` がないとエラー。
   - 提出フォルダ集合を列挙できる。
   - 指定提出フォルダ内の通常ファイルを列挙できる。
   - 入れ子ZIPを1段だけ展開できる。
   - 壊れたZIPでエラー。
   - 壊れた入れ子ZIPでエラー。

4. `ManabaReportListArchiveValidateService`
   - expectedとactualが一致すれば成功。
   - expectedにだけあるフォルダがあればエラー。
   - actualにだけあるフォルダがあればエラー。
   - 未提出者に対応する余計なarchiveフォルダがある場合エラー。

#### 更新するワークフローテスト

`tests/workflows/test_project_initialize_from_archive.py` を新構造で通す。

確認項目:

- student repositoryに架空学生が正しく作成される。
- 提出済み学生は `is_submitted == True`。
- 未提出学生は `is_submitted == False`。
- 提出済み学生の提出ファイルが `static/reports/<student_id>` に展開される。
- 入れ子ZIP内のファイルも既存挙動と同じ相対パスで展開される。
- 未提出学生の提出フォルダは作られない、または既存仕様どおり扱われる。

### Phase 11: import整理と不要依存削除

削除対象:

- `service/student_master_create.py` の `openpyxl` import
- `service/student_master_create.py` の `pandas` import
- `service/student_master_create.py` の `re` import。ただしStudentID側へ完全移行した場合。
- `infra/io/report_archive.py`
- `ManabaReportArchiveIOError`

注意:

- `requirements.txt` から `pandas` を削除できるかは別途確認する。
- 他箇所でpandasを使っていなければ削除候補。
- `openpyxl` はExcel出力でも使っているため削除しない。

## 実装時の注意点

### Pathの正規化

ZIP内部のパスは `PurePosixPath` を使う。

ただし、Excel hyperlink target はWindows風の `\` を含む可能性がある。
Parserで以下のように正規化する。

```text
"folder_name\\"
  -> "folder_name"
  -> PurePosixPath("folder_name")

"some\\nested\\folder\\"
  -> "some/nested/folder"
  -> PurePosixPath("some/nested/folder")
```

既存のmanaba archiveでは提出フォルダ名だけである可能性が高いが、ネストしていても扱えるようにしておく。

### 入れ子ZIP内パス

既存挙動を維持する。

```text
提出フォルダ/
  submit.zip
    prog01.c

-> relative_path = submit.zip/prog01.c
```

つまり、ZIPファイル名を仮想フォルダとして扱う。

### bytes遅延読み込み

`ManabaReportArchive` はarchive全体のbytesだけを保持する。
各メソッド内で `io.BytesIO(self._archive_bytes)` から `zipfile.ZipFile` を作る。

提出ファイル本体は `iter_submission_files()` 呼び出し時に読む。
ただし `ManabaSubmissionFile` としてyieldする時点では `content_bytes` を持つ。

### private rows

`ReadonlyExcelWorksheet` と `ManabaReportList` はprivateにtupleを持つ。
外部にtupleを直接返さない。

### 既存DB互換

`Student.submission_folder_name` は当面 `str | None` のまま維持する。
`ManabaSubmissionFolderPath` は新しい読み込み・検証・展開側の値オブジェクトとして使う。

### pandas廃止

`_StudentMasterExcelReader` 由来のDataFrame処理は廃止する。
`ManabaReportListParser` は `ReadonlyExcelWorksheet.cell_at(...)` を使って直接行を読む。

## 完了条件

- `grep -R "ManabaReportArchiveIO" -n .` で参照がない。
- `grep -R "ManabaReportArchiveIOError" -n .` で参照がない。
- `infra/io/report_archive.py` が削除されている。
- `StudentMasterCreateService` が `openpyxl` / `pandas` / `ManabaReportArchive` / `ManabaReportArchiveGateway` を知らない。
- `StudentSubmissionExtractService` が `ManabaReportArchiveIO` を知らない。
- `CurrentProjectInitializeStaticUseCase` が新しい初期化フローを統括している。
- reportlist上の提出済み/未提出状態とarchive内提出フォルダ集合のvalidationが入っている。
- 既存のアーカイブ初期化ワークフローテストが通る。
- 新規単体テストでExcel中間表現、reportlist parser、archive model、archive validate serviceの主要異常系を確認できる。

