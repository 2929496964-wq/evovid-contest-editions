@echo off
setlocal
cd /d "%~dp0"
set "PY_CMD=py -3.12"
py -3.12 -c "import sys" >nul 2>&1
if errorlevel 1 (
 set "PY_CMD=py -3.11"
 py -3.11 -c "import sys" >nul 2>&1
 if errorlevel 1 goto python_missing
)
%PY_CMD% -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requirements.lock
if errorlevel 1 goto fail
echo Installed. Starting requires no API key in DEMO mode.
if /i not "%~1"=="--from-start" pause
exit /b 0
:python_missing
echo Python 3.12 or 3.11 with the Windows Python launcher is required.
echo Install from https://www.python.org/downloads/
:fail
echo Installation failed. Check the Python installation and your network, then try start.bat again.
pause
exit /b 1
