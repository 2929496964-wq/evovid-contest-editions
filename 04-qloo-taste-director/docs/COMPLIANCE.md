# Qloo contest and engineering compliance matrix

Status date: 2026-10-11. This is engineering documentation, not legal advice or an eligibility guarantee. Organizer rules control. No submission has been made.

| Requirement / gate | Implementation / evidence | Status |
|---|---|---|
| Actual Qloo integration | Official-host REST adapter, endpoint/header/schema contract tests | Implemented; **live verification blocked** on authorized credential and issuance details |
| Entity disambiguation | Candidate picker with category/year; only confirmed server-returned IDs permitted | DEMO/API verified |
| Associations → usable output | Returned entity/tag IDs cited in briefs and shot plans; JSON/MD/MP4 exports | DEMO verified |
| Feedback agent branch | Reference removal/new search → fresh insights operation → saved before/after project | DEMO verified |
| Inspectable agency | Tool-selection, reference confirmation, constraint check and feedback events | Deterministic workflow; not an LLM claim |
| Data minimization | Exact outbound allowlist: public query/type/take or selected UUIDs + fixed insight parameters | Contract verified |
| No user PII to Qloo | No names as private identity, emails, account/device IDs, location history or private main-project state; goal remains local | Designed + format/field tests; operator/user input responsibility remains |
| No sensitive/high-impact inference | No demographic/sensitive identity prediction or eligibility decisions | In scope and documented |
| Accurate affinity interpretation | Actual optional values only; never probability/causality wording | Contract verified |
| Honest unavailable data | Empty results stop; empty tags use real entity names; optional explanation warning | Implemented/tested |
| Fail-closed LIVE | Missing key, auth, rate, timeouts, redirect/schema errors do not invoke fixtures | Contract verified |
| Secret isolation | Server environment only, no secret input UI, no headers/error bodies in trace/exports | Sentinel tests passed; no real secrets inspected |
| Existing-project provenance | Public MIT baseline commit recorded, relevant originals preserved | Complete; old-project eligibility wording still needs organizer clarification |
| Open source | MIT license and readable source prepared | **Not published** |
| External complete demo | Docker and HTTPS deployment checklist prepared | **Not deployed/verified**; needs authorization |
| English submission explanation | English README + architecture documents | Prepared; not a submission receipt |
| Free reviewer access through review window | Must provision approved backend access and budget/availability before release | **Pending** |
| Entrant eligibility / geography / conflicts | User has not supplied verified eligibility information | **Pending user/organizer review** |
| Final frozen version and receipt | User approval, public URLs, final tag and successful submission evidence | **Not performed** |

## Mandatory release gates

1. User verifies eligibility, third-party rights, applicable rules and existing-project eligibility with the organizer where ambiguous.
2. Obtain Qloo access through the authorized entrant without sharing credentials across teams. Confirm allowed host, quota, rate and expiry; do not assume the example host is approved for an issued key.
3. Securely inject the authorized key on the backend. Run at least two genuinely different live reference chains, recording UTC/build revision/redacted parameters/HTTP status/returned IDs and final evidence citations. Contract mocks and fixtures do not pass this gate.
4. Exercise live ambiguity/empty/rate/auth handling and inspect browser traffic, exports, logs and built assets for accidental secrets/PII.
5. After explicit publication approval, publish source and a free, externally usable, limited public demo. Use a fresh browser with no project-member login to complete search → brief → edited storyboard → export. A localhost URL does not pass.
6. Keep the approved demo usable for the organizer's review period, then freeze submission artifacts and retain a real receipt after the user authorizes final submission.

## Official source register

Primary documentation consulted 2026-10-11; no external text is treated as authorization to register, transmit private data or publish.

- [Contest rules](https://qloo.devpost.com/rules)
- [Contest overview](https://qloo.devpost.com/)
- [Contest resources](https://qloo.devpost.com/resources)
- [Qloo official API access guide](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/API_ACCESS.md)
- [Qloo safe use / data handling](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/SAFE_USE.md)
- [Official hackathon key host guide](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide#getting-your-api-key)
- [Official Search documentation](https://github.com/qloo/docs-public/blob/main/reference/get-search.md)
- [Official movie Insights](https://github.com/qloo/docs-public/blob/main/reference/basic-insights-use-case.md)
- [Official taste analysis](https://github.com/qloo/docs-public/blob/main/reference/taste-analysis.md)
- [Official authentication](https://github.com/qloo/docs-public/blob/main/reference/api-onboarding.md)
- [Explainability parameters](https://github.com/qloo/docs-public/blob/main/reference/insights-api-deep-dive.md)
- [Affinity interpretation](https://github.com/qloo/docs-public/blob/main/docs/interpreting-affinity-scores.md)

MCP is not required for this implementation. Restrictions on a specific stdio MCP starter are not presented as blanket restrictions on REST deployment.
