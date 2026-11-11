# 開発・コーディング規約

## 1. 規約の適用

- このリポジトリでコードを実装、修正、リファクタリングするときは、作業前にこのファイルを参照する。
- 新規コードはこの規約に従う。
- 既存コードを変更する場合も、作業範囲を不必要に広げない範囲でこの規約に従う。
- 規約適用のみを目的とした既存コードの一括修正は、明示的な指示がない限り行わない。

## 2. プロジェクト構成

- アプリケーションコードは `src/autoprogen/` 配下に置き、`autoprogen` 名前空間からimportする。
- アプリケーションの起動点には `src/autoprogen/__main__.py` を使用し、`python -m autoprogen` で起動できる状態を維持する。
- Pythonプロジェクトの設定、依存関係、開発用依存関係およびpytest設定は `pyproject.toml` で管理する。

### 2.1 バージョン管理

- 現在のアプリケーションバージョンは、`pyproject.toml`の`project.version`を唯一の正として管理する。
- `project.version`にはPEP 440形式を使用し、実行時は`importlib.metadata`からインストール済みパッケージのバージョンを取得する。
- alpha版とbeta版ではPEP 440のリリース番号を`0`とし、プレリリース番号を従来の表示上のパッチ番号として扱う。
- 対応する記述と画面表示は次のとおりとする。

| `pyproject.toml`の表記 | 画面表示 |
|---|---|
| `1.1.0b5` | `1.1-beta.5` |
| `1.2.0a3` | `1.2-alpha.3` |
| `1.2.4` | `1.2.4` |

- バージョン変更後はeditable installのメタデータ更新が必要になる。通常起動では`run.bat`が`pyproject.toml`との不一致を検出して自動更新する。
- パッケージメタデータを取得できない未インストールのソースツリーでは、開発用フォールバックとして`0.0.0`を使用する。

## 3. コーディング規約

### 3.1 Python構文・型ヒント

- `from __future__ import annotations` など、futureのannotationは使用しない。
- 型ヒントは最新のPython構文に準拠し、組み込みジェネリクスとPEP 604形式を優先する。
  - `typing.Union` は使わず、`A | B` を使う。
  - `typing.Optional` は使わず、`T | None` を使う。
  - `typing.List` は使わず、`list[T]` を使う。
  - `typing.Dict` は使わず、`dict[K, V]` を使う。

### 3.2 docstring

- クラスと関数には必ずdocstringを付ける。
- クラスのdocstringには、そのクラスの責務と用途を記述する。

### 3.3 フィールドとコメント

- dataclass、NamedTupleなどのモデルを構成する各フィールドには、役割が分かる日本語コメントを付ける。
- フィールドのコメントには、値の意味と、`None`や既定値が表す状態を必要に応じて記述する。
- コメントは必ず日本語で書く。
- 長い手続きには、処理ブロックごとに意図が分かる一行コメントを書く。
- 自明な処理を逐語的に説明するコメントは避ける。
- 必要に応じて、設計意図、前提、制約、なぜその処理が必要かをコメントに残す。

### 3.4 例外クラス

- 新しい例外クラスを `src/autoprogen/domain/error/__init__.py` に追加しない。
- 例外クラスは、その例外を送出するクラスの定義の直上に定義する。
- 対応するインターフェースがある場合は、実装クラスではなくインターフェースの定義の直上に定義する。

## 4. 開発環境とローカル設定

### 4.1 Pythonと仮想環境

- 開発および実行にはPython 3.11～3.14を使用する。
- このリポジトリでPython関連コマンドを実行するときは、リポジトリ直下の `.venv` を使用する。
- Python、pip、pytestなどは、原則として次の形式で実行する。

```powershell
.\.venv\Scripts\python.exe -m pip ...
.\.venv\Scripts\python.exe -m pytest ...
.\.venv\Scripts\python.exe -m autoprogen
```

- システムにインストールされた `python` や `pytest` を、開発作業で直接使用しない。

### 4.2 デバッグ用ローカル設定

- 開発者ごとのデバッグ用設定は、リポジトリ直下の `.autoprogen-dev.toml` に記述する。
- `.autoprogen-dev.toml` はGitの管理対象外とし、各開発者が自身の環境に合わせて作成する。
- アプリケーションの起動時には、`run-debug.bat` から起動した場合にだけこのファイルを読み込み、通常の `run.bat` からの起動には影響しない。
- ファイルが存在しない場合、アプリケーションの入力補助はすべて無効な既定値で起動する。
- Windowsパスは、バックスラッシュをそのまま記述できるTOMLのリテラル文字列で指定する。

