# EvoVid Creator Commerce

> Public-source copy: raw execution logs, internal QA material, runtime/session data and old source-package inventories are excluded. Historical pass/fail and live/fixture boundaries are preserved in [public verification](evidence/PUBLIC_VERIFICATION.md). The new root [manifest](../PUBLIC-MANIFEST.json) inventories this exact copy.

**A local-first creator studio with a real PayPal Sandbox Orders v2 adapter.** A fictional brief becomes an editable motion storyboard, then a watermarked video preview. A server-priced, revision-bound checkout unlocks a real portrait MP4 only after matching `COMPLETED` capture evidence.

[中文说明](README.zh-CN.md) · [Architecture & security](docs/architecture-security.md) · [Sandbox setup](docs/sandbox-setup.md) · [2:40 demo script](docs/demo-script.md) · [Verification status](status.json)

## Current truth

- This is a runnable development build, **not a submission-ready or submitted contest entry**.
- Default planner: **DEMO FIXTURE**, a deterministic template, not an AI model.
- Default payment: **TEST FIXTURE，非PayPal真实支付 / NOT A REAL PAYPAL PAYMENT**. It makes no PayPal API request and uses no real money.
- The actual local OpenAI-compatible adapter and actual PayPal Sandbox REST adapter are implemented. They have offline contract tests. **A real model inference and real PayPal Sandbox transaction have not been performed in this environment.** No credentials were created or obtained.
- The renderer creates original, silent Pillow/FFmpeg motion graphics, not neural video or photographic footage. The included `.mp4` files are actual playable renders, not UI recordings.
- Browser-engine execution is restricted in the development environment. HTML/JS and API tests do not establish visual/mobile/browser checkout correctness. Windows scripts are supplied but not executed on Windows.

## Quick start

Requirements: Python 3.11+, a current browser, and internet for the **first dependency installation only**. No model downloads. All dependencies are pinned in `requirements.lock`; `imageio-ffmpeg` supplies an encoder when system FFmpeg is absent.

