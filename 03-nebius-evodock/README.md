# EvoDock Storyboard Agent

> Public-source copy: raw execution logs, internal QA material, runtime/session data and old source-package inventories are excluded. Historical pass/fail and live/fixture boundaries are preserved in [public verification](evidence/PUBLIC_VERIFICATION.md). The new root [manifest](../PUBLIC-MANIFEST.json) inventories this exact copy.

A local-first creative studio derived from the public MIT EvoVid branch. It turns an approved creative brief into an editable, versioned storyboard, then renders an actual silent H.264 motion-graphics video and a portable project package.

**Current truth (2026-10-11): the complete offline workflow works. Real Nebius integration is BLOCKED and has made zero live requests.** Legal Token Factory access for the actual country, an authorized key and authorized runtime usage are still required. Fixture/contract tests are not contest compliance evidence.

[中文说明](README.zh-CN.md) · [Architecture](docs/architecture.md) · [Provider setup](docs/provider-setup.md) · [2:50 demo script](docs/demo-script.md) · [Readiness checklist](docs/production-readiness.md) · [Sources](docs/sources.md)

## What works now

- Browser studio with a persistent project list, shot titles/captions, duration, local asset selection, motion, palette, reorder, add/remove, save and revision history.
- Explicit **DEMO FIXTURE** planning. Synthetic deterministic templates are fully usable without a key; they are not an LLM. Fixture changes support shorter, warmer and reversed order; other requests replace the last caption.
- Production HTTP integration path: official Nebius `GET /models` → exact discovered NVIDIA model selection → `POST /chat/completions` → strict local schema validation. No model ID is guessed. No NVIDIA NIM or alternative provider is substituted.
- Live planning/revision fails closed if unauthorized, missing a key, missing consent, invalid output, missing usage, wrong model, quota exhausted or upstream failure. It never falls back to a fixture.
- Real 960×540, 24-fps H.264 MP4, poster, SRT captions, editable JSON, trace and SHA-256 manifest in a ZIP. Rendering uses FFmpeg and locally drawn geometry/type, **not neural video generation**.
- Cancel jobs; retry explicitly; restore earlier revisions into a new edit; reuse the same completed render rather than duplicate work.
- Conservative persisted daily quotas, one bounded 429 retry, no automatic retry for timeout/network/5xx ambiguity, no key in browser/logs/exports, loopback binding, no user file/path/tool execution.

## Quick start

