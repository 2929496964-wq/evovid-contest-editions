@echo off
setlocal
cd /d "%~dp0"
if not defined PORT set PORT=8712
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -c "import cv2,fastapi,imageio_ffmpeg; assert cv2.__version__ == '5.0.0'" >nul 2>&1
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.lock
  if errorlevel 1 goto fail
)
if not exist examples\synthetic-quality-lab.mp4 (
  .venv\Scripts\python.exe tools\make_examples.py
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe tools\verify_environment.py
if errorlevel 1 goto fail
echo Open http://127.0.0.1:%PORT% in your browser. Ctrl+C stops the app.
start "" http://127.0.0.1:%PORT%
.venv\Scripts\python.exe -m uvicorn vision.server:app --host 127.0.0.1 --port %PORT% --workers 1
if errorlevel 1 goto fail
exit /b 0
:fail
echo Setup or startup failed. Python 3.11 or 3.12 64-bit is recommended. Check the error above.
pause
exit /b 1
