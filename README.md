# AutoProgen v0.4-alpha

プロ言の提出物の採点を効率化するためのツールです。

> [!IMPORTANT]
> このツールは採点を支援するためのものです。
> 開発者はツールの不具合で生じた採点ミスに責任を負いません。
>
> 最終的な点数を使用者が十分に検討した上でご利用ください。

> [!IMPORTANT]
> 利用者への対応が難しくなるので、アップデート通知機能が実装されるまで二次配布はご遠慮ください。
> GitHubへのリンクをご利用ください。

# 確認済み動作環境

- Windows 11
- Python 3.10

# v0.4-alpha

> [!WARNING]
> このバージョンは正式リリースではなく、テストを目的としたアルファ版です。

## 変更点

- １つのプロジェクトで１つの設問を扱うよう変更
- ファイル入出力に対応
- UIの大幅な変更
- [install-requirements.bat](install-requirements.bat)
  でPythonに必要なライブラリをインストールし、[run.bat](run.bat)でインストールしないよう変更
- （開発: 設計をレイヤー化）

> [!IMPORTANT]
> このバージョンで過去のプロジェクトデータを開くことはできません。

## 既知のバグ

バグを見つけたら開発者までご連絡ください。

### 重大なバグ

> [!CAUTION]
> テスト機能に重大なバグがあります。テスト機能は使わないでください。

- テストのアルゴリズムにバグがありテスト結果が正しく表示されない。
- プロジェクトを開いた直後とステージデータが更新された後、テーブルをスクロールするとすごく重い。

### ほかのバグ

- テストケースが複数ある状態ですべてのステージの実行を完了したのち、ソースコード抽出やコンパイルがエラーとなる状況を作って実行すると、1つ目のテストケース以外の実行状況が完了状態で残る。
- クリア操作後、実際にはステージデータは消えているのにテーブルの表示が更新されないことがある。再起動するとなおる。
- 採点画面で、出力ファイルのテキストエディタにフォーカスが奪われると、左右キーで生徒を移動できない。

# 使用技術

- Python
- PyQt5
- JSON
- Visual Studio Developer Command Prompt

# FAQ

**どうやって使うの？**

