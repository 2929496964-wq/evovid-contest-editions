#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
if [[ ! -d .venv ]]; then "$PYTHON" -m venv .venv; fi
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.lock
exec .venv/bin/python run.py "$@"
