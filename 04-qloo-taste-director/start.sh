#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c 'import fastapi,uvicorn,httpx,PIL' >/dev/null 2>&1; then
  printf 'First run: installing locked dependencies from official PyPI...\n'
  ./install.sh
fi
exec .venv/bin/python launcher.py "$@"
