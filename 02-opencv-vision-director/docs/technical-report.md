# EvoVid Vision Director: explainable, human-approved video repair

Date: 2026-10-11 UTC. Development artifact, not a claim of competition submission or organizer acceptance.

## 1. Problem and intended user

Small creators often have short clips with black intervals, dark exposures, accidental softness or distracting camera motion. A blind automatic cut can remove intentional atmosphere. Vision Director therefore makes technical evidence inspectable and requires human approval before applying a selected edit. The target is one creator reviewing up to three minutes of footage on a private workstation.

The implemented deliverable is a complete FastAPI-served web interface: file upload, recent-session recovery, source/output players, warning timeline, target-length and sharpness controls, per-interval selection and bounded exposure/sharpening choices, approval gate, render status, cancellation, and report downloads. No paid provider or model download is required.

## 2. Provenance and contribution

The project extends the public MIT EvoVid Pocket source snapshot `31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`. A preserved `desktop/evovid/vision.py` supplies the strict OpenCV 5 version guard. Earlier EvoVid's quality-analysis precedent is acknowledged. The temporal review workflow, actual user-directed edit pipeline, detailed metrics, job state/recovery, bounded renderer, new web UI, controlled evaluation and private AWS deployment design were implemented for this independent version. Other variants and the supplied upstream were not modified. AI coding assistance was used.

## 3. Architecture and actual data flow

See `architecture.svg`.

1. Browser uploads bytes through a streaming HTTP endpoint. The server assigns a random job directory. The original filename is only a display label. Size and free-space limits are checked.
2. One bounded worker sequentially decodes the actual source using OpenCV 5. Approximate four-Hz sample instants retain decoded frame number, decoder timestamp and explicit frame-index fallback provenance where necessary. Thumbnails are stored approximately once per second.
3. Raw sample metrics become one-second review bins. A deterministic quality ranking proposes clips under the requested target length; their order remains chronological. Every selected and excluded bin gets traceable reasoning.
4. The user edits inclusion, exposure and sharpening and explicitly approves. The server requires a literal boolean `true`, validates all numeric bounds, checks chronological non-overlap and atomically reserves an attempt. Concurrent duplicate render requests are rejected.
5. FFmpeg trims the selected intervals and applies only approved adjustments. The first audio stream is retained when present and encoded to AAC; silent inputs work. H.264/yuv420p output is assembled, decoded again and checked against the expected duration tolerance.
6. Original and output hashes, version evidence, analysis, approved ranges/filters, per-attempt FFmpeg arguments/logs and operation events are retained. JSON, CSV and an audit ZIP are downloadable. The audit ZIP excludes media by default; the original and output have separate endpoints.

Files survive process restarts. Active jobs found at startup become `interrupted`, never success. The user chooses to retry. Cancellation sets a per-job event checked in decode loops and while supervising FFmpeg; FFmpeg is terminated and then killed after a bounded grace period if needed. Prior successful outputs remain available.

## 4. OpenCV 5 implementation and evidence

The isolated environment actually imported:

- Python 3.12.14, Linux x86_64
- Distribution `opencv-python-headless==5.0.0.93`
- Runtime `cv2.__version__ == 5.0.0`
- NumPy 2.3.5
- System FFmpeg 7.1.5-0+deb13u1
- Bundled fallback from `imageio-ffmpeg==0.6.0`: FFmpeg 7.0.2-static, exercised by a separate render test

The downloaded Linux manylinux_2_28_x86_64 wheel SHA-256 is `ed709fdf9aa0bd1f2ed8549e71d19449b03a675bb581eb292285f6861953be37`, matching the official PyPI release metadata. The Windows wheel's hash is different and is not substituted. The package version's `.93` suffix is distribution metadata; the underlying OpenCV runtime version is `5.0.0`.

The [public verification summary](../evidence/PUBLIC_VERIFICATION.md), `../evidence/wheel-sha256.txt`, and `../requirements.lock` retain the recorded runtime/version and wheel provenance. Raw install/build/download logs and machine-specific paths are excluded from public source. Startup invokes the inherited strict major-version guard. No OpenCV 4 run is relabeled as 5. AWS must generate its own runtime evidence after deployment; this Linux evidence does not establish AWS or Windows success.

### Metric definitions

Frames are resized while preserving aspect ratio, with width capped at 480 pixels. OpenCV converts BGR to grayscale. Measurements are deterministic for the decoded pixels:

