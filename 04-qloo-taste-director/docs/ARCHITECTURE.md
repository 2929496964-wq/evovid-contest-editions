# Architecture

## Flow

Browser (vanilla JS + accessible HTML) → FastAPI same-origin API → server-side Qloo adapter → bounded rule-based planning → SQLite project/event store → Pillow frame drawing → FFmpeg H.264 encoding.

1. Search is a narrow public-title/stage-name tool. Two supported types: movie and artist. Candidates include provider UUID/name/category/year. There is no auto-selection, invented ID, or free-form provider request.
2. Server persists candidate provenance per anonymous browser session and per mode. A plan accepts only 1–4 IDs previously returned to that browser in the selected mode.
3. The planner selects movie insights plus media-keyword insights, using the exact confirmed IDs as `signal.interests.entities`. Goal, browser/session identity, budget and pacing never go to Qloo.
4. Raw returned order and optional affinity are preserved; no score is created when absent. Only supported numeric/UUID contribution metadata is exposed. Missing explainability has a visible warning. Metadata does not become a personal-preference probability.
5. Three distinct deterministic narrative structures use actual returned tags, or returned entity names when tags are empty. Each shot records source IDs. Palette, camera, story and sound choices are explicitly EvoVid interpretations.
6. Constraints enforce 4 shots, 2–6 seconds each and matching total (12/16/20/24 seconds). Phone-only uses one familiar room; small-crew uses two nearby locations.
7. Feedback makes a new saved project, calls insights again (no cache), records parent project, input changes and before/after theme. Results need not differ just because inputs differ.
8. Editing uses an integer version and rejects stale writes. Rendering snapshots one saved revision so later edits cannot change an active export.

## State, recovery, concurrency

SQLite persists anonymous session capabilities, selected candidates, jobs, documents and ordered events. Two bounded worker threads process at most 12 active operations globally and at most 2 per browser. Session/project limits and a server-wide hourly Qloo budget reduce accidental abuse. Explicit same-origin operation requests require `X-Taste-Client: 1` and reject cross-origin submissions. Browser session cookie is HttpOnly, SameSite=Strict; enable Secure for HTTPS deployment.

The API accepts an idempotency key. An identical operation returns its existing job; different input, kind or target with the same key returns 409. UI disables primary actions during active work. Cancellation is cooperative; an in-flight upstream request may take its bounded timeout to return. Render cancellation terminates FFmpeg and removes incomplete output. On startup, running/queued jobs become interrupted; they are not silently replayed. Refresh discovers active jobs and resumes status polling.

## Provider truth modes

| Source | Origin | `actual_http_call` | Use |
|---|---|---:|---|
| `demo_fixture` | Authored offline synthetic fixture | false | Explicit DEMO workflow only |
| `contract_mock` | Injected HTTP mock in tests | false | Adapter contracts, never live evidence |
| `live_http` | HTTPS request to fixed official host | true | Requires authorized server key |

The only outbound host is the official dedicated hackathon host, `https://hackathon.api.qloo.com`. There is no configurable arbitrary URL. LIVE is fail-closed. No automatic retries, no credential/host fallback, no redirects, no personal-profile signals, no external image fetches. Requests have a 5-second connect timeout, 15-second HTTP timeouts and 2 MB response cap. Responses/errors never expose headers, key, upstream error bodies or exception repr.

## EvoVid foundation

The public MIT upstream contributed the constrained Scene/Storyboard model pattern, SQLite job/event persistence design and Pillow/FFmpeg motion-rendering approach. The original relevant files are preserved in `vendor/evovid/`. The independent runnable `taste/` implementation adds cultural evidence, three briefs, four-shot constraints, multiple aspect ratios, explicit source modes, browser session isolation, idempotence, optimistic editing and feedback provenance. No private main-project bridge or credential import exists.

## Scope limits

A deterministic agentic workflow is not an autonomous LLM system. No automatic personal preference inference, audience demographics, sensitive-trait inference, high-impact decision, copyrighted media retrieval, voice/audio synthesis or neural video generation is implemented. Anonymous sessions are a minimal local/public-demo isolation mechanism; this is not a hardened multi-tenant production service. Single-process deployment is required for in-memory worker/quota coordination; do not run multiple workers without a shared durable queue/quota implementation.
