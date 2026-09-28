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
    echo Python 3.11以降をインストールしてください。
    echo https://www.python.org/downloads/ からダウンロードできます。
    pause
    exit /b 1
)

REM Pythonバージョンの確認
python -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo エラー: Python 3.11以降が必要です。
    python --version
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

REM Check virtual environment installation
if not exist ".venv\pyvenv.cfg" (
    echo 仮想環境が正しく作成されていないようです。
    pause
    exit /b 1
)

REM 仮想環境のPythonバージョンの確認
"%VENV_PYTHON%" -c "import sys; raise SystemExit(sys.version_info < (3, 11))" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo エラー: このツールで使用しているPythonが古いバージョンです。
    echo 最新のPythonをインストールしてください。
    echo インストール後、このフォルダーの.venvフォルダーを削除してから、もう一度run.batを実行してください。
    pause
    exit /b 1
)

REM Check package and dependency installation status
"%VENV_PYTHON%" -c "import autoprogen, PyQt5, openpyxl, psutil, dateutil" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 必要なパッケージをインストール中...
    "%VENV_PYTHON%" -m pip install --editable .
    if %ERRORLEVEL% neq 0 (
        echo エラー: パッケージのインストールに失敗しました。
        pause
        exit /b 1
    )
    echo パッケージのインストールが完了しました。
)

REM Launch main application
if "%DEBUG_MODE%"=="1" (
    set "APP_DEBUG=1"
    set "APP_VERBOSE_LOG=1"
    echo Starting in debug mode...
) else (
    set "APP_DEBUG="
    set "APP_VERBOSE_LOG="
    echo Starting application...
)
"%VENV_PYTHON%" -m autoprogen
if "%DEBUG_MODE%"=="1" (
    echo.
    echo デバッグモードで終了しました。
    pause
)
