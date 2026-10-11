@echo off
cd /d "%~dp0"
py -3 -m venv .venv || exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.lock || exit /b 1
echo FFmpeg must be installed separately and available on PATH. Then run start.bat
