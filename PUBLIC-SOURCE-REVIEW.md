# Public-source preparation review

Prepared 2026-10-11. Scope: the exact files listed in PUBLIC-MANIFEST.json. This is a local staging review, not evidence that a repository, deployment, public video or competition entry has been published.

## Included

Five independent edition folders with application code, static UI, launch/install scripts, dependency locks, complete MIT attribution, technical/setup/demo-script documentation, reproducible offline tests, and clearly labeled synthetic samples. OpenCV retains synthetic comparison measurements, final comparison MP4s and approved plans. Nebius retains its unchanged fictional sample project archive and valid internal manifest. Qloo contains authored fixtures only, never a real Qloo response dataset.

## Excluded

- All original Git histories, installed environments, wheel/package caches and native dependency binaries
- Runtime databases/ledgers, runtime media stores, session/cookie data, credentials and populated secret files
- Raw install/test/server/FFmpeg logs, process IDs, internal QA material and internal QA screenshots
- Original whole-source manifests and packaging allowlists that would no longer describe this copy
- Intermediate OpenCV clip fragments and runtime audit exports; final controlled comparison outputs remain
- Private cloud workspace paths, private download URLs and personal source materials

Reviewed `.env.example` files contain empty credential fields only. Application code legitimately contains names of environment variables, auth headers and runtime session-handling logic; these are not saved credentials or sessions.

## Verification

The fresh source-copy suites passed: Amazon 17, OpenCV 18, Nebius 30, Qloo 18, PayPal 23, totaling **106 tests**. All five JavaScript syntax checks passed. The recheck reused existing Linux Python 3.12 dependency environments; it did not perform a clean reinstall, browser visual test or real provider call. See each edition's evidence/PUBLIC_VERIFICATION.md for separately identified historical tests and current unverified boundaries.

101 copied executable/application/configuration files were byte-compared against the frozen inputs with no changes. All 64 Python files, including the added root verifier, parsed successfully. The original frozen edition directories and existing delivered archives were not edited.

The supplied `tools/verify_public_source.py` verifies SHA-256 and byte counts against the exact new manifest, checks for unreviewed files and excluded artifact types, scans selected high-confidence secret/private-path patterns, verifies the nested sample archive and checks local Markdown links. The manifest excludes itself to avoid a circular hash.

Manual text review also covered credential-like assignments, URL tokens, email/phone-shaped test values, JSON sample fields, font/media metadata and nested archive contents. Credential-like strings remaining in tests are explicit synthetic sentinels such as TEST-ID, TEST-SECRET and SYNTHETIC_TEST_KEY; reserved example domains and fictional negative-test inputs are deliberate. No usable credential, observed personal identity, runtime session record or private workspace path was identified in the final tree. This bounded check cannot guarantee absence of every possible secret or vulnerability.

## Asset and license findings

Complete upstream MIT text and original copyright are preserved. Claimed unmodified upstream files match the inspected public baseline. Sample images/videos are authored procedural compositions with retained synthetic/fixture labels; no third-party footage, music recording, model weights or font files were identified. Inspected MP4 metadata contains encoder/container fields and inspected PNGs contain no identifying text/EXIF. See THIRD_PARTY_NOTICES.md and each edition's notices.

The unchanged Nebius sample ZIP is covered here by the surrounding repository license. Its internal manifest correctly describes its archive entries. Separate distribution should use a newly regenerated archive containing the full license and updated internal manifest.

## Later Amazon-only status update — 2026-10-11

The Amazon edition now has a [submitted Devpost project](https://devpost.com/software/evobridge-creator-assistant) and [public English Vimeo demo](https://vimeo.com/1234797768). Its later Linux browser coverage, uncommitted exact-Origin working-copy adaptation, sampled playback checks and remaining limits are documented in [Amazon verification](01-amazon-evobridge/evidence/PUBLIC_VERIFICATION.md). This documentation/metadata refresh does not change executable source or the other four editions. The original staging review and test results above remain historical records.

## Original release gates (historical; later Amazon status above)

- Explicit owner authorization for the public repository, exact audience and source scope
- Verified public repository/commit and user/judge access after publication
- Actual target-browser/layout/playback and Windows/macOS checks where currently unverified
- AWS deployment, Nebius/NVIDIA live access, Qloo live access, actual local AI and actual PayPal Sandbox workflows as applicable
- Applicable entrant eligibility, existing-project rules, public demo-video requirements and final submission

Publication of this source alone does not satisfy those gates. No existing “unverified,” “fixture,” “simulation,” “not deployed” or “not submitted” result is promoted to a pass.
