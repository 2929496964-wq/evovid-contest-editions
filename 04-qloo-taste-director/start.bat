@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto install
.venv\Scripts\python.exe -c "import fastapi,uvicorn,httpx,PIL" >nul 2>&1
if errorlevel 1 goto install
goto run
:install
echo First run: installing locked dependencies from official PyPI...
call install.bat --from-start
if errorlevel 1 exit /b 1
:run
.venv\Scripts\python.exe launcher.py %*
if errorlevel 1 pause
