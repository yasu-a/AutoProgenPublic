## Generic Blocking Task Runner (with WaitDialog)

Handlerでスレッド管理を行わずに済むよう、Navigator経由で「WaitDialogによる待機」と「バックグラウンド処理」を一括実行する仕組みを実装。

### 実装内容

1. **BlockingTaskWorker** (`shared/view/task_runner.py`)
   - 汎用ワーカースレッドクラス
   - `task_func`は必ず`progress_callback: Callable[[str], None]`をキーワード引数として受け取る（必須）
   - `get_result()`, `get_error()`で結果とエラーを取得

2. **Navigator.run_blocking_task** (`app/navigator.py`)
   - WaitDialog + BlockingTaskWorker + QEventLoopを使用
   - `dialog.show()` + `QEventLoop.exec_()` + `dialog.close()`のパターン
   - エラーは例外として再送出

3. **Handlerでの使用例**
   - progress_callbackが必要な場合（Path→str変換など）:
     ```python
     def task(progress_callback: Callable[[str], None]):
         def progress_callback_wrapper(path: Path):
             progress_callback(str(path))
         return self._xxx_usecase.execute(progress_callback=progress_callback_wrapper)
     ```
   - progress_callbackが不要な場合:
     ```python
     def task(progress_callback: Callable[[str], None]):
         # progress_callbackは受け取るが使用しない（引数を無視）
         return self._xxx_usecase.execute(some_param="value")
     ```

### 注意事項

- **compiler searchは専用のダイアログ（CompilerSearchDialog）があるので、run_blocking_taskは使用しない**

---

python3.13だとCLIがNoneを返すことがある？？
バージョンの制限を設けたほうがいいかもしれない

第6回の5 授業後
python -V: 3.13.3

ファイル構造：

```
domain/entity/*.py
domain/value/*.py
domain/service/*.py (interface: domain/interface/service.py)
infra/repository/*.py (interface: domain/interface/repository.py)
infra/state/*.py (interface: domain/interface/state.py)
infra/gateway/*.py (interface: domain/interface/gateway.py)
infra/system/*.py (interface: domain/interface/system.py)  # TaskManagerやProcessPoolなど
feature/*/usecase/*.py (interface: feature/*/usecase/interface.py, dto: feature/*/usecase/dto.py)
feature/*/handler/*.py (interface: feature/*/handler/interface.py)  # IControllerやIPresenterをインターフェースとし、Handlerクラスを実装する
feature/*/view/*.py (interface: feature/*/handler/interface.py)  # Viewのインターフェースもhandler/interface.pyに定義
common/handler/interface.py  # IMainNavigatorなど共通のHandlerインターフェース
application/navigator.py  # MainNavigatorなどNavigatorの実装
```

---

# ダイアログの実装・起動ガイドライン

アプリケーション内でのダイアログ（モーダルウィンドウ）の実装および呼び出しに関するルールです。

## 1. 基本原則

* **誰が管理するか**: 原則として、**現在アクティブな画面の Handler (Controller)** が管理・呼び出しを行います。
* Navigator は「画面遷移（Launcher ⇔
  Workspace）」の管理に専念し、画面内の細かいダイアログ（設定、確認、タスク停止など）には関与しません（※再起動時のクリーンアップ処理など、例外的にNavigatorが呼ぶケースを除く）。


* **親 (Parent) は誰か**: **現在の View (Window/Widget)**
  を親として渡します。これにより、ダイアログが親画面の中央に配置され、親画面の操作をブロック（モーダル化）できます。
* **起動メソッド**: 基本的に **`exec_()`** を使用してブロックします。

## 2. 実装パターン

ダイアログの複雑さに応じて、2つのパターンを使い分けます。

### パターンA：機能付きダイアログ（Sub-Controller パターン）

設定画面、詳細編集、タスク停止画面など、ロジックやDIが必要な場合に使用します。
呼び出し側で **ViewとHandlerのセットアップ** を行い、実行します。

**構成要素:**

* **View**: `QDialog` を継承。ロジックを持たず、UI構築とセッター/ゲッターのみ。
* **Handler**: UseCaseを実行し、Viewを更新する。
* **UseCase**: ドメインロジック。

