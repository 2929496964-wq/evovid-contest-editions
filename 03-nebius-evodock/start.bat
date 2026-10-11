@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title EvoDock Storyboard Agent

echo EvoDock - local storyboard studio
if exist ".venv\Scripts\python.exe" goto check_venv

set "PYTHON_CMD="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"
if defined PYTHON_CMD goto check_python
python --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
  echo Python was not found. Install Python 3.11 or newer from https://www.python.org/downloads/
  echo During installation, enable Add Python to PATH. Then double-click start.bat again.
  goto failed
)
:check_python
%PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo Python 3.11 or newer is required. Update Python, then double-click start.bat again.
  goto failed
)
echo First launch: creating an isolated Python environment...
%PYTHON_CMD% -m venv .venv
if errorlevel 1 goto failed

:check_venv
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo The existing .venv cannot run Python 3.11+. Move it aside and run this launcher again.
  goto failed
)
if not exist ".venv\installed-requirements.lock" goto install_deps
fc /b requirements.lock ".venv\installed-requirements.lock" >nul 2>&1
if errorlevel 1 goto install_deps
goto start_app

:install_deps
echo Installing the pinned Python dependencies. Internet access may be needed on the first launch.
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.lock
if errorlevel 1 goto failed
copy /y requirements.lock ".venv\installed-requirements.lock" >nul
if errorlevel 1 goto failed

:start_app
where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo WARNING: FFmpeg is not on PATH. Editing still works; video rendering requires FFmpeg.
  echo Install it from the official links at https://ffmpeg.org/download.html and restart this app.
)
if not defined PORT set "PORT=8713"
echo Starting on loopback; the exact local URL is printed below. Close this window or press Ctrl+C to stop.
echo DEMO FIXTURE is available without an API key. Live calls remain disabled unless separately authorized.
".venv\Scripts\python.exe" launcher.py %*
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo EvoDock could not start. The error above has been kept visible.
echo No account, API key or paid model call was created by this launcher.
pause
exit /b 1
