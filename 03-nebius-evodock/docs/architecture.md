# Architecture and trust boundaries

```text
Browser on 127.0.0.1
  ├─ brief / editor / revisions / explicit render confirmation
  └─ same-origin, request-guarded FastAPI
      ├─ strict Pydantic schema (no paths, URLs-as-actions or tools)
      ├─ SQLite projects + revisions + jobs + budget + hash-chain trace
      ├─ DEMO FIXTURE → deterministic local planner
      ├─ LIVE (authorized only) → httpx → official GET /models
      │                                  → NVIDIA model /chat/completions
      │                                  → validate model + usage + schema
      └─ local renderer → Pillow RGB frames → FFmpeg → MP4/poster
                                           → ZIP + SRT + JSON + manifest
```

Only brief, selected storyboard and revision instruction leave the computer in live mode. The provider key remains in the server process. The renderer is never provider-controlled; scene assets, duration, path, codec and command are allowlisted/owned by the application. The model cannot see arbitrary files or private memory. No uploaded media or file browsing is supported in this first version.

## Data model

Projects have UUIDs, a fixed planning-source mode, the brief and current revision number. Revisions are append-only snapshots with source labels and revision instructions. Jobs move queued→running→complete/failed/cancelled; restart marks unfinished work interrupted. Optimistic revision checks prevent stale saves. A single active job is allowed per project. Local render files live in a server-owned UUID/revision directory. Render reuse applies to the exact revision.

Trace events store safe structured metadata and hashes; each references the prior project event hash. ZIP manifests hash every exported file. Neither mechanism authenticates Nebius independently. Provider usage-console corroboration is an external readiness gate.

## Provider policy

The real client uses TLS, an exact endpoint allowlist, no redirect following and no proxy environment inheritance. Model IDs are discovered each inference run and selected explicitly. The namespace filter accepts only nvidia IDs; the operator must verify the selected model's official open license and JSON capabilities. A request carries no tools. Responses require matching model ID, valid usage, stop finish reason and strict storyboard JSON. Extra keys, tool calls, invalid assets/durations and secret echoes cannot create saved plans.

Before each inference attempt, a SQLite transaction reserves a conservative input-byte + output-token allowance and one daily attempt. Reservations are never refunded automatically on uncertainty. One 429 retry is possible; timeout, network errors and 5xx have no automatic POST retry. HTTP error bodies never enter user-visible errors or saved trace. Cancelled successful provider calls retain safe usage but do not apply the returned plan.

## Local security scope

Loopback only, allowed Host validation, no CORS, exact same-origin checks for mutations, mandatory custom request header, required numeric content length with streamed actual-body limit, strict request schemas, CSP, no inline scripts and textContent-based rendering. Keys are rejected if accidentally pasted into project text and discarded if echoed by the provider. These are local single-user protections, not authentication for remote hosting. Local malware or another process running as the user is outside this prototype's threat boundary.

## Known engineering limits

Two worker threads and at most four queued/running jobs. A cancellation may wait for a blocking HTTP timeout; it cannot recall a completed cloud charge. Render cancellation is checked each frame; encoder finalize may take up to 30 seconds. Only one server process should use a data directory. No encrypted local database, deletion UI, authentication, billing dashboard reconciliation, multiplayer collaboration, crash-resume renderer or broad model-quality benchmark is claimed.
