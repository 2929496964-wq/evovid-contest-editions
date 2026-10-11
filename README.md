# EvoVid contest editions

Five independent local-first prototypes derived from the public MIT [EvoVid Pocket](https://github.com/2929496964-wq/evovid-pocket) snapshot `31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`. This is a prepared public-source copy. Publication, contest eligibility, public demo availability and final submission are separate gates.

## Choose one edition

- [01 · EvoBridge Creator Assistant](01-amazon-evobridge/README.md), port 8711: bilingual Alexa+ experience simulation; deterministic local commands, no actual Alexa integration.
- [02 · EvoVid Vision Director](02-opencv-vision-director/README.md), port 8712: actual OpenCV 5 video analysis and approved FFmpeg edits. AWS deployment is prepared, not performed.
- [03 · EvoDock Storyboard Agent](03-nebius-evodock/README.md), port 8713: offline fixture workflow; Nebius/NVIDIA integration is implemented but zero live provider requests are verified.
- [04 · EvoVid Taste Director](04-qloo-taste-director/README.md), port 8714: authored synthetic Qloo-style demo data; real Qloo response data is absent and must not be published.
- [05 · EvoVid Creator Commerce](05-paypal-creator-commerce/README.md), port 8715: fictional payment fixture workflow; actual local AI inference and actual PayPal Sandbox transaction remain unverified.

Open an edition's folder and follow its README. Each contains its own source, pinned dependency lock, launchers, executable tests, license, documentation and synthetic samples. Python dependencies are installed by the user on first launch. Nebius also needs a separately installed FFmpeg executable. No model weights or installed dependency binaries are bundled.

## Verification and privacy

- [Public-source review](PUBLIC-SOURCE-REVIEW.md): exact scope, privacy/secret/asset checks and limitations.
- [Public manifest](PUBLIC-MANIFEST.json): final SHA-256 inventory, excluding the manifest itself. Run `python tools/verify_public_source.py` to check integrity and absence of excluded artifacts.
- Each edition's `evidence/PUBLIC_VERIFICATION.md` separates historical build claims from fresh public-copy checks. Raw test logs and internal QA screenshots are excluded.
- Included videos are synthetic rendered output, not recordings of a browser or proof of live cloud usage. Real-browser layout/playback, Windows/macOS execution and external-service gates remain as stated in each edition.
- Never commit credentials, `.env`, runtime databases, cookies, session records, private footage, account details or real Qloo response data.

## Licensing and attribution

The original MIT copyright and full permission notice are retained in [LICENSE](LICENSE) and every edition. See [third-party and sample notices](THIRD_PARTY_NOTICES.md) plus the edition-specific notices. Dependency licenses and provider terms remain separate. No affiliation or endorsement by Amazon, OpenCV, Nebius, Qloo or PayPal is implied.

## 中文

五个目录可独立启动。这里只包含经过整理的源码、启动脚本、依赖清单、测试、许可证与明确标注的虚构样片。真实服务调用、付款、云部署、公开视频和最终参赛提交均以各版本实际验证状态为准；本地fixture测试不等于真实集成通过。私密运行数据与原始QA日志不在公开范围内。
