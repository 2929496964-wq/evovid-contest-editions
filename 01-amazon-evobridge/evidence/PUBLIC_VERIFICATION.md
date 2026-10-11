# Public verification summary

Prepared 2026-10-11. This report summarizes recorded historical build results and distinguishes a fresh public-copy recheck. It is not a replacement raw execution log, independent certification, or live-provider attestation.

## Historical build results

17 unittest tests; 52 independent HTTP checks; 7 independent jsdom checks; clean locked install, three synthetic renders and cancellation/retry checks were recorded as passed.

These results were read from the frozen edition's status and verification reports. Raw installation/test/server output and private/internal QA artifacts were deliberately excluded from this source copy. The retained source tests allow the documented local checks to be rerun.

## Fresh public-copy check

- Executable test suite: **17 passed**, exit code 0.
- JavaScript syntax: `node --check static/app.js`, exit code 0.
- Environment: existing Linux Python 3.12 dependencies reused; no fresh package installation in this recheck.
- Scope: local/source and offline mocked-contract tests only. No live provider requests, account changes, financial transaction or external deployment.
- Executable application, launcher, test and tool files remain byte-identical to the supplied frozen edition. Only public-copy documentation/metadata and repository review tools were added or adjusted.

## Subsequent browser, demo and submission checks — 2026-10-11

- The public runtime source was inspected at commit `249ad7acf3dd248128390dbd15d93415c79a9a2e`; this status refresh changes documentation/metadata only.
- In a private Linux Codespace (2 cores, 8 GB), 17 Python unit tests and JavaScript syntax checking passed. Actual browser interaction covered storyboard edits, undo, captions, aspect ratio, render confirmation, real rendering, video playback/download, refresh persistence, JSON backup/restore, cancel/retry and repeated-request idempotency.
- The test working copy allowed only the additional exact proxy Origin `https://localhost:8711`; loopback Host and session-token checks stayed in place. This one-line adaptation was **not committed to the public runtime source**. The result does not certify an unchanged checkout under an arbitrary proxy.
- [Public Vimeo demo](https://vimeo.com/1234797768): 153-second 1080p English walkthrough edited from real browser captures. It identifies Alexa+ simulation, deterministic rules and non-neural generation. The demonstrated local output is an 11-second 960×540 motion-graphics MP4.
- Vimeo settings were Public, embeddable and All audiences; transcoding completed. Playback advanced to 34.8 seconds in the signed-in cloud browser; the Devpost embedded player advanced to 16 seconds. These are sampled playback checks, not a full-duration or anonymous playback certification. The independent anonymous check was bot-blocked.
- [Devpost project](https://devpost.com/software/evobridge-creator-assistant) showed “Project submitted!” and “SUBMITTED TO” Amazon at 12:56 UTC. A refreshed project list also showed “SUBMITTED” at 12:57 UTC. This is platform receipt evidence, not an eligibility acceptance or judging result.

## Remaining limits

Alexa+ remains a simulation; no real Alexa service, device, SDK, runtime LLM or neural video generation is implemented. Windows/macOS execution, mobile layout and personal-image upload remain unverified. A pre-2026-08-31 upstream baseline remains unavailable; no historical commit was invented. The organizer determines eligibility and judging outcomes.

The original browser-launch/access failures in the build environment remain historical results; the later bounded Linux browser run does not erase them. No fixture or DOM test is promoted to an actual cloud-inference or payment pass. No private runtime data, raw logs or internal screenshots are published with this update.

## Public artifact policy

No runtime databases, sessions/cookies, credentials, `.env`, installed virtual environments, raw run logs, internal QA screenshots or old whole-source packaging inventories are included. New generated outputs must be reviewed again before publication. The root [public manifest](../../PUBLIC-MANIFEST.json) describes this exact source copy and intentionally excludes itself from its hash list.