[チュートリアル](#チュートリアル)を参照してください。

**コンパイルがタイムアウトする**

[実行環境の性能に応じた設定のチューニング](#実行環境の性能に応じた設定のチューニング)を参照してください。

**実行がタイムアウトする**

生徒のプログラムの実行が（正常終了か異常終了かにかかわらず）停止しないで動き続けているときに発生します。

次の理由が考えられます：

- **生徒のプログラムが入力を待ち続けています。**
  テストケースを確認してください。
  例えば、コンソール上でEnterキーを押下する場所では、テストケースの入力文字列に改行を挿入する必要があります。
  テストケースが正しい自信があるなら、生徒のプログラムに原因があります。
- **生徒のプログラムが無限ループにはまっています。**
  この場合は生徒のプログラムに原因がありそうですが、テストケースの入力に間違いがないか確認する必要があるかもしれません。
- **実行時間が足りません。**
  プログラムの計算量や実行環境の性能によっては時間内に実行が終了しない可能性があります。
  実行のタイムアウトの設定は、テストケース編集画面の「実行の構成」タブ→「実行のオプション」→「実行のタイムアウト（秒）」を参照してください。

**ツールが落ちた・急に画面が消えて終了した**

バグでクラッシュしています。

もし時間があれば、[run.bat](run.bat)で起動する代わりに[run-debug.bat](run-debug.bat)で起動し、
バグを再現し、クラッシュしたときにコマンドプロンプトに表示されるエラーログを開発者に送ってやってください。
[run-debug.bat](run-debug.bat)で起動すると、プロセスの終了後もすぐにコマンドプロンプトが消えなくなります。

# チュートリアル

プロ言の提出物の採点を効率化するためのツールです。

生徒の提出物からソースコードを自動的に抽出、コンパイル、実行、テストし、その結果をもとに手動で採点するGUIツールを提供します。

生徒の提出物はmanabaからダウンロードしたzipファイル（以下「提出データ」）から展開されます。

GUIの背後でコンパイルと実行のプロンプトを叩いています。
コンパイルには授業と同様にVisual Studioに付属するツール群であるMSVCを利用します。

## ツールの起動

### 初回

> [!NOTE]
> この項目ではデフォルトのPythonにライブラリをインストールして起動する方法を説明します。
>
> 仮想環境など代替の環境で起動したい場合はこの手順を参考にして適宜環境を構築してください。

1. このツールをダウンロードします。
2. ダウンロードしたファイルがzipファイルなら展開します。
3. このツールはPythonで動作します。
   Pythonがインストールされていない場合はインストールする必要があります。（[Download Python | Python.org](https://www.python.org/downloads/)）
4. ツールの動作に必要なPythonライブラリをインストールします
   手順2で展開したフォルダにある[install-requirements.bat](install-requirements.bat)を実行します。
5. 手順2で展開したフォルダにある[run.bat](run.bat)を実行してツールを起動します。

### 2回目以降

- 初回の手順5のみを実行

## プロジェクトを作る

すべての作業データは「プロジェクト」という単位で管理されます。

１つのプロジェクトは、１つの提出データに含まれる１つの設問（prog01など）を扱います。

1. manabaから、生徒の提出物を含むzipファイルを適当な場所にダウンロードします。
2. ツールを起動してWELCOMEウィンドウを表示します。
3. 「新しいプロジェクト」タブを選択し、次のフィールドを入力します。
    1. 「プロジェクト名」に適当なプロジェクトにつける名前を入力します。
       例えば、第3回の授業のprog05.cを採点するプロジェクトなら、「3-5」などにすればわかりやすいでしょう。
    2. 「提出データ」で手順1でダウンロードしたzipファイルを選択します。
       右のアイコン「<img src="./img/folder.png" width="15px">」をクリックしてファイルを選択します。
    3. 「設問番号」に採点する設問番号を入力します。
       この番号をもとに提出ファイルが探索されます。例えば、prog05.cを採点する場合は`5`と入力します。
4. 「START」ボタンをクリックしてプロジェクトを開始します。

## コンパイラの設定（初回のみ）

必須の初期設定です。Visual Studio開発者ツール（MSVC）のパスを設定し、コンパイルが実行できるようにします。

1. ツールバーの「<img src="./img/settings.png" width="15px">設定」をクリックして設定画面を開きます。
2. 「Visual Studio開発者ツールのパス」の「自動検索」をクリックして、パスを検索します。この処理は10秒ほどかかります。
3. 検索が終わるとパスの選択を促されます。
   複数のバージョンのVisual Studioがインストールされている場合は正しいMSVCを選びます。
   パスを確認したら「OK」をクリックしてパスを設定します。
4. 「テスト」をクリックして、コンパイルテストを実行します。
   「コンパイラは正しく動作しています」と表示されれば設定は完了です。
5. そのまま画面を閉じて設定を保存します。

> [!NOTE]
> 手順2でパスが見つからない場合、Visual Studioがインストールされているか確認してください。

## テストケースの設定

ツールを動かす前に、生徒が書いたプログラムに与える入力を定義する必要があります。

次の４つをまとめて「テストケース」とよびます。

- 実行の構成
    - **入力ストリームの構成** 生徒のプログラムに与える標準入力やファイル入力の設定
    - **実行のオプション** 生徒のプログラムを実行するときの設定
- 自動テストの構成
    - **出力ストリームの自動テスト構成** 生徒のプログラムから受け取る標準出力やファイル出力のテスト方法の設定
    - **自動テストのオプション** 生徒のプログラムから受け取る出力をテストするときの設定

> [!TIP]
> 「標準入力」はプログラム実行時にコマンドプロンプトに与える入力で、
> C言語では`scanf`などで読み込まれる文字列のことです。
>
> 「標準出力」はプログラム実行時にコマンドプロンプトに表示される出力で、
> C言語では`printf`などで書きこまれる文字列のことです。

### テストケースの作成

1. ツールバーの「<img src="./img/research.png" width="15px">テストケースの編集」をクリックして、テストケースの一覧を表示します。
2. 「新規作成」をクリックしてテストケースを作成します。
3. 作成されたテストケースをダブルクリックして、テストケースの編集画面を開きます。
4. （以下のケースを参考にしてテストケースを編集します）
5. テストケースを編集したらそのまま画面を閉じて保存します。

### 【ケース１】標準入力を追加する

生徒のプログラムを実行する時にキーボード操作で与える文字列を設定します。

1. テストケースの編集画面を開きます。
2. 「実行の構成」タブを選択します。
3. 「入力ストリームの構成」の右上端にある「<img src="./img/plus.png" width="15px">」アイコンをクリックします。
4. メニューから「<img src="./img/console.png" width="15px">標準入力」を選択して、標準入力を追加します。
5. 追加されたタブ内のエディタに、生徒のプログラムを実行した後に入力する文字列を打ち込みます。

### 【ケース２】ファイル入力を追加する

・・・

### 【ケース３】標準出力をテストする

・・・

### 【ケース４】出力ファイルをテストする

・・・

### 【ケース５】ファイルに対する上書きをテストする

・・・

## 実行

ツールバーの「<img src="./img/play.png" width="15px">実行」をクリックして、生徒それぞれに次の「ステージ」を順に実行します。

1. **ソースコード抽出** ソースコードを自動的に抽出する
2. **コンパイル** ソースコードをコンパイルする
3. **実行** コンパイルしたプログラムをテストケースをもとに実行する（テストケースごと）
4. **テスト** 実行結果をテストケースをもとにテストする（テストケースごと）

> [!IMPORTANT]
> **生徒の提出物のファイル構成を修正する**
>
> 生徒が正しいプログラムを書いていても提出の形式に従っていない場合、実行時にエラーが発生することがあります。
> 公平な採点のために、ここでファイル構成を編集することでエラーを解決する必要があります。
>
> テーブルの学籍番号をクリックすると生徒の提出物を展開したフォルダを開けます。このフォルダの中身を編集すると、次回の実行に反映されます。
> なお、ここで編集できるファイル構成はもとの提出データのzipファイルの内容ではなく、このプロジェクトのために展開された別データです。

> [!IMPORTANT]
> **変更と再実行**
>
> 生徒の提出物のファイル構成やテストケースに変更が加えたら、再実行する必要があります。

> [!IMPORTANT]
> **処理されないステージとクリア**
>
> 実行は、未完了のステージやエラーで終了したステージを実行しますが、すでに完了したステージは実行しません。
> すべてのステージを実行する場合は、ツールバーの「<img src="./img/trash.png" width="15px">クリア」から、
> 実行結果を削除する必要があります。
>
> なお、クリア操作はステージの結果を削除しますが、採点でつけた点数は残ります。

## 採点

1. ツールバーの「<img src="./img/marker.png" width="15px">採点」をクリックして、採点画面を開きます。
2. 生徒のソースコードと実行結果を見ながら点数をつけます。
3. Aキーで前の生徒・Dキーで次の生徒に移動します。スペースキーで入力した点数をクリアします。
4. 採点が終わったらそのまま採点画面を閉じて結果を保存します。

> [!NOTE]
> 手順3で紹介したショートカットキーの詳細は、
> 採点画面の右下にある「<img src="./img/keyboard.png" width="15px">ショートカット一覧」をクリックしてください。

## 結果の出力

成績記録用のExcelシートの対応する生徒の対応する設問番号に、ツールでつけた点数を自動でエクスポートすることができます。

1. ツールバーの「<img src="./img/write.png" width="15px">点数をエクスポート」をクリックして、エクスポート画面を開きます。
2. 手順に従ってエクスポートを行います。

> [!NOTE]
> 設定画面の「成績記録用Excelのバックアップ」が有効になっていると、点数がエクスポートされる前にExcelファイルのコピーが作成されます。
> コピーはExcelファイルがあるフォルダに作られ、ファイル名に日時が追加されます。

## 実行環境の性能に応じた設定のチューニング

このツールはマルチタスクで全生徒のコンパイルと実行をするため、とても重いです。

設定画面では、実行環境の性能に応じて実行をチューニングするためのオプションを提供します。

1. ツールバーの「<img src="./img/settings.png" width="15px">設定」をクリックして設定画面を開きます。
2. 次のオプションを調整します：
    1. **コンパイルのタイムアウト** コンパイラの実行を何秒待つかを設定します。
       実行時にコンパイルがタイムアウトする場合は、この秒数を増やしてください。
    2. **並列タスク実行数** 実行時に何人の生徒を同時実行するかを設定します。
       実行時にコンパイルや実行がタイムしたり、システムの動作が重くなる場合は、この数を減らしてください。
3. そのまま画面を閉じて設定を保存します。



