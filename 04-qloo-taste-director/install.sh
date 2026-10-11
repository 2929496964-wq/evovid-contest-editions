#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --index-url https://pypi.org/simple -r requirements.lock
printf '\nInstalled. Start with ./start.sh\n'