**呼び出しコード例 (Handler内):**

```python
# feature/project/handler/main_window_handler.py

def on_settings_button_clicked(self):
    # 1. Viewの生成（親は現在のView）
    # Importはメソッド内で行うと循環参照を防ぎやすい（Composition Rootとして振る舞う場合）
    from feature.settings.view.dialog_settings import SettingsDialog
    dialog = SettingsDialog(parent=self._view)

    # 2. UseCaseの取得（DIコンテナから）
    import app.di as di
    usecase = di.get_settings_usecase()

    # 3. Handlerの生成と結合
    from feature.settings.handler.settings_handler import SettingsHandler
    handler = SettingsHandler(view=dialog, usecase=usecase)
    
    # 必要ならHandlerの初期化処理
    # handler.load_initial_data()

    # 4. 実行（ここで処理がブロックされる）
    dialog.exec_()
    
    # 5. 終了後の処理（必要であれば）
    # HandlerやViewはスコープを抜けるとGCされる

```

### パターンB：単純な確認ダイアログ（Helper Method パターン）

「本当に削除しますか？」のようなYes/No確認や、エラー表示のみの場合に使用します。
Handlerが直接 `QMessageBox` をimportするのを避けるため、**Viewにヘルパーメソッド** を生やします。

**Viewの実装:**

```python
# feature/workspace/view/main_window.py
class MainWindow(QMainWindow):
    # ...
    def confirm_stop_task(self) -> bool:
        ret = QMessageBox.question(
            self, "確認", "タスクを停止しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        return ret == QMessageBox.Yes

```

**呼び出しコード例 (Handler内):**

```python
# feature/workspace/handler/main_window_handler.py
def on_stop_clicked(self):
    # Viewに尋ねさせる
    if self._view.confirm_stop_task():
        self._usecase.stop_task()

```

---

# DTOとエラーのリファクタリング方針

## 基本方針

現在、`dto.py` 等にまとめて定義しているDTOやエラーを、**そのDTO/エラーを用いてやり取りが定義されるinterfaceの直上に定義する**形式に統一します。

## 適用範囲

- **DTO**: UseCase、Handler、View間のデータ転送オブジェクト
- **エラー**: ドメインエラー、UseCaseエラー、Handlerエラーなど

## 配置ルール

### パターン1: UseCaseのDTO/エラー

```python
# feature/*/usecase/interface.py

# DTOはinterfaceの直上に定義
@dataclass
class SomeUseCaseDTO:
    """SomeUseCaseの結果を表すDTO"""
    field1: str
    field2: int

class SomeUseCaseError(Exception):
    """SomeUseCaseで発生するエラー"""
    pass

class ISomeUseCase(ABC):
    @abstractmethod
    def execute(self, param: str) -> SomeUseCaseDTO:
        raise NotImplementedError()
```

### パターン2: HandlerのDTO/エラー

```python
# feature/*/handler/interface.py

# DTOはinterfaceの直上に定義
@dataclass
class SomeHandlerDTO:
    """SomeHandlerの結果を表すDTO"""
    field1: str

class ISomeHandler(ABC):
    @abstractmethod
    def some_method(self) -> SomeHandlerDTO:
        raise NotImplementedError()
```

### パターン3: ViewのDTO/エラー

```python
# feature/*/handler/interface.py (Viewのインターフェースもここに定義)

# DTOはinterfaceの直上に定義
@dataclass
class SomeViewDTO:
    """SomeViewで使用するDTO"""
    field1: str

class ISomeView:
    @abstractmethod
    def set_data(self, data: SomeViewDTO) -> None:
        raise NotImplementedError()
```

## 移行計画

- **既存のコード**: リファクタリングは将来的に実施（優先度低）
- **新規追加**: 今後追加するすべてのDTO/エラーは上記の形式で定義する

## メリット

1. **可読性向上**: interfaceを見れば、使用するDTO/エラーがすぐに分かる
2. **保守性向上**: 関連する定義が一箇所にまとまる
3. **循環参照の回避**: interfaceファイル内で完結するため、依存関係が明確
