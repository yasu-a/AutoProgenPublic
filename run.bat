@echo off
chcp 65001 >nul
cd /D "%~dp0"

REM Check arguments
set DEBUG_MODE=0
if "%1"=="debug" set DEBUG_MODE=1

REM Check Python installation
echo Pythonのインストールを確認中...
python -V >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo エラー: Pythonがインストールされていません。
    echo Python 3.10以上をインストールしてください。
    echo https://www.python.org/downloads/ からダウンロードできます。
    pause
    exit /b 1
)

echo 仮想環境を確認中...

REM Check .venv directory existence
if not exist ".venv" (
    echo 仮想環境が見つかりません。.venvを作成中...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo エラー: 仮想環境の作成に失敗しました。
        pause
        exit /b 1
    )
    echo 仮想環境が作成されました。
)

REM Set virtual environment Python path
set VENV_PYTHON=.venv\Scripts\python.exe

REM Check requirements.txt installation
if not exist ".venv\pyvenv.cfg" (
    echo 仮想環境が正しく作成されていないようです。
    pause
    exit /b 1
)

REM Check package installation status (simple check)
if not exist ".venv\Lib\site-packages\PyQt5" (
    echo 必要なパッケージをインストール中...
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo エラー: パッケージのインストールに失敗しました。
        pause
        exit /b 1
    )
    echo パッケージのインストールが完了しました。
)

REM Launch main application
if %DEBUG_MODE%==1 (
    echo デバッグモードで起動中...
) else (
    echo アプリケーションを起動中...
)
"%VENV_PYTHON%" main.py
if %DEBUG_MODE%==1 (
    echo.
    echo デバッグモードで終了しました。
    pause
)