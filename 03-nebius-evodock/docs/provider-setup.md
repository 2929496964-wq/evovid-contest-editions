# Real provider activation and safe credential handling

## Stop conditions in this build

The actual-country service-onboarding issue remains unresolved. No account was created, no API/OAuth credential was generated, no real model call occurred and no fee was incurred by this work. **Do not activate live mode until official access and authorization are established.** A contest registration does not establish Token Factory service availability.

1. Obtain an official resolution from Nebius for service access using the true country/residence. Do not switch to a false country, VPN, borrowed account or another inference company to represent compliance.
2. Separately approve any account terms, persistent credential creation and runtime spending. This build does not do these steps.
3. Use an existing authorized Nebius key only in your local server process. Never paste it in chat, browser controls, brief, screenshots, source files, a repository or a shell command containing a literal key.
4. Verify the applicable current model pricing in the legitimate account and approve the usage budget. The app caps requests/tokens but does not implement a currency cap. Credit balances and account quotas may impose additional limits.

## Recommended local injection

Linux/macOS: `.venv/bin/python tools/run_with_key.py`

Windows: `.venv\Scripts\python.exe tools\run_with_key.py`

This script asks for local confirmation of authorized live usage, offers the documented endpoints, then uses Python getpass for a hidden key prompt. The key is held only by the process; nothing is written to a config file. Closing the process removes that process's copy. Existing authorization is still required: the script's local confirmation cannot resolve legal eligibility or grant a third party access to an account.

For managed environments, inject `NEBIUS_API_KEY` through the environment's approved secret manager, `NEBIUS_LIVE_AUTHORIZED=1`, and `NEBIUS_BASE_URL` set to the legitimate account's endpoint. Do not print the environment or enable HTTP debug logging. No `.env` loader is used; `.env.example` is documentation only. API keys are never included in the API status endpoint.

## API sequence

- `GET https://api.tokenfactory.nebius.com/v1/models` with server-side Bearer key. The alternative documented endpoint is `https://api.tokenfactory.us-central1.nebius.com/v1`. Region is configuration, not a workaround for eligibility.
- UI shows only exact `nvidia/...` IDs from the live returned catalog. No fallback model or invented ID is used. Verify the selected model's official open-license card; namespace alone is not a license audit.
- Select an appropriate affordable NVIDIA open model. The official cookbook documents `nvidia/nemotron-3-super-120b-a12b`, but this is a documentation example, not this build's configured default or evidence that it is available to a particular account.
- Accept the on-screen transmission checkbox. Only approved synthetic/public brief, the current storyboard and revision instruction are sent. Use the default plain JSON-instruction path first. Set `NEBIUS_JSON_MODE=1` only if the selected model card supports JSON mode; no automatic parameter fallback makes extra paid calls.
- Create a plan and make two revisions. Inspect trace model, endpoint, hashes, HTTP status, latency and usage. Compare against the Nebius usage console. Never share API key/account identifiers in screenshots.

## Defaults and error semantics

Maximum 1600 output tokens/attempt; 6 inference attempts/day; 45000 conservative reserved tokens/day, persisted in SQLite UTC buckets. Reservation is JSON payload UTF-8 length + max output tokens + 256 overhead; it intentionally overestimates normal input tokenization and is not a guaranteed billed-token or money estimator. Do not change limits to evade an account quota.

429 retries at most once, waiting 0.1–3 seconds from a numeric Retry-After (otherwise one second). Every retry consumes another reservation. 401/403/5xx stop immediately. A timeout/network failure is marked uncertain; you may have incurred usage, so the app never retries it automatically. Missing/invalid usage or a different returned model blocks success. Empty/malformed/truncated/tool-call output fails without applying it. Credentials and raw error payloads are never returned. Cancellation discards a result when it arrives, but cannot guarantee provider-side cancellation.

## Live acceptance gate, still unrun

Three distinct synthetic briefs, two different revisions each, successful exact NVIDIA responses and matching usage evidence; invalid-output and failure cases; actual confirmed render after approval; resulting MP4 verified and ZIP hashes valid. Keep live outputs in a separately labeled evidence directory. Do not relabel fixture/sample/mock runs as live, and do not claim contest readiness while any real-service gate remains blocked.
