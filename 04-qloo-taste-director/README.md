# EvoVid Taste Director

> Public-source copy: raw execution logs, internal QA material, runtime/session data and old source-package inventories are excluded. Historical pass/fail and live/fixture boundaries are preserved in [public verification](evidence/PUBLIC_VERIFICATION.md). The new root [manifest](../PUBLIC-MANIFEST.json) inventories this exact copy.

**An independently runnable Qloo competition edition of EvoVid.** Public cultural reference → explicit entity choice → Qloo associations → three original creative briefs → editable four-shot storyboard → saved project → real motion-graphic MP4.

[简体中文](README.zh-CN.md) · [Architecture](docs/ARCHITECTURE.md) · [Compliance and release gates](docs/COMPLIANCE.md) · [Deployment](docs/DEPLOYMENT.md) · [Verification](docs/VERIFICATION.md)

## Current truth

- The full **DEMO** workflow works offline with clearly labeled **authored synthetic fixtures**. Fixture IDs/associations are not Qloo data. No synthetic affinity scores are displayed.
- The server contains the **real Qloo REST adapter** for Search and Insights. Contract/error tests exercise it with an HTTP transport double. **No real Qloo credential was obtained, read, created or used during this build. Live API integration is not yet verified.** LIVE without a key fails closed; errors never fall back to fixtures.
- Planning is an inspectable, deterministic tool-using workflow. **No LLM** is used. The agent resolves ambiguity, selects insights tools, checks constraints, and replans on feedback.
- MP4 export really renders the saved shots using **Pillow + FFmpeg**. It is a **silent geometric motion storyboard**, not neural text-to-video, film footage or licensed music.
- Code is prepared locally. **No public repository push, public deployment, credential registration or contest submission has been performed.** The external demo and public-source contest requirements remain release gates.

## Quick start

Requires Python 3.12 (tested) or Python 3.11 (compatible installer fallback, not executed here) and a modern browser. No model download, account or API key is needed for DEMO.

### Windows

1. Install Python 3.12 (preferred) or 3.11 from [python.org](https://www.python.org/downloads/), enabling the Python launcher.
2. Double-click `start.bat`. On first run it automatically creates `.venv` and installs the exact official-PyPI dependency lock, then starts without an extra success-pause. The installer prefers Python 3.12 and falls back to 3.11.
3. Your browser opens `http://127.0.0.1:8714`. A failed install stops with a visible error. `install.bat` remains available for manual dependency repair.

### Linux / macOS

```sh
./start.sh  # automatically installs locked dependencies on first run
# Headless or custom port:
PORT=8714 ./start.sh --no-browser
```

If the runtime packages are already installed, `python launcher.py --no-browser` works without a venv. The first-party installer does not install OS packages. On Linux, if Python reports `venv` unavailable, install your distribution's Python venv package. FFmpeg is discovered on PATH, otherwise the pinned `imageio-ffmpeg` PyPI wheel supplies its binary. It never downloads a model or binary at runtime.

The default bind is loopback. The default data directory is `.taste-data/`. Keep the browser session cookie if you want to reopen its saved projects; localStorage stores only the last project ID. A different browser receives an isolated workspace. This is a local prototype with anonymous capability sessions, not a multi-user account system.

## Try the complete workflow

1. Keep **DEMO** selected. Search **Moonlight**. Choose the 2016 or 2002 candidate yourself, demonstrating disambiguation.
2. Add **Spirited Away**, or switch category to Music artist and search **Daft Punk**. Pick 1–4 references.
3. Set an original creative goal, 12/16/20/24 seconds, aspect, pacing and phone-only/small-crew budget.
4. Select **Create my directions**. Inspect returned fixture associations separately from EvoVid's three creative interpretations.
5. Choose a direction. Edit shot titles, visual directions, duration distribution and camera motion. **Save storyboard** persists an optimistic-versioned revision.
6. Play the local canvas preview. **Export MP4** renders the saved storyboard. Download the video, JSON project with trace, or Markdown brief.
7. Remove a reference, search **Interstellar**, explicitly select it and **Replan**. The new project records before/after themes, input changes and a fresh insights operation. Actual provider results can legitimately overlap.
8. Reopen a saved project, reload during a run, or cancel a render. Restarted unfinished runs are marked **interrupted**, never presented as complete; retry is explicit.

Fixture catalog: Spirited Away, Moonlight (two candidates), Interstellar, Amélie, Arrival, The Grand Budapest Hotel, Daft Punk, Björk and Tycho. Other fixture queries honestly return no results.

## LIVE setup, only after authorization

See [server configuration](docs/DEPLOYMENT.md). The only credential variable is `QLOO_API_KEY`; it belongs in the **server process environment**, injected through the operator's approved secret manager. Do not send keys in chat, put them in frontend fields, CLI arguments, screenshots, exports or Git. `.env.example` is documentation only; the app deliberately does not automatically inspect or load local secret files.

This competition edition fixes the host to `https://hackathon.api.qloo.com` per the [official hackathon key guide](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide#getting-your-api-key), with `Accept: application/json` and `X-Api-Key`. It does not rotate hosts, follow redirects, search for keys, use a browser-held key or fall back after authentication failure. The eventual credential's authorized host/quota must be verified against the organizer's issuance instructions before a live smoke test. If it requires a different host, a reviewed explicit code/config change is required.

The UI asks for public cultural titles or artist stage names. Input filters reject obvious emails, URLs, telephone-like strings and markup. Such filters are not a universal PII detector: never enter personal names as private identity, contacts, account/device IDs, location history or private EvoVid materials. Creative goals remain in the local project and are **not sent to Qloo**. User/session IDs are never Qloo signals.

## Tests and evidence

```sh
python -m unittest discover -s tests -v
node --check static/app.js  # optional JS syntax check; Node is not a runtime dependency
python tools/make_sample.py
```

The tests include request contracts, 401/403/429/500/redirect/timeout/schema failure, absent key, ambiguous search, public-input guard, session/export isolation, same-origin checks, idempotence/conflicts, edits/stale versions, feedback and real H.264 output. The sample generator performs the actual application API flow using a local ASGI client and writes clearly labeled DEMO artifacts to `samples/`.

See `status.json` and [verification notes](docs/VERIFICATION.md) for the exact verified/unverified scope. Windows execution, Docker build and a real Chromium end-to-end visual check have not been claimed. A browser execution restriction prevented visual QA in this environment; DOM tests are not a substitute for a real browser.

## Source, licensing and credits

Based on the MIT public [EvoVid Pocket repository](https://github.com/2929496964-wq/evovid-pocket), baseline commit `31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`. `vendor/evovid/` preserves the original public model/store/renderer files for provenance; the running `taste/` package adapts its bounded storyboard, SQLite event-store and Pillow/FFmpeg renderer patterns. It does not copy the main project's private state, identities, configuration, memory, credentials, media or model weights.

Authored changes are MIT; the upstream MIT copyright/license is preserved. See [third-party notices](docs/THIRD_PARTY_NOTICES.md). The sample compositions and fixture associations are original synthetic demonstration content. Public film/artist names identify cultural references only; no posters, clips, music or fonts are redistributed. FFmpeg and other dependencies retain their own licenses. AI coding assistance was used.
