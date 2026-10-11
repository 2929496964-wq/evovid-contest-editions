#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
if [ ! -x .venv/bin/python ]; then "$PYTHON" -m venv .venv; fi
if ! .venv/bin/python -c 'import cv2,fastapi,imageio_ffmpeg; assert cv2.__version__ == "5.0.0"' >/dev/null 2>&1; then
  .venv/bin/python -m pip install --only-binary=:all: -r requirements.lock
fi
if [ ! -f examples/synthetic-quality-lab.mp4 ]; then .venv/bin/python tools/make_examples.py; fi
.venv/bin/python tools/verify_environment.py
printf '\nOpen http://127.0.0.1:%s in your browser. Ctrl+C stops the app.\n' "${PORT:-8712}"
exec .venv/bin/python -m uvicorn vision.server:app --host 127.0.0.1 --port "${PORT:-8712}" --workers 1
