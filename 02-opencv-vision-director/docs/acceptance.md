# Acceptance truth (2026-10-11 UTC)

| Area | State | Evidence / limitation |
|---|---|---|
| OpenCV 5 installed in isolated Linux environment | Passed | Runtime 5.0.0, wheel 5.0.0.93, recorded official SHA-256 match; public summary and wheel hash retained |
| Real input decode and metric computation | Passed | 5 generated input MP4s plus independent QA fixture; stored timestamps/metrics |
| Parameter changes selection and actual output | Passed | `evidence/evaluation/parameter-causality.json` and two distinct rendered MP4 hashes |
| Explicit human gate; no unapproved render | Passed | HTTP tests; boolean true required; UI edits revoke approval |
| MP4 render, audio, output duration and hashes | Passed locally | System FFmpeg and bundled-FFmpeg fallback tested; H.264/AAC independent QA |
| Cancellation, duplicate clicks, recovery | Passed locally | Independent HTTP QA and atomic operation locking |
| Original and failed attempt preservation | Passed locally | Historical hash/cancellation checks summarized; raw execution logs excluded |
| Five different evaluation inputs | Passed for synthetic tests only | Generated graphics with license/provenance manifest; no real-user dataset |
| Baseline comparison and failure cases | Passed for controlled evidence | Actual JSON/CSV results; low-light false positives, subtitle-masked soft background false negatives |
| Human preference and cut-quality study | Not run | Fields are null, never fabricated |
| Mobile-responsive WebUI | Implemented | Responsive CSS, accessible labels, bounded controls; actual visual rendering not verified due environment restriction |
| DOM/API interaction | Passed, nonvisual | 8 local and 6 independent checks; synthetic demo, recommendation, approval, actual render, logs and approval invalidation |
| Actual browser screenshot / full-browser automation | Blocked | Chromium socket creation prohibited in the build environment; blocked status retained, raw failure log excluded |
| Windows start.bat | Prepared, not run | Requires a separate Windows machine test |
| Docker container build | Prepared, not run | Docker daemon unavailable here; bundled media runtime tested outside Docker |
| AWS compute | Prepared, not deployed | No account, permissions, region, spending or resource approval supplied |
| AWS job evidence / costs | Blocked | Must be collected on an authorized deployment; current local results are not AWS proof |
| Organizer eligibility / public demo / submission | Not done | No contest registration, upload, public deployment or submission performed |

No row marked “prepared” or “blocked” is a completed contest-compliance claim. The full previously researched competition checklist remains stricter than this local artifact acceptance.