| Signal | Calculation | Current heuristic |
|---|---|---|
| Exposure | Mean grayscale value, 0–255 | Underexposure if mean <40 unless black |
| Black | Fraction of pixels <12 | Black if fraction >0.95 |
| Highlight clipping | Fraction of pixels >245 | Overexposure if fraction >0.70 |
| Detail | Variance of 64-bit Laplacian | Soft warning if <65 |
| Motion | Mean absolute difference from prior sampled grayscale frame | Review if >35; never rewarded as inherently good |
| Scene change | Bhattacharyya distance of 32-bin normalized grayscale histograms | Informational candidate if >0.55 |

One-second bins average metrics. The quality score is `50 − 0.15×abs(luma−120) − 100×black_fraction − 50×white_fraction + sharpness_weight×min(50, 8×log(1+sharpness))`. This is an explicit hand-designed heuristic, not learned accuracy or semantic quality. The selected set is ranked by this score and then sorted by source time. A final partial bin meets the requested target duration. No face recognition, identity inference or content-understanding model is used.

### User-controlled transformations

Exposure is an FFmpeg brightness offset bounded to [−0.25, +0.25]; the UI offers a smaller fixed menu. Gentle sharpening uses `unsharp=5:5:0.5:5:5:0`. These transformations cannot reconstruct lost detail. Clip time ranges and all parameters are written to the approved plan. User strings never enter shell evaluation or arbitrary FFmpeg filter syntax.

## 5. Evaluation: observed results, not a promotional claim

Five authored synthetic videos are shipped with exact generator/provenance/hash metadata: quality lab, intentional low light, soft background with sharp overlay, all black and scene cuts. They contain no downloaded third-party footage. All-black pixels deliberately omit an embedded label so the metric is honestly testable; filename and manifest provide the synthetic label.

Each input was analyzed and actually rendered twice: a fixed first-four-seconds baseline (or the full three-second black sample) and a quality-ranked four-second edit. Final comparison outputs, approved plans and numeric measurements are retained in `../evidence/evaluation/`. Execution logs and intermediate clip fragments are excluded from this public copy. A technical-warning ratio counts sampled frames flagged black, underexposed, overexposed or soft. It is **not** viewer satisfaction or objective filmmaking quality. A low-change ratio and histogram jump count are also recorded, with explicit definitions. Human preference and cut-quality ratings are null because no human study took place.

| Synthetic input | Baseline warning ratio | Vision warning ratio | Interpretation |
|---|---:|---:|---|
| All black | 1.0 | 1.0 | No good interval exists; selection cannot invent one |
| Intentional low light | 1.0 | 1.0 | Creative intent is falsely treated as a technical warning |
| Quality lab | 0.5 | 0.0 | This controlled input benefits from avoiding dark/black intervals |
| Scene cuts | 0.0 | 0.0 | No exposure/softness warning improvement was needed |
| Soft background + sharp overlay | 0.0 | 0.0 | Important false negative: global edge energy from subtitles masks soft imagery |

Per-run times are in the JSON/CSV. On this small 640×360 corpus, recorded renders were approximately 0.37–0.42 seconds for the single-range baseline and 0.65–0.84 seconds for the multi-range selection; these timings are one machine's small tests, not throughput promises. The raw values, rather than a fabricated improvement percentage, are authoritative.

### Causal parameter check

On the same twelve-second quality-lab input with target four seconds:

- Sharpness weight 0 selected intervals 4, 5, 8 and 9. Actual rendered SHA-256: `4bfb2d9abc49b8f483618f921efe8da46aa75ac3f0c56891c9a0fff998791d31`.
- Sharpness weight 4 selected intervals 0, 1, 8 and 9. Actual rendered SHA-256: `b10f589b2072dc9c38fa5d9940e94efea40784e018b0333e6d14b9977a7724e5`.

Both outputs decode to four seconds. The parameter affected actual selected source content and rendering, not only a UI label. `parameter-causality.json` and the two MP4 files retain the evidence.

### Failure cases retained

1. Intentional low-light scenes remain warned even when aesthetically correct. Human approval is the guard against removing creative intent.
2. Sharp labels/subtitles inflate a whole-frame Laplacian metric, causing blurred background content to escape the softness threshold. Region-aware metrics and authored real-world calibration are future work.
3. An entirely black input stays black. Neither selection nor exposure should be sold as recovery of missing content.

