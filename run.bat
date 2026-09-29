@echo off
setlocal
cd /D "%~dp0"

REM ==============================================================================
REM Initial settings
REM ==============================================================================

set "SUPPORTED_PYTHON_MESSAGE=AutoProgen supports Python 3.11 through 3.14."
set "VENV_PYTHON=.venv\Scripts\python.exe"
set "PYTHON_MANAGER_AUTOMATIC_INSTALL=false"

set "DEBUG_MODE=0"
if "%1"=="debug" set "DEBUG_MODE=1"
set "SETUP_ONLY=0"
if "%1"=="setup-only" set "SETUP_ONLY=1"

REM Process overview:
REM   1. Reuse an existing compatible .venv.
REM   2. Otherwise, search the py launcher and then Python on PATH.
REM   3. Prepare .venv and the required packages.
REM   4. Start the application in the requested mode.

echo [run.bat] Checking the virtual environment...
if exist ".venv\" goto check_existing_venv
goto find_python

REM ==============================================================================
REM Validate an existing virtual environment
REM ==============================================================================

:check_existing_venv
if not exist ".venv\pyvenv.cfg" goto invalid_venv
if not exist "%VENV_PYTHON%" goto invalid_venv

"%VENV_PYTHON%" -c "import sys; raise SystemExit(not ((3, 11) <= sys.version_info[:2] < (3, 15)))" >nul 2>&1
if errorlevel 1 goto unsupported_venv

echo [run.bat] Reusing the existing compatible .venv.
"%VENV_PYTHON%" --version
goto check_packages

REM ------------------------------------------------------------------------------
REM Leave an invalid environment unchanged and show recovery instructions
REM ------------------------------------------------------------------------------

:invalid_venv
echo [run.bat] Error: The existing .venv is not a valid virtual environment.
echo [run.bat] %SUPPORTED_PYTHON_MESSAGE%
echo [run.bat] Delete or rename .venv, and then run run.bat again.
pause
exit /b 1

:unsupported_venv
echo [run.bat] Error: The existing .venv uses an unsupported Python version.
echo [run.bat] %SUPPORTED_PYTHON_MESSAGE%
"%VENV_PYTHON%" --version
echo [run.bat] Delete or rename .venv, and then run run.bat again.
pause
exit /b 1

REM ==============================================================================
REM Find Python for a new virtual environment
REM ==============================================================================

:find_python
echo [run.bat] Searching for a supported Python installation...
set "PYTHON_CMD="
set "PYTHON_LABEL="
set "PATH_PYTHON_FOUND=0"

REM Check py launcher candidates from Python 3.14 down to Python 3.11
where py >nul 2>&1
if errorlevel 1 goto try_path_python

call :try_python "py -3.14" "py -3.14"
if errorlevel 1 goto try_py313
goto create_venv

:try_py313
call :try_python "py -3.13" "py -3.13"
if errorlevel 1 goto try_py312
goto create_venv

:try_py312
call :try_python "py -3.12" "py -3.12"
if errorlevel 1 goto try_py311
goto create_venv

:try_py311
call :try_python "py -3.11" "py -3.11"
if errorlevel 1 goto try_path_python
goto create_venv

REM ------------------------------------------------------------------------------
REM Check Python on PATH only when the py launcher finds no supported version
REM ------------------------------------------------------------------------------

:try_path_python
where python >nul 2>&1
if errorlevel 1 goto no_supported_python
set "PATH_PYTHON_FOUND=1"

call :try_python "python" "Python on PATH"
if errorlevel 1 goto no_supported_python
goto create_venv

REM ==============================================================================
REM Create a virtual environment with the selected Python
REM ==============================================================================

:create_venv
echo [run.bat] Creating .venv with %PYTHON_LABEL%.
%PYTHON_CMD% --version
%PYTHON_CMD% -m venv .venv
if errorlevel 1 goto venv_creation_failed

if not exist ".venv\pyvenv.cfg" goto venv_creation_failed
if not exist "%VENV_PYTHON%" goto venv_creation_failed

"%VENV_PYTHON%" -c "import sys; raise SystemExit(not ((3, 11) <= sys.version_info[:2] < (3, 15)))" >nul 2>&1
if errorlevel 1 goto venv_creation_failed

echo [run.bat] The virtual environment was created successfully.
goto check_packages

REM ------------------------------------------------------------------------------
REM Stop when virtual environment creation fails
REM ------------------------------------------------------------------------------

:venv_creation_failed
echo [run.bat] Error: Failed to create .venv with %PYTHON_LABEL%.
echo [run.bat] If a partial .venv remains, delete it and run run.bat again.
pause
exit /b 1

REM ------------------------------------------------------------------------------
REM Stop when no supported Python installation is available
REM ------------------------------------------------------------------------------

:no_supported_python
echo [run.bat] Error: No supported Python installation was found.
echo [run.bat] %SUPPORTED_PYTHON_MESSAGE%
if "%PATH_PYTHON_FOUND%"=="1" python --version
echo [run.bat] Install Python 3.11, 3.12, 3.13, or 3.14, and then run run.bat again.
echo [run.bat] Download Python from https://www.python.org/downloads/
pause
exit /b 1

REM ==============================================================================
REM Check the application and runtime dependencies
REM ==============================================================================

:check_packages
"%VENV_PYTHON%" -c "import autoprogen, PyQt5, openpyxl, psutil, dateutil" >nul 2>&1
if errorlevel 1 goto install_packages
goto packages_ready

REM ------------------------------------------------------------------------------
REM Run editable install only when a required import is unavailable
REM ------------------------------------------------------------------------------

:install_packages
echo [run.bat] Installing the application and required packages...
"%VENV_PYTHON%" -m pip install --editable .
if errorlevel 1 goto package_install_failed
echo [run.bat] Package installation completed successfully.
goto packages_ready

:package_install_failed
echo [run.bat] Error: Package installation failed.
pause
exit /b 1

REM ------------------------------------------------------------------------------
REM CI prepares the environment without opening the GUI
REM ------------------------------------------------------------------------------

:packages_ready
if "%SETUP_ONLY%"=="1" goto setup_complete
goto launch_application

:setup_complete
echo [run.bat] The virtual environment and required packages are ready.
exit /b 0

REM ==============================================================================
REM Launch the application
REM ==============================================================================

:launch_application
if "%DEBUG_MODE%"=="1" goto launch_debug

set "APP_DEBUG="
set "APP_VERBOSE_LOG="
echo [run.bat] Starting application...
"%VENV_PYTHON%" -m autoprogen
exit /b 0

:launch_debug
set "APP_DEBUG=1"
set "APP_VERBOSE_LOG=1"
echo [run.bat] Starting in debug mode...
"%VENV_PYTHON%" -m autoprogen
echo [run.bat] The application exited in debug mode.
pause
exit /b 0

REM ==============================================================================
REM Helper subroutine for checking a Python candidate
REM ==============================================================================

:try_python
REM Save the candidate only when it is Python 3.11 through Python 3.14
%~1 -c "import sys; raise SystemExit(not ((3, 11) <= sys.version_info[:2] < (3, 15)))" >nul 2>&1
if errorlevel 1 exit /b 1
set "PYTHON_CMD=%~1"
set "PYTHON_LABEL=%~2"
exit /b 0
