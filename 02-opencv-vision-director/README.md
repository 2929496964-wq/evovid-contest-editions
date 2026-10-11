# EvoVid Vision Director

> Public-source copy: raw execution logs, internal QA material, runtime/session data and old source-package inventories are excluded. Historical pass/fail and live/fixture boundaries are preserved in [public verification](evidence/PUBLIC_VERIFICATION.md). The new root [manifest](../PUBLIC-MANIFEST.json) inventories this exact copy.

An independent, local-first OpenCV 5 video review workstation. Upload your footage, inspect measured issues on a timeline, approve your own selection, and export a real H.264/AAC MP4 using FFmpeg.

**Current truth:** OpenCV 5.0.0 genuinely ran in a new Linux Python environment. Actual uploads, metric computation, human approval, FFmpeg rendering, audio preservation, cancellation, recovery and audit exports were tested. The AWS private-compute deployment is prepared but **not deployed or verified**. Windows startup and Docker build are prepared but untested. Browser visual QA was blocked by this execution environment; Eight DOM/API interaction checks passed; they do not verify visual layout or browser media playback. No competition registration or submission was performed.

## Start in a minute

Requires **64-bit Python 3.11 or 3.12** and internet access for the first dependency installation. No API keys, model weights, user coding, or paid services are needed.

- **Windows:** unzip into a writable folder and double-click `start.bat`.
- **Linux:** run `bash start.sh` in the unzipped folder.
- Open **http://127.0.0.1:8712**. Windows launches this address automatically.
- Set `PORT` before starting to change the port, e.g. `PORT=8812 bash start.sh`. The server binds loopback only.
- First launch creates `.venv` and installs the exact versions in `requirements.lock`. If FFmpeg isn't on PATH, the pinned `imageio-ffmpeg` package supplies its own binary. No runtime download is made by the application.
- Click **Try the synthetic quality lab** for the bundled demonstration. This is generated controlled footage, not a real-world benchmark. Or upload a video you have permission to process.

If setup fails, read the terminal error. Do not replace the pinned OpenCV dependency with 4.x. Startup refuses OpenCV versions outside major 5. Linux packaging here specifically tested 5.0.0.93 / runtime 5.0.0.

## Use it

1. Upload MP4/MOV/MKV/WebM/AVI, up to 150 MB, 180 seconds, 120 fps and 1920×1080 equivalent pixels. Portrait aspect ratios are supported by the implementation.
2. Review the unmodified source, warning timeline and per-interval luma, detail and motion metrics.
3. Ask for a target-length selection, and change sharpness preference if useful. Selection is quality-ranked then chronological. Motion is not rewarded.
4. Include/exclude intervals; optionally lift/reduce exposure or apply gentle sharpening. Any edit revokes the previous approval checkbox.
5. Approve the plan and render. Review output and original side by side. Download the MP4, CSV, JSON or ZIP audit bundle.
6. Cancel a running operation if needed. Restart-interrupted jobs are marked interrupted, never silently successful. Retry analysis explicitly; the original and previous outputs remain on disk.

A browser may not preview every input codec even if OpenCV can decode it. The rendered MP4 is H.264/yuv420p with the first audio track converted to AAC if present. Check sound and cut timing manually. No audio track is required.

## Privacy and bounds

- No automatic network calls, cloud fallback, model download or external upload during processing.
- Original files are stored by generated job ID, never by user-supplied paths. Filenames are display labels only.
- State writes are atomic, operations per job are serialized, and FFmpeg uses argument arrays without a shell.
- Container signatures are checked before decoding; playlists/URLs are rejected and media protocol access is restricted to file/pipe. Host validation and same-origin write checks are enabled. Remote mode also requires an access token of at least 24 characters.
- `runtime/` is private working data. Do not publish or include it in a source archive. There are 30 sessions max and 10 render attempts per job. Stop the app before manually archiving old runtime folders.
- One server process/worker only. This is a private single-user workstation, not a public multi-tenant service.

## Verify

```
.venv/bin/python -m pytest -q
.venv/bin/python tools/verify_environment.py
.venv/bin/python tools/evaluate.py
```

For HTTP end-to-end checks, keep the server running and in another terminal run:

```
.venv/bin/python tools/e2e.py --url http://127.0.0.1:8712
```

On Windows use `.venv\Scripts\python.exe` instead. Some restricted execution tools isolate loopback namespaces per command; `tools/run_e2e.py` launches both the server and checks in one process tree.

- [Public verification summary](evidence/PUBLIC_VERIFICATION.md): historical unit/integration results, including real decode/render and bundled-FFmpeg fallback, plus source-staging rechecks. Raw test logs are excluded.
- Latest offline contract recheck: **25 pytest cases passed** (18 original and 7 new). The new source/ASGI cases check environment labels and authentication; they do not run Docker or AWS. The image default is `container`; the EC2 template explicitly overrides it to `aws-ec2`.
- `evidence/e2e.json`: actual HTTP workflow results and checks.
- `evidence/evaluation/results.json`: five synthetic inputs, fixed-prefix baseline and actual vision-selected outputs; no invented human ratings.
- `evidence/evaluation/parameter-causality.json`: changing sharpness weight changes selection and actual output hashes on the same input.
- [Public verification summary](evidence/PUBLIC_VERIFICATION.md) and `evidence/wheel-sha256.txt`: recorded runtime and wheel provenance. Machine-specific paths and raw build/install logs are excluded.
- `status.json`: passed, untested and externally blocked checks.

Optional DOM/API test (Node 20+): install `jsdom@26.1.0` with `npm install --prefix .qa-node --ignore-scripts jsdom@26.1.0`, then run `node tools/dom_qa.cjs`. This uses a real local backend but does not substitute for a browser layout/playback test.

## Deliverables

- [Technical report](docs/technical-report.md), [architecture diagram](docs/architecture.svg), [demo script ≤5 min](docs/demo-script.md)
- [AWS private EC2 deployment](deploy/README.md), `Dockerfile`, `deploy/private-ec2.yaml`
- Five labeled synthetic source MP4s in `examples/`, with provenance and hashes in `examples/manifest.json`
- Actual baseline and vision outputs under `evidence/evaluation/`; approved plans, measured results and hashes retained. Execution logs and intermediate clip fragments are excluded.
- [Licenses and attribution](docs/third-party-notices.md), [acceptance truth](docs/acceptance.md)

## What is not claimed

This is explainable computer vision with human-approved actions. It is not a neural restoration model, semantic video editor, autonomous agent, real-world accuracy benchmark, completed AWS deployment, Windows certification, or completed contest entry. Intentional low light can be flagged; subtitles can hide blurred backgrounds from a global sharpness metric. No human preference study has been run.