```toml
compiler_tool_fullpath = 'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat'
report_archive_fullpath = 'C:\TestData\report.zip'
auto_generate_project_name = true
target_number = 4
```

各項目の用途は次のとおり。

- `compiler_tool_fullpath`: Visual Studio開発者ツールの起動スクリプトを、GlobalSettingsの初期値として使用する。`settings.json` に保存済みの設定がある場合は、保存済み設定を優先する。
- `report_archive_fullpath`: 新規プロジェクト画面の「提出データ」へ初期入力するZIPファイルの絶対パス。省略時は空欄にする。
- `auto_generate_project_name`: `true` の場合、新規プロジェクト画面へ `proj-<乱数>` 形式の名前を自動入力する。省略時は `false` とする。
- `target_number`: 新規プロジェクト画面へ初期入力する0以上99以下の設問番号。省略時は空欄にする。

なお、採点統合テストでは、アプリケーションの起動方法とは別に `.autoprogen-dev.toml` の `compiler_tool_fullpath` を読み込む。詳細は次節を参照する。

## 5. テスト運用

### 5.1 テストの配置とマーカー

- すべてのpytestテストは `tests/` 配下で管理する。
- 可視GUIを起動し、人の操作やデスクトップ環境を必要とするテストには `gui_visible` マーカーを付ける。
- offscreenで完結し、人の操作やデスクトップ環境を必要としないGUIテストには `gui_visible` マーカーを付けない。
- 実際のMSVCを使用する採点統合テストには `msvc_integration` マーカーを付ける。
- **ローカルの `pytest` は、マーカーによる除外を行わず、すべてのテストを実行する。** CIでの除外条件は「5.3 CI」を参照する。

### 5.2 ローカルでの実行

通常の全テスト実行には、次のコマンドを使用する。`gui_visible` と `msvc_integration` も実行対象に含まれるため、対応するGUI環境とMSVCが必要となる。

```powershell
.\.venv\Scripts\python.exe -m pytest
```

採点統合テストは `.autoprogen-dev.toml` の `compiler_tool_fullpath` を読み込む。全テストを実行する開発環境では、使用する `VsDevCmd.bat` の絶対パスを必ず設定する。

採点統合テストだけを実行し、詳細な進行状況を標準出力で確認する場合は、次のコマンドを使用する。

```powershell
.\.venv\Scripts\python.exe -m pytest -s tests/workflows/test_grading_smoke.py -m msvc_integration
```

可視GUIテストだけをWindowsのローカル環境で実行する場合は、次のコマンドを使用する。

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m pytest -m gui_visible
$env:QT_QPA_PLATFORM = $null
```

### 5.3 CI

- CIでは、可視GUI・デスクトップ環境を必要とする `gui_visible` と、ローカルのMSVC設定を必要とする `msvc_integration` を除外する。
- offscreenで完結するGUIテストはCIの実行対象に含める。
- CIのpytest実行条件は `.github/workflows/test-python.yml` で次のように明示する。

```powershell
.\.venv\Scripts\python.exe -m pytest -m "not gui_visible and not msvc_integration"
```

## 6. Git・GitHub運用

### 6.1 Git運用

- 明示的な指示がない限り、`git add`、stage解除、commitなど、Gitのindexや履歴を変更する操作を行わない。
- コミットメッセージを生成するときは、必ず対象の `git diff` を確認し、実際の差分内容に基づいて生成する。
- コミットメッセージは日本語の一行とし、`feat:`、`fix:`、`refactor:`、`docs:`、`test:`、`chore:` などのConventional Commits形式の接頭辞を付ける。

### 6.2 Issue・GitHub運用

- Issueの作成・整理・記述は `CONTRIBUTING.md` に従う。
- 開発課題の正はGitHub Issuesとし、READMEへ詳細なバックログを重複して記載しない。
- `gh`によるIssue、Pull Request、コメント、ラベル、リリースなどの書き込み操作は、ユーザーが「作成する」「編集する」「閉じる」などの実行を明示的に指示した場合にのみ行う。
- 検討、整理、調査、提案、または「追加したい」という表現だけを、GitHubへの書き込み許可として扱わない。
- GitHubへの書き込み指示がない場合は、一覧取得や内容確認などの読み取り操作に留める。
