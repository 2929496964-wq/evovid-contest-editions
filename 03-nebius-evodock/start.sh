#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
fail() {
  printf '\nEvoDock could not start. Check the error above.\n' >&2
  if [ -t 0 ]; then printf 'Press Enter to close...'; read -r _unused || true; fi
  exit 1
}
printf 'EvoDock — local storyboard studio\n'
if [ ! -x .venv/bin/python ]; then
  if command -v python3 >/dev/null 2>&1; then PYTHON=python3
  elif command -v python >/dev/null 2>&1; then PYTHON=python
  else printf 'Install Python 3.11+ from https://www.python.org/downloads/ and rerun start.sh.\n' >&2; fail
  fi
  "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' || { printf 'Python 3.11+ is required.\n' >&2; fail; }
  printf 'First launch: creating an isolated Python environment...\n'
  "$PYTHON" -m venv .venv || fail
fi
.venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' || fail
if [ ! -f .venv/installed-requirements.lock ] || ! cmp -s requirements.lock .venv/installed-requirements.lock; then
  printf 'Installing pinned dependencies. Internet access may be needed on first launch.\n'
  .venv/bin/python -m pip install --disable-pip-version-check -r requirements.lock || fail
  cp requirements.lock .venv/installed-requirements.lock || fail
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  printf 'WARNING: FFmpeg is missing. Editing works, but rendering requires FFmpeg on PATH.\nSee https://ffmpeg.org/download.html\n'
fi
printf 'Starting on loopback; the exact local URL is printed below. Ctrl+C stops the app.\n'
printf 'DEMO FIXTURE needs no key. Live inference is never automatically enabled.\n'
.venv/bin/python launcher.py "$@" || fail
