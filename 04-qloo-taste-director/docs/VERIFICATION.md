# Verification report

Date: 2026-10-11. This report distinguishes observed results from pending integration. No actual Qloo credential or external Qloo call was used. No public deploy/push/submission occurred.

## Passed

- **Clean install:** `./install.sh` created an isolated Python 3.12 virtual environment and successfully installed all 18 pinned runtime distributions from official PyPI. `pip check` reported no broken requirements. Historical result: [public verification summary](../evidence/PUBLIC_VERIFICATION.md); raw logs excluded.
- **18 application/contract tests:** `.venv/bin/python -m unittest discover -s tests -v` passed, including provider request shapes, auth/rate/server/redirect/timeout/invalid schema, no-key fail closed, missing results, public input guard, unknown candidate rejection, mode separation, idempotence/conflict, optimistic editing, source-linked replanning, cross-session read/export prevention, origin/body/host limits, cooperative cancellation + explicit retry, interrupted-run recovery and actual H.264 rendering. Historical result: [public verification summary](../evidence/PUBLIC_VERIFICATION.md); raw output excluded.
- **Actual launcher / HTTP:** `start.sh --no-browser` obeyed `PORT=18714`, served the UI and `/api/state`, kept LIVE unconfigured and applied HttpOnly cookie/security headers. This test used actual loopback HTTP, not only an ASGI test client. Historical result: [public verification summary](../evidence/PUBLIC_VERIFICATION.md); raw output excluded.
- **Independent API exercise:** 21 checks passed against actual local HTTP, including ambiguity, JSON/Markdown export, same-session video access, blocked other-session download, actual render and restart persistence. Historical result: [public verification summary](../evidence/PUBLIC_VERIFICATION.md); raw output excluded.
- **Independent DOM simulation:** 7 checks passed using jsdom and the real HTML/JavaScript against a real local HTTP backend: candidate confirmation, three directions, safe text rendering, video URL after actual export, reset, visible no-key LIVE failure and no uncaught JS error. Historical result: [public verification summary](../evidence/PUBLIC_VERIFICATION.md); raw output excluded. Canvas/media APIs were stubbed; this is not layout or actual video-playback verification.
- **Syntax:** `node --check static/app.js` and Python compilation passed.
- **Actual sample:** Application API flow produced `samples/demo-project.json`, `demo-brief.md`, `demo-replanned-project.json`, `demo-storyboard.mp4` and `sample-manifest.json`. Input changed from Spirited Away to Interstellar; synthetic evidence changed from Wonder to Time. Both remain prominently marked DEMO.
- **Video probe:** `ffprobe` verified H.264, 640×360, 15 fps, 16.000 seconds; no audio stream. `evidence/ffprobe.json`. A real decoded video frame was visually inspected internally; it is not a browser screenshot or proof of browser playback.
- **Alternate aspect / bundled encoder:** 9:16 and 1:1 renders were encoded using the installed imageio-ffmpeg fallback binary and probed for dimensions/duration. `evidence/aspect-ratio-renders.json`.

The dedicated hackathon host was corrected to `https://hackathon.api.qloo.com` after the official developer-guide check; contract assertions now require that exact host, with no arbitrary URL or production-host fallback. Live access is still unverified.

## Not verified / blocked

- **Live Qloo calls:** no authorized key was obtained or inspected. Injected MockTransport responses are labeled `contract_mock`, with `actual_http_call=false`, and do not satisfy live evidence requirements. Actual credential host/quota/expiry remain unverified.
- **Real browser visual E2E:** this environment's Chromium launch was restricted. No attempt was made to evade the restriction. A separate cloud browser cannot reach this executor's localhost. Responsive layout, interactive canvas playback and native browser video controls need a real-browser check before release.
- **Windows start.bat execution:** prepared and statically reviewed (automatic first-run install; prefers Python 3.12, falls back to 3.11), but not run on Windows. Linux launcher and clean venv were tested.
- **Docker build/runtime:** Dockerfile/compose are prepared but not executed here; target architecture and container FFmpeg availability need validation.
- **Public deploy / source push / end-to-end external access / entry submission / eligibility:** not performed. See the compliance release gates.

## Reproduce

```sh
./install.sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
python tools/http_smoke.py
python tools/make_sample.py
ffprobe -v error -show_streams -show_format samples/demo-storyboard.mp4
```

The HTTP smoke helper deliberately clears the Qloo key in its child process. Sample and unit tests inject a no-key provider or a test-only sentinel/mock and never discover server credentials. Unit tests use a fresh session/database under the project's evidence directory and remove it afterward. A FastAPI/Starlette test-client deprecation warning concerning future httpx2 support may be printed; it is not a test failure, and the pinned httpx version currently passes.

## Manual pre-release checklist

1. Fresh desktop browser + narrow mobile viewport; keyboard navigate search, candidate selection, forms, direction picker and saved-project selector.
2. Save edits, change direction with unsaved edits, confirm/dismiss, open a different project, reload, cancel operations, retry and repeat clicks. Verify no unexpected duplicate project or render appears.
3. Verify actual preview animation and MP4 playback/download for all three aspect ratios and maximum text lengths.
4. Configure an explicitly authorized server key and exercise two real public-reference chains. Confirm successful request trace, real returned IDs and citation lineage; inspect for accidental credential exposure.
5. Authorize publication, deploy and verify externally in a fresh unauthenticated browser. Do not claim contest completion before this passes.
