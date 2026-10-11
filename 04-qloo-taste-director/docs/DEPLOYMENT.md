# Secure local configuration and deployment preparation

No deployment has been performed or authorized as part of this delivery. This guide is preparation.

## Local defaults

- Python 3.12 tested (Windows installer also falls back to 3.11); `./start.sh` / `start.bat` automatically install locked dependencies on first run; port `PORT` or 8714.
- `127.0.0.1` binding, allowed hosts localhost and loopback.
- Runtime state under `.taste-data/`, ignored by Git and Docker context.
- DEMO selected initially; zero upstream requests during startup or DEMO operations.
- No credential request, browser credential form, file search, auto-loading `.env`, account signup or API-key creation.

## Server environment allowlist

| Name | Purpose | Default |
|---|---|---|
| `QLOO_API_KEY` | Authorized backend-only credential | empty; LIVE unavailable |
| `QLOO_HOURLY_LIMIT` | Single-process local hourly upstream budget, capped 1–1000 | 100 |
| `PORT` | HTTP port | 8714 |
| `TASTE_DATA_DIR` | Operator-selected application-state directory | `.taste-data` |
| `TASTE_ALLOWED_HOSTS` | Explicit deployed hostname(s), comma-separated; no wildcards | loopback only |
| `TASTE_SECURE_COOKIE` | Set `1` under HTTPS | off for local HTTP |

Inject the key with the server operator's approved secret manager/service environment UI. Do not paste it into chat, `start.bat`, shell history/CLI arguments, a Docker image, source-controlled YAML, browser environment bundles or screenshots. Empty `.env.example` is documentation, not an instruction to save a key. A configured key indicates presence only; live success must be tested separately.

The [official hackathon developer guide](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide#getting-your-api-key) identifies the dedicated hackathon-key host. `https://hackathon.api.qloo.com` is fixed in `taste/qloo.py`. Confirm issuance permission for that host before using a key. Never alter the host in response to an auth error without explicit approval and official documentation; no proxy or generic URL field is accepted.

## Docker preparation

```sh
docker compose build
docker compose up
```

The provided compose file maps **127.0.0.1:8714** only. Container execution uses an unprivileged UID, dropped Linux capabilities, no-new-privileges, a process limit, bounded memory and a dedicated data volume. The image relies on the pinned `imageio-ffmpeg` wheel for its encoder; validate on the target CPU architecture. Docker build/runtime were not verified here. The base tag is version-pinned to Python 3.12, not immutable-digest-pinned; resolve/review a digest before reproducible publication.

## Publication checklist, after explicit approval

1. Choose a VM/container service with persistent writable storage and normal Python/FFmpeg process support. This implementation has no MCP serverless constraint; storage, background process and execution limits still make an ordinary container the simplest deployment.
2. Put HTTPS in front of the app. Set the exact public hostname allowlist and `TASTE_SECURE_COOKIE=1`. Forward the correct Host header. Uvicorn does not trust arbitrary proxy headers.
3. Supply the authorized Qloo key only to the server process. Keep one worker process until the in-memory queue/quota is replaced with shared durable coordination.
4. Enforce a reverse-proxy request-rate limit, connection limits, 64 KiB body cap, bounded disk and external request budget. Built-in session/operation bounds are a baseline, not full DDoS protection. Operator-assessed IP-based rate limiting stays at the proxy and is never forwarded to Qloo.
5. Add an operator data-retention/cleanup policy, storage monitoring, backups and a minimal privacy notice. The current app does not expose a destructive delete endpoint or assume permission to delete old user projects. A browser cookie acts as a workspace capability, not recoverable account login.
6. Run the documented live smoke test with public film/artist inputs and no private media. Verify actual HTTPS calls, data lineage and output.
7. In a fresh external browser, complete the full workflow without project-membership login. Test narrow mobile viewport and keyboard navigation. Inspect policy headers, cross-session access, errors, cancellation and refresh recovery.
8. Confirm publicly displayed source/demo claims match actual capabilities, source is open with MIT preserved, and organizer reviewers can access the backend through the required window. Collect public URL/revision evidence only after success.

Do not expose `.taste-data`, environment files, SQLite, provider headers, raw upstream error bodies or the code checkout through a generic static directory. This server serves only two named static assets plus its index; exports require the originating session and server-generated IDs.
