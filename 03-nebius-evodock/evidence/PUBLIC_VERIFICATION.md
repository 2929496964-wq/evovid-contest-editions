# Public verification summary

Prepared 2026-10-11. This report summarizes recorded historical build results and distinguishes a fresh public-copy recheck. It is not a replacement raw execution log, independent certification, or live-provider attestation.

## Historical build results

30 unittest tests; 20 independent HTTP checks; 4 body-boundary checks; 10 independent DOM checks; missing-FFmpeg status check. Three fictional briefs, actual local FFmpeg output and project ZIP trace/hash verification were recorded. Launcher testing reused inherited packages, not a pristine internet dependency install.

These results were read from the frozen edition's status and verification reports. Raw installation/test/server output and private/internal QA artifacts were deliberately excluded from this source copy. The retained source tests allow the documented local checks to be rerun.

## Fresh public-copy check

- Executable test suite: **30 passed**, exit code 0.
- JavaScript syntax: `node --check static/app.js`, exit code 0.
- Environment: existing Linux Python 3.12 dependencies reused; no fresh package installation in this recheck.
- Scope: local/source and offline mocked-contract tests only. No live provider requests, account changes, financial transaction or external deployment.
- Executable application, launcher, test and tool files remain byte-identical to the supplied frozen edition. Only public-copy documentation/metadata and repository review tools were added or adjusted.

## Still unverified or blocked

Zero live Nebius calls. Lawful service access, authorized credential/runtime spending, exact NVIDIA model and usage-console evidence remain absent. Windows/macOS, real-browser visual/playback and pristine install are unverified. Hash chains establish local integrity only.

No fixture or DOM result is a real-browser, actual cloud-inference or actual payment pass. Public repository availability, demo hosting, entrant eligibility and final competition submission require their own verified steps.

## Public artifact policy

No runtime databases, sessions/cookies, credentials, `.env`, installed virtual environments, raw run logs, internal QA screenshots or old whole-source packaging inventories are included. New generated outputs must be reviewed again before publication. The root [public manifest](../../PUBLIC-MANIFEST.json) describes this exact source copy and intentionally excludes itself from its hash list.