Sparse sampling can miss sub-quarter-second defects. Abrupt lighting can resemble a scene cut. Global frame differences mix object motion, camera movement and lighting. VFR, audio layouts beyond the first stream, HDR/color-management, rotation edge cases and a broad codec matrix remain limitations requiring manual checks.

## 6. Testing and verification boundaries

Local tests include 18 core tests (metric direction, true version, invalid media, cancellation, invalid numeric ranges and approvals, actual exposure increase after rendering, and silent input using bundled FFmpeg). The 16-check HTTP workflow validates original hashes, invalid input, approval, duplicate requests, playable decoded output, duration, output hashes, exports and Origin/Host boundaries.

A separate reviewer ran 23 HTTP checks on another self-generated eight-second black/soft/clear source with audio, including simultaneous duplicate render requests, one-attempt allocation, H.264/AAC streams, duration, cancellation preserving the original/prior successful output and restart behavior. Its historical result is summarized in [public verification](../evidence/PUBLIC_VERIFICATION.md); raw HTTP output is excluded. Three additional independent upload checks rejected remote HLS, file-concat playlists and plain URL content before analysis; see `evidence/independent-container-security.json`. Eight additional local DOM/API checks and six independent DOM checks used the real local HTTP backend; this verifies control/event/data flow, not layout or video playback.

Real Chromium launch was attempted but the execution environment prohibits the required local socket creation; permitted execution escalation did not resolve it. The blocked status is retained in [public verification](../evidence/PUBLIC_VERIFICATION.md); the raw environment failure log is excluded. Responsive CSS and a browser script are provided, but no screenshot or actual full-browser interaction pass is invented. Windows and Docker remain unrun.

## 7. AWS component and deployment boundary

The optional deployment runs the same processing image on private EC2, so AWS would perform the real OpenCV and FFmpeg work. The cloud component is substantial compute, not merely static hosting or an S3 logo. The frontend would reach it through an SSM port forward; there is no silent local fallback. A disconnected tunnel is a failure.

`Dockerfile` uses a non-root UID. `deploy/private-ec2.yaml` defaults `EnableCompute` to false. Enabling after separate approval provisions a private instance and scoped IAM role, IMDSv2, encrypted EBS, no public IP/inbound security-group rules and constrained Docker runtime. ECR image digest is required. Credentials are not embedded; the instance uses temporary role credentials. A per-deployment application token is generated only when the authorized template is actually run. Detailed deployment, cost review, stop and retained-resource cleanup instructions are in `deploy/README.md`.

**No AWS resources were created, image uploaded, IAM permission granted, bill incurred by deployment, cloud job run or AWS validation claimed.** Docker is unavailable in this environment, so its build is prepared rather than verified. Actual AWS account, region, image digest, runtime OpenCV build, job logs, hashes and cost evidence must be collected after explicit approval. The existing private VPC/subnet and SSM/ECR/package connectivity are operator prerequisites.

The template retains data-bearing compute/storage instead of deleting user media unexpectedly. Stack deletion therefore does not necessarily end costs. Operators must explicitly stop compute and inventory retained EBS/ECR resources. Cost caps and cleanup are operational responsibilities, not guaranteed by a template label.

## 8. Responsible use and limitations

Users should process only footage they may use. Inputs remain private and original bytes remain intact. No inference of identity or other personal attributes is performed. Do not publish `runtime/`, access tokens, personal media or account details. A shared-token, single-user design is unsuitable for public multi-tenant access. Repeated real-world calibration and stronger authenticated isolation would be necessary before production service deployment.

This is a deterministic analysis-and-review workflow. It does not claim the contest's Agentic Vision or COOL special-award criteria. The prepared work does not settle eligibility, grant-application interpretation, organizer deadline conflicts, public-demo access or final submission requirements.

## 9. Primary sources

- OpenCV wheel and checksums: https://pypi.org/project/opencv-python-headless/5.0.0.93/
- OpenCV official release: https://github.com/opencv/opencv/releases/tag/5.0.0
- OpenCV installation guidance: https://docs.opencv.org/5.0/py_tutorials/py_setup/py_pip_install/py_pip_install.html
- FFmpeg filter documentation: https://ffmpeg.org/ffmpeg-filters.html
- AWS EC2 CloudFormation: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ec2-instance.html
- AWS SSM session start: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html
- AWS temporary role credentials: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_use-resources.html

These links explain components; only the local evidence files establish what was actually run here.
