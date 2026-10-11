# Four-minute demonstration script

**Target: 4:30, maximum 5:00.** Record only actual running screens. Do not show tokens, personal media, paths with secrets or AWS account details. This script is prepared; no final narrated submission video has been recorded.

## 0:00–0:25 — Problem and truth
“My small-creator workflow is EvoVid Vision Director. It turns technical video signals into reviewable editing decisions. The analysis uses real OpenCV 5. The output is real FFmpeg editing. Every final edit is approved by the person.” Briefly introduce the actual team; do not invent team members.

## 0:25–0:55 — Original input
Open http://127.0.0.1:8712. Show `OpenCV 5.0.0 · local`. Click “Try the synthetic quality lab.” State: “This is controlled generated test footage, explicitly labeled. It is not a real-world benchmark.” Play the source and show clear, dark, soft, black and changed-color intervals.

## 0:55–1:45 — Evidence changes the decision
Inspect the signal timeline and click an interval to seek the original. Explain luma, Laplacian-variance detail, black fraction, motion and histogram change. “Warnings describe pixel statistics, not creative intent.” Set target to 4 seconds. Compare “Ignore softness” with “Favor detail”; show that selected intervals change on the same input. Do not describe high motion as inherently good.

## 1:45–2:35 — Human edit and real output
Uncheck an interval if desired. On a dark interval demonstrate selecting exposure +0.20, explaining that this lifts pixels but cannot recover clipped detail. Check the human approval box and click Render. Show processing status. Play the rendered MP4 next to the untouched original, with sound. Explain that trims change their time axes. Download the output and audit bundle.

## 2:35–3:15 — Trace and recovery
Expand logs. Show `human_approved_render` followed by `render_finished`, with plan ranges and output hash. Show the JSON report/CSV. If rehearsed, start another render and cancel it; show the old successful output remains. Do not claim cancellation if the task completed first.

## 3:15–3:50 — Evaluation and failures
Open the actual evaluation summary. On the synthetic quality-lab clip, the fixed-prefix baseline has 0.5 technical-warning ratio; the measured selection has 0.0 for this run. “This is only one controlled fixture; it is not a 50% real-world accuracy claim.” Show intentional low light remaining flagged and soft background plus sharp subtitles avoiding the softness warning. Neither failure is hidden.

## 3:50–4:20 — Architecture and AWS boundary
Show `docs/architecture.svg`. Explain that the private EC2 container is designed to perform the actual OpenCV and FFmpeg computation through SSM, without public ingress. “The container and CloudFormation template are prepared. AWS deployment and billing approval are still pending. This recording demonstrates local execution only.”

## 4:20–4:30 — Close
“Evidence stays inspectable, the original stays intact, and the creator owns the final cut.” Point to source, locked dependencies and reproducible tests. Leave remaining time for actual result loading; stop before five minutes.
