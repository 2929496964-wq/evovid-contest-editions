@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.11 or 3.12 from python.org, then run this file again.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.lock
if errorlevel 1 (
  echo Dependency installation failed. Check internet access to PyPI.
  pause
  exit /b 1
)
echo Open http://127.0.0.1:8711 in your browser. PORT environment variable can override it.
.venv\Scripts\python.exe run.py %*
pause
