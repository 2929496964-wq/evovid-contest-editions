# Production and contest readiness

## Verified locally

- [x] Brief→fixture plan→manual editor→save→successive revision→confirmed real render→preview/export.
- [x] Persistent SQLite history, optimistic concurrency, active-job deduplication, exact-revision render reuse, explicit cancellation and retry.
- [x] Synthetic sample media, schema boundaries, current project's safe trace, ZIP SHA-256 manifest.
- [x] Actual HTTP client with offline contract responses: discovery, success, timeout, 401/403, 429 bounded retry, 5xx, malformed JSON/envelope, wrong model, bad usage, tool calls, invalid assets/durations/paths, secret echo, budget exhaustion.
- [x] Cross-origin mutation guard, body bounds, no arbitrary provider endpoints, no file-upload/execution route.
- [x] English/Chinese instructions, exact Python dependency pins, Linux launch exercised, Windows/macOS scripts supplied.

## External blockers / explicitly not done

- [ ] Official lawful Token Factory access for the user's true residence/country.
- [ ] Account/terms/credential creation and runtime budget approvals where required.
- [ ] Actual server-side authorized key. No key is bundled or requested in chat.
- [ ] At least one actual NVIDIA open-model response via Nebius; zero live requests so far.
- [ ] Three live briefs and two revision styles, sample counts, exact model and usage-console corroboration.
- [ ] Official selected model license/card review and feature compatibility verification.
- [ ] Independent region/account eligibility and current competition-rule confirmation.
- [ ] Authorized public open-source repository and a freely testable demo/build through the review period.
- [ ] Under-three-minute public YouTube English/English-subtitled demonstration, feedback and actual submission.

## Before production/multi-user hosting

- [ ] Real authentication/authorization, CSRF/session model, HTTPS and managed secret handling.
- [ ] Persistent billing hard limits and monitoring; exact price catalog/account balance reconciliation.
- [ ] Encryption/retention/deletion controls for project text and local artifacts.
- [ ] Stress, recovery, large-history storage, database migration, capacity and race fuzz tests.
- [ ] Reproducible clean-install validation on Windows and macOS; supported system FFmpeg verification per platform.
- [ ] Dependency vulnerability/license audit and a fully hash-locked multi-platform dependency supply-chain manifest.
- [ ] Accessibility audit, international text/glyph coverage, longer-content typography and renderer visual QA.
- [ ] Real-provider quality evaluation and regression set. Deterministic fixture success does not measure model quality.

Do not expose the local server to the Internet or call this production-ready. No paid hosted infrastructure, external deployment, credential creation, model downloads or publication were performed.
