# コーディング規約

## Python構文

- `from __future__ import annotations` など、futuresのannotationは使用しない。
- type hintは最新のPython構文に準拠する。
  - `typing.Union` は使わず、`A | B` を使う。
  - `typing.Optional` は使わず、`T | None` を使う。
  - `typing.List` は使わず、`list[T]` を使う。
  - `typing.Dict` は使わず、`dict[K, V]` を使う。
  - 同様に、組み込みジェネリクスとPEP 604形式を優先する。

## docstring

- 関数には必ずdocstringを付ける。

## コメント

- コメントは必ず日本語で書く。
- 長い手続きには、処理ブロックごとに意図が分かる一行コメントを書く。
- 自明な処理を逐語的に説明するコメントは避ける。
- コメントには必要に応じて、設計意図、前提、制約、なぜその処理が必要かを残す。

## プロジェクト構成

- アプリケーションコードは `src/autoprogen/` 配下に置き、`autoprogen` 名前空間からimportする。
- アプリケーションの起動点には `src/autoprogen/__main__.py` を使用し、`python -m autoprogen` で起動できる状態を維持する。
- Pythonプロジェクトの設定、依存関係、開発用依存関係およびpytest設定は `pyproject.toml` で管理する。
- READMEは自動生成されるため、説明を変更する場合は原則として `static/readme/README.md` を編集し、`main_generate_readme.py` で `README.md` を再生成する。

## 開発環境とコマンド実行

- このリポジトリでPython関連コマンドを実行するときは、リポジトリ直下の `.venv` を使用する。
- Python、pip、pytestなどは、原則として次の形式で実行する。

```powershell
.\.venv\Scripts\python.exe -m pip ...
.\.venv\Scripts\python.exe -m pytest ...
.\.venv\Scripts\python.exe -m autoprogen
```

- システムにインストールされた `python` や `pytest` を、開発作業で直接使用しない。

## Git運用

- 明示的な指示がない限り、`git add`、stage解除、commitなど、Gitのindexや履歴を変更する操作を行わない。
- コミットメッセージを生成するときは、必ず対象の `git diff` を確認し、実際の差分内容に基づいて生成する。
- コミットメッセージは日本語の一行とし、`feat:`、`fix:`、`refactor:`、`docs:`、`test:`、`chore:` などのConventional Commits形式の接頭辞を付ける。

## 規約の適用

- このリポジトリでコードを実装、修正、リファクタリングするときは、作業前にこのファイルを参照する。
- 新規コードはこの規約に従う。
- 既存コードを変更する場合も、作業範囲を不必要に広げない範囲でこの規約に従う。
- 規約適用のみを目的とした既存コードの一括修正は、明示的な指示がない限り行わない。
