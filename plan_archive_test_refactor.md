# Archive Workflow Test Refactor Plan

## 目的

- `AppContainer` に `AppPathConfig` の constructor injection を導入する。
- 既定値を `AppPathConfig.production()` にして本番挙動を維持する。
- テストは `AppContainer(app_path_config=AppPathConfig.testing(test_root))` に統一する。
- `mock` / `monkeypatch` / `property override` を使わず、`AppContainer` / `ProjectContainer` 経由の workflow test を構築する。

## 現在の前提

- 既存テストはコメントアウトのまま維持する（後で復活予定）。
- `tests/conftest.py` は廃止済みで、`tests/conftest_legacy.py` に退避済み。
- アーカイブは `tests/testdata/archives/` 配下に配置済み。
- 初手の workflow test は archive 初期化（`report-test-1.zip`）を対象とする。

## 目標構成

```text
tests/
  conftest.py
  conftest_legacy.py

  helpers/
    __init__.py
    archive_expected.py
    archive_assertions.py

  workflows/
    test_project_initialize_from_archive.py

  testdata/
    archives/
      report-test-1.zip
```

## フェーズ別実装手順

### フェーズA: AppContainer の DI 対応

対象:
- `application/container/app.py`

作業:
1. `AppContainer.__init__(self, *, app_path_config: AppPathConfig | None = None)` を追加する。
2. `self._app_path_config = app_path_config or AppPathConfig.production()` を保持する。
3. `app_path_config` プロパティは `self._app_path_config` を返す。
4. 既存の `AppContainer()` 呼び出し（`main.py`）は変更しない。

完了条件:
- `AppContainer()` の挙動が本番で変わらない。
- テストで `AppContainer(app_path_config=AppPathConfig.testing(...))` が利用できる。

### フェーズB: conftest の再構築

対象:
- `tests/conftest.py`（新規）

作業:
1. `test_root` fixture（session）を作成。
2. `app_path_config` fixture（session）で `AppPathConfig.testing(test_root)` を返す。
3. `_copy_required_app_resources` で最小リソースを `test_root/global` にコピー。
4. `prepared_app_path_config` fixture（session）で copy 済み config を返す。
5. `app_container` fixture を `AppContainer(app_path_config=prepared_app_path_config)` で作成。
6. `archive_path` fixture を archive 名指定の path resolver として実装。
7. `create_project` fixture を project 作成 factory として実装。
8. `open_project_container` fixture を open + `ProjectContainer` 生成 factory として実装。
9. `run_project_initialize_from_archive` fixture を実行専用 factory として実装。
10. `initialized_project_from_archive` fixture を成功系 factory として実装。

補足:
- `ProjectInitializeRun` dataclass を `conftest.py` に定義する。
- `conftest_legacy.py` には手を入れない。

完了条件:
- test root 以外（本番ディレクトリや repo root）へ書き込まない。
- workflow 実行に必要な最低限の app resource が揃う。

### フェーズC: helper の分離

対象:
- `tests/helpers/archive_expected.py`
- `tests/helpers/archive_assertions.py`
- `tests/helpers/__init__.py`

作業:
1. `ExpectedStudent` を定義。
2. `ExpectedArchiveStudentMaster` を定義。
3. `REPORT_TEST_1_EXPECTED_MASTER` を定義。
4. `assert_project_initialized` を実装。
5. `assert_student_master_matches` を実装。
6. `assert_submission_folders_match` を実装。
7. `assert_archive_initialization_matches` を実装。

完了条件:
- 期待値定義と assertion ロジックが `conftest.py` から分離される。

### フェーズD: workflow テスト作成

対象:
- `tests/workflows/test_project_initialize_from_archive.py`

作業:
1. 初期化成功系テスト 1 本を作成。
2. `initialized_project_from_archive(...)` を使って `ProjectContainer` を取得。
3. `assert_archive_initialization_matches(...)` で検証。

完了条件:
- テスト本体が短く、workflow 検証が helper に集約される。

### フェーズE: 実行確認と安定化

作業:
1. workflow テスト単体で実行確認。
2. 必要に応じて fixture の一意名生成や path 解決を調整。

完了条件:
- 初期化 workflow が安定して再現可能。

## archive 名指定での拡張設計

将来複数 archive 追加を想定し、以下を関数化する。

1. アーカイブ取得:
   - `archive_path(name: str) -> Path`
2. 期待値取得:
   - `get_expected_master(name: str) -> ExpectedArchiveStudentMaster`

推奨実装:
- `archive_expected.py` に registry を置く。
- 未知の name は明示的な `AssertionError` で失敗させる。

## 検証観点

1. `CurrentProjectRepository.get().is_initialized` が `True`。
2. `StudentRepository.list()` の student_id 集合が expected と一致。
3. expected 各学生を `StudentRepository.get()` で再取得可能。
4. 各フィールド（`student_id`, `name`, `name_en`, `email_address`, `submitted_at`, `num_submissions`, `submission_folder_name`）が一致。
5. 非学生ID（除外対象）が repository に含まれない。
6. 提出あり学生は `student_submission_dir(student_id)` が存在し、ファイルを含む。
7. 提出なし学生は `student_submission_dir(student_id)` が存在しない。

## リスクと対策

1. `submitted_at` の比較揺れ:
   - 比較が不安定なら比較粒度を helper 側で明文化して調整。
2. archive 配置変更の影響:
   - `archive_path` を単一の入口にして呼び出し側を固定化。
3. 実行環境依存（python/pytest 未整備）:
   - 実装と実行確認の段階を分離して進める。

## 未決定事項

archive 指定名の規約をどちらで統一するか:

1. `report-test-1`（拡張子なし）
2. `report-test-1.zip`（拡張子あり）

備考:
- どちらでも実装可能。期待値 registry と揃えて固定する。

