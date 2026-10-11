# Actual test report — 2026-10-11

## Environment

Linux x86_64, kernel 6.18.44, glibc 2.41; Python 3.12.14; Pillow 12.3.0; imageio-ffmpeg 0.6.0; system FFmpeg 7.1.5 with libx264. Chinese sample uses the locally installed Noto Sans CJK font. No model or cloud API.

## Executed and passed

1. `python -m py_compile evobridge/*.py run.py` — Python syntax checks passed.
2. `node --check static/app.js` — JavaScript syntax check passed.
3. `.venv/bin/python -m unittest discover -s tests -v` — **17 tests passed**. Covers English/Chinese wizard, two edits and undo, Unicode, ordering, invalid/empty/long input, atomic validation, brief cancellation, render-confirmation semantics, fresh project isolation, bounded history, static headers/CSP, Host/Origin/session token, path traversal, safe asset decoding, JSON restore and restart interruption/persistence.
4. `.venv/bin/python tools/create_evidence.py` — **three genuinely different H.264 exports**, each after two edits, passed. The 9-second briefs become 8 seconds after scene trimming; the 12-second Chinese brief becomes 11 seconds. Real ffprobe checks confirm 960×540 / 540×960 and exact durations. Byte hashes differ. The script also verifies a repeated render reuses its ID, actual cancellation publishes no finished movie, and an injected failure can be retried with a successful real export.
5. `.venv/bin/python tools/clean_smoke.py` — copied source into a new directory, created a fresh venv, installed the hash-locked dependencies, reran all 17 tests, started the server and verified `/api/health` and the actual HTML response. Historical result summarized in [public verification](../evidence/PUBLIC_VERIFICATION.md); raw install log is excluded.
6. Independent HTTP QA passed; the historical count and coverage are summarized in [public verification](../evidence/PUBLIC_VERIFICATION.md); raw per-check output is excluded. This separately covers three themes, editing, render hashes/duration, cancellation, deduplication, request validation, security and restart persistence.
7. Independent **jsdom simulation 7/7 passed**, with real local HTTP: sample scene cards; injected HTML stays text; export opens confirmation; closing confirmation performs no render call; genuine completed output linked into video/download elements; Chinese UI toggle; no uncaught app JavaScript errors. The historical result is summarized in [public verification](../evidence/PUBLIC_VERIFICATION.md); raw per-check output is excluded. jsdom is not a real browser, compositor, layout engine or video decoder.
8. Actual exported landscape/Chinese portrait frames were inspected. The delivered PNGs are decoded from the corresponding final MP4s by FFmpeg, not browser screenshots or invented UI images.

## Evidence mapping

- `samples/{cafe,garden-zh,makers}.json` contains the exact project snapshot, output SHA-256, byte count and duration for the sibling MP4.
- `samples/*-frame.png` is an actual decoded representative frame.
- `evidence/render-tests.json` contains final hashes, ffprobe output and cancellation/retry outcomes.
- `evidence/dependency-release-hashes.json` records official PyPI filenames and hashes used in `requirements.lock`.
- The root `PUBLIC-MANIFEST.json` inventories this public source copy. Internal local Git history and original packaging inventories are excluded.

## Blocked or not run

- **Real-browser UI, layout, mobile layout and video playback:** not passed. Playwright's Chromium launch failed at OS socket permission checks. A permitted retry gave the same result. The available cloud browser could not reach the app and a subsequent binding was refused by its URL policy. No restriction was bypassed.
- **UI screen recording:** not produced. `docs/DEMO_SCRIPT.md` is a 2:35 script, not a recording. The sample MP4s only prove output rendering. No public demo URL exists.
- **Windows/macOS startup and fonts:** scripts and platform paths are supplied, but actual execution happened only on Linux.
- No real Alexa integration is implemented or claimed. That is a deliberate simulator boundary rather than an untested production integration.
- A pre-event upstream SHA is missing from the supplied shallow checkout; see PROVENANCE.md. No historical commit was fabricated.

## Before submission

On a supported machine, run the browser through fresh project → brief → two edits → undo → image upload → confirmation cancel → confirmed export → playback/download → refresh/reopen → history. Repeat at 390 px width and use keyboard Escape on the dialog. Check local language/fonts. Record the actual flow with the supplied English script, obtain authorized judge access, verify entrant eligibility and publish/submit only with owner approval.