Requirements: Python 3.11+ (tested on Python 3.12/Linux), FFmpeg with `libx264` on PATH. No GPU, model download, Node or cloud account is needed for the fixture path. FFmpeg is an external system prerequisite, not bundled; use [FFmpeg's official download page](https://ffmpeg.org/download.html) and verify local `ffmpeg -version`. Windows/macOS launch scripts are supplied but have **not** been executed on those operating systems.

The launchers now check Python, create `.venv` on first use and install the exact lock automatically. They leave clear errors visible instead of asking you to type setup commands. FFmpeg remains a separately installed system prerequisite.

Fast path: double-click `start.bat` on Windows, or run `./start.sh` on Linux/macOS. The manual commands below are optional alternatives.

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
./start.sh
```

Windows PowerShell or Command Prompt:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
start.bat
```

Alternatively, `install.sh` / `install.bat` run those installation steps explicitly. They install only pinned Python packages; no provider access or models are activated. On Windows `click` may add its platform-specific dependency `colorama`; see the conditional pin in the lock.

Open **http://127.0.0.1:8713**. `PORT` overrides the default; `python launcher.py --port 8713 --data-dir data` is also supported. The process never listens on a LAN interface. Runtime data is stored in `data/` unless `EVODOCK_DATA_DIR` or `--data-dir` is set. `.venv` and runtime data are excluded from the source release.

1. Keep **DEMO FIXTURE** selected and click Create storyboard.
2. Edit a shot and Save edits. Ask “Make it shorter”, then “Make it warmer”. Each changes actual saved data.
3. Confirm & render locally, accept the local render confirmation, and play the preview.
4. Download the MP4 or ZIP. The fixture watermark remains in every frame.
5. Restart the server and select the saved project to verify persistence.

## Safe real-provider activation (not yet performed)

Read [the full setup guide](docs/provider-setup.md) first. Do not send a key in chat. Do not create an account using false country information, borrow an account, use a VPN to evade a restriction, or interpret a regional endpoint as permission to access the service.

After legitimate access, a separately authorized existing key, and runtime/spending authorization are in place, run `.venv/bin/python tools/run_with_key.py` (Windows: `.venv\Scripts\python.exe tools\run_with_key.py`). It uses a hidden terminal prompt, keeps the key only in the process, and asks you to select your account's official endpoint. It neither creates nor persists a key. Then use **Discover NVIDIA models**, verify the chosen model card/license, select the exact returned ID, check transmission consent and start a live plan.

Environment variable names: `NEBIUS_API_KEY`, `NEBIUS_LIVE_AUTHORIZED=1`, `NEBIUS_BASE_URL`, optional `NEBIUS_JSON_MODE=1` only for a model documented to support JSON mode. No `.env` file is loaded automatically. The base URL is restricted to the documented global or US-central1 Token Factory endpoint. Only planning uses Nebius; all other operations stay local.

## Verification

```sh
python -m unittest discover -s tests -v
python tools/make_samples.py
python tools/verify_package.py examples/project.zip
```

Tests use Python's built-in `unittest`. `test_contract.py` uses **the real production HTTP client with httpx.MockTransport** and synthetic HTTP responses; this is not a live integration test. `test_workflow.py` tests the actual API/SQLite/FFmpeg path, cancellation, persistence, export integrity and range playback. See [public verification summary](evidence/PUBLIC_VERIFICATION.md), `evidence/fixture-evaluation.json`, `evidence/ffprobe.json` and `status.json`. Raw test/install logs and internal QA reports are excluded from public source.

Three fictional briefs each have two fixture revisions. `examples/preview.mp4` and `examples/project.zip` are an actual locally generated 10-second sample. Sample files contain no identities, private memories, user footage, keys or copyrighted third-party assets. Local fonts are system fonts and are not redistributed. Optional CJK text requires a locally installed CJK font via `EVODOCK_FONT_PATH`; glyph support is not guaranteed by the default font.

## Evidence limits

Trace records include source labels, endpoint/model, request/input/output/catalog hashes, timestamps, latency, HTTP status, usage and a hash of the provider response ID. No raw provider envelope or secret is retained. The hash chain and ZIP manifest detect local corruption, **not independent attestation**. A successful real call must still be corroborated with the actual Nebius usage console and account authorization; those remain absent. Local edit provenance stays distinct from model provenance.

A successful HTTP response alone is insufficient: the exact selected model, consistent usage, a completed choice and valid storyboard must all exist. Invalid completions retain safe usage where available but do not save a storyboard. In-flight provider cancellation cannot guarantee provider-side cancellation or a refund. Request quotas are conservative control limits, not an exact tokenizer or currency cap. A cached export is reused only for the same revision.

## Public-branch provenance and new work

Upstream: [2929496964-wq/evovid-pocket](https://github.com/2929496964-wq/evovid-pocket), commit `31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`, MIT. This independent derivative follows the upstream's strict Pydantic storyboard, SQLite persistence and local Pillow/FFmpeg motion-rendering design. It retains the MIT license. See [PROVENANCE.md](PROVENANCE.md) for adaptation details. No private Windows master project was read or included.

This build's substantive additions are the Nebius/NVIDIA discovery+planning adapter, bounded tool-free schema, full shot editor, successive revisions and diffs, conservative persistent usage ledger, explicit live/fixture separation, hashed execution trace, revisioned media+project exports, multi-platform launch scripts, mock-HTTP contract/security tests and local evidence suite. No source was published, externally deployed, submitted to a contest or uploaded to YouTube by this build.

## Contest and production status

Prepared for an Apps and Agents direction, **not submission-ready**. The local prototype cannot satisfy a real Nebius/NVIDIA runtime requirement while service access and live evidence are blocked. Publishing a repository/demo, providing free judge access through the official review window and uploading the under-three-minute English demo all require separate authorization and verified current contest rules. This is a single-user local prototype, not a multi-user production service. See the readiness checklist for precise gates.

MIT-authored application code; dependencies retain their own licenses. No model weights are bundled. Development used AI coding assistance.
