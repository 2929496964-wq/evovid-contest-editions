# Architecture and threat model

## Data flow

Browser static UI → same-origin JSON HTTP endpoints → bounded command state machine / project editor → SQLite → confirmed immutable render snapshot → single-worker queue → Pillow RGB frames → FFmpeg H.264 → local output plus SHA-256 manifest.

Runtime dependency graph: Python standard library + Pillow 12.3.0 + imageio-ffmpeg 0.6.0. No JavaScript framework, build service, cloud credential, model or network runtime dependency. FFmpeg is discovered locally, then from the installed wheel. Fonts are discovered from local platform candidates, with `EVOBRIDGE_FONT` as an explicit local override.

## Modules

- `model.py`: atomic validation, three-scene templates, bilingual command grammar, brief wizard, undo snapshots and limits.
- `app.py`: loopback HTTP, persistent projects/assets, same-origin session protection, import validation and render coordination.
- `job_store.py`: MIT upstream SQLite job/event store, independent connections and parameterized SQL.
- `render.py`: Pillow raster frames, bounded text layout, animated shapes/text/image pan, no-shell FFmpeg process and cancellation.
- `static/`: responsive local workspace; keyboard-friendly native forms/dialog, language toggle, material thumbnails, editing, history, explicit actual-video mode.

Projects retain theme, audience, duration, tone, format, ordered scenes, revision, wizard state, messages and bounded undo history. A render saves an immutable project snapshot. SHA-256 of project ID/revision/scenes/format/duration deduplicates queued, running or completed repeats. Explicit retry after failure/cancellation creates a new job. On service restart, queued/running jobs become interrupted. They never silently resume.

## API

`GET /api/state`, `/api/health`; POST `/api/projects`, `/api/brief`, `/api/command`, `/api/edit`, `/api/undo`, `/api/import`, `/api/assets`, `/api/render`, `/api/cancel`. Mutation requests need JSON plus the session token returned only to same-origin page code. Render requires `confirmed: true` and the current revision. Assets and outputs are addressed by server-created UUID only. Static files use an explicit allowlist. Video supports byte-range requests for seeking.

## Defenses and bounded input

127.0.0.1 binding; exact localhost Host and Origin checks; no CORS; random session token; CSP forbids external scripts, frames and connections; text escaped or assigned via textContent; SQL parameters; no shell command interpolation; no arbitrary client filesystem path; 12 MiB HTTP body maximum; 8 MiB / 20 MP image maximum; commands 2,000 chars; theme/audience 100 chars; headline 100/caption 220 chars; three scenes; 45-second output maximum; maximum ten queued/running renders. Image inputs are decoded and re-encoded as JPEG, stripping metadata and active formats. Imported projects receive new IDs and drop external asset references.

Cancellation checks between frames and before publishing the final output. Temporary MP4s are removed on interruption/failure. Existing exports are immutable. System shutdown recovery marks unfinished jobs visibly, while preserving completed files and projects.

## Known limits

Single-user local trusted-computer app, not a hosted multi-tenant service. No authentication against another process already running as the same local user. The service is not intended to be exposed publicly. No speech recognition, audio track, timeline media trimming, neural generation, Alexa connection or runtime LLM. Three scene durations can be trimmed/extended; images can be attached; arbitrary imported video/audio clips are not supported. CSS preview is approximate. Full UI browser QA and Windows/macOS execution remain unverified in this environment. A failed-history Retry button explicitly reviews the current storyboard rather than silently replaying an older snapshot.