**Windows:** double-click `start.bat`. If needed, install Python from [python.org](https://www.python.org/downloads/) first and enable its PATH option. Keep the command window open.

**Linux/macOS:** run `bash start.sh`. If Python reports that `venv` is unavailable, install your system's Python venv support, then rerun.

Open **http://127.0.0.1:8715**. To change the port, set `PORT` before starting, or copy `.env.example` to `.env` and edit `PORT`. Keep one server process; do not run this as a multi-worker public service. The launcher binds `127.0.0.1` only.

Once installed, start without another package-index check using `.venv/bin/python launcher.py` (Windows: `.venv\Scripts\python.exe launcher.py`). Stop with Ctrl+C. No public hosting, signup, billing, or external account is necessary for fixture mode.

## Try the complete offline flow

1. Keep **DEMO fixture · not AI** selected. Enter a fictional creative brief and choose **Build my storyboard**.
2. Edit the scene headlines, captions, durations, and accents. Save a new revision. **Render preview** creates a real watermarked 360×640 H.264 video.
3. **Open labeled fixture checkout**. The server quotes **USD 4.99**, one-time, for this exact saved revision. The browser cannot choose the amount.
4. Choose **PENDING** or **Wrong amount** to prove that exports stay locked. Use a fresh project after a permanent `REJECTED` verification. For the recoverable case, choose **Completed, response lost**, then **Verify existing order**.
5. A matching fixture `COMPLETED` capture unlocks **Render & download MP4**: 720×1280, 12 fps, silent, 4–24 seconds according to the storyboard. The file is explicitly stamped as fixture output.
6. Refresh or restart the server. The same browser profile retains projects, orders, and rights. A duplicate click does not create a second order or entitlement. Encoding failures can be retried without checkout again.

The included `evidence/sample-storyboard.json` can be restored in the project panel. JSON restoration creates a new project; it never imports payment rights.

## Real AI: user-configured local service

Copy `.env.example` to `.env`. Point `AI_BASE_URL` to an **already-running local OpenAI-compatible `/v1` service**, set `AI_MODEL` to its exact model ID, and restart. If your local service uses authentication, set `AI_API_KEY` locally; never put it in chat, a screenshot, source control, or a submitted archive.

Select **My local AI model**. The adapter POSTs `/chat/completions` and validates the returned title, 2–5 scene objects, captions, durations, and palette. Model output directly changes the editable timeline, preview, and export. There are no executable model instructions, remote asset URLs, or model-selected file paths. Invalid or unavailable model responses produce an error; **there is no silent fixture fallback**. The local evidence panel records provider, model, input/output hashes, revision and export hash. The app does not download or start a model.

Only loopback model endpoints are permitted in this edition. Use your own service's documented setup; remote paid model providers are intentionally outside this scope. API calls send the brief to that configured local process only.

## Real Sandbox integration

See [sandbox-setup.md](docs/sandbox-setup.md). A user with an existing suitable Sandbox application configures its client ID, secret, and merchant ID **locally**. Set `PAYMENT_MODE=sandbox` and restart. Missing configuration fails startup; it never silently reverts to fixtures.

The server creates an Orders v2 order and returns the approved **Sandbox-only** checkout URL. The browser goes to PayPal Sandbox, then returns to this app. The server queries, validates, and captures the stored order. Only complete and matching payment evidence creates the entitlement. No JS SDK, webhook, recurring subscription, refund or payout feature is needed for this bounded flow.

Fixture and Sandbox orders, captures, and rights are mode-separated in SQLite. Changing the mode cannot reuse fixture rights as a Sandbox purchase. Production payment mode, custom PayPal hosts, live approval URLs, and remote model URLs are rejected.

## Reproduce checks and evidence

After installing:

```sh
python -m unittest discover -s tests -v
node --check static/app.js             # optional JavaScript syntax check
python tools/make_evidence.py          # with a running fixture-mode launcher
```

Use the venv's Python if it is not activated. Tests use the standard-library `unittest` runner, FastAPI's ASGI client, mock external transports, and real FFmpeg encoding. No external transaction is performed. `tests/test_commerce.py` covers client amount tampering, no entitlement before completion, pending/decline/cancel, currency/amount/merchant/order/reference mismatches, concurrent clicks, unique rights, pre-capture verification, recovery, mode isolation, cross-project/session denial, CSRF/origin/host/input boundaries, revisions, import, encoder failure retries, and actual MP4 format.

See `status.json` for separately recorded passed, untested, and externally blocked checks. The sample videos in `evidence/` are intentionally shareable fictional fixture outputs. The live browser checkout and real model/Sandbox test remain mandatory before claiming those integrations have passed.

## Storage and privacy

The private runtime folder is `data/` (or `EVOVID_DATA_DIR`). It contains the SQLite ledger and media caches. Do not include it in a public archive. `.env`, `.venv`, runtime databases, and session cookies must also stay private. No analytics, CDN, remote fonts, or external assets are loaded by the studio. Server error messages avoid provider response bodies, secrets, and tokens.

A random HttpOnly session cookie is the local ownership boundary. Keep the same browser profile **and the same hostname** (`localhost` and `127.0.0.1` have different cookies) to resume. Clearing cookies loses access to that session's rights; the app deliberately has no weak email-based bypass. Export storyboard JSON for content portability. Backup the entire private data directory only for your own safekeeping. This local single-user edition is not designed for public shared hosting or protection from an administrator of the same computer.

## Upstream and rights

Based on the public MIT [EvoVid Pocket](https://github.com/2929496964-wq/evovid-pocket) baseline `31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`. The original small-creator storyboard contract and local motion-renderer approach are retained and extended. This independent edition replaces the iOS/RevenueCat-specific purchase flow with a local web studio, real local-AI adapter, and PayPal Sandbox ledger. See [upstream notes](docs/upstream-and-license.md) for the exact increment and retained reference files.

Authored application code and fictional artwork are MIT licensed. Dependencies retain their own licenses. FFmpeg is obtained by the user through dependency installation; no third-party model weights, music, photographs, private assets, or credentials are included. Font files are not redistributed. AI coding assistance was used in development. No repository push, deployment, agreement acceptance, account creation, real charge, or final contest submission was performed.
