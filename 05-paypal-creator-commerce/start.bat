@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if not errorlevel 1 (py -3 -m venv .venv) else (python -m venv .venv)
  if errorlevel 1 goto :fail
)
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.lock
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" launcher.py
if errorlevel 1 goto :fail
exit /b 0
:fail
echo Startup failed. Install Python 3.11+ from python.org and read README.md.
pause
exit /b 1
