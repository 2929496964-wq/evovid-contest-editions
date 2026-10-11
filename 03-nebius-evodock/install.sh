#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
printf '\nPython dependencies installed. FFmpeg must be installed separately from its official source and available on PATH.\nRun ./start.sh\n'
