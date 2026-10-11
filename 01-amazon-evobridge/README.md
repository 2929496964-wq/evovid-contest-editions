# EvoBridge Creator Assistant

> Public-source copy: raw execution logs, internal QA material, runtime/session data and old source-package inventories are excluded. Historical pass/fail and live/fixture boundaries are preserved in [public verification](evidence/PUBLIC_VERIFICATION.md). The new root [manifest](../PUBLIC-MANIFEST.json) inventories this exact copy.

A local, bilingual creator studio: brief → three-scene storyboard → conversational edits → confirmed render → a real downloadable MP4.

**Alexa+ experience simulation.** This project was built with AI-assisted development tools. Its interaction layer uses bounded deterministic rules. It does not connect to the Alexa+ service, a device, an LLM, or an Alexa SDK. Storyboard edits and video rendering run locally. Video output is **motion graphics**, not neural text-to-video.

## Start in two minutes

Install **Python 3.11 or 3.12** from python.org first (tested on Python 3.12.14).

- **Windows:** double-click `start.bat`, then open **http://127.0.0.1:8711**. Keep the console open.
- **Linux / macOS:** run `bash start.sh`, then open **http://127.0.0.1:8711**.
- First launch downloads the two hash-locked Python dependencies from PyPI into `.venv`. `imageio-ffmpeg` includes the FFmpeg executable for supported Windows/macOS/Linux wheel platforms; **you normally do not need a separate FFmpeg installation**. If a system FFmpeg already exists, it takes priority. No model download, account, credentials, cloud service, or payment is needed.
- After installation, launch without reinstalling: `.venv/bin/python run.py` (Windows: `.venv\Scripts\python.exe run.py`). This works offline.
- Another port: `PORT=8801 bash start.sh` on Linux, or `set PORT=8801` before `start.bat` on Windows. Alternatively `python run.py --port 8801`.
- Stop with Ctrl+C. Reopen with the same command to restore saved projects and history. The server is deliberately bound to **127.0.0.1 only**.

### Your first story

1. Choose **The corner café**, or type **Create a project** in the assistant. Answer the theme, audience, duration (6–45 seconds), and tone prompts.
2. Type **Shorten scene 2**, then **Tone warm**. Use **Undo** if you change your mind.
3. Select a scene. Change its headline, caption, duration, animation or color, then click **Apply changes**. Arrow buttons reorder scenes. Upload your own JPEG/PNG/WebP and click its thumbnail to use it in the selected scene.
4. Choose landscape or portrait. Click **Export video**, check the revision and duration, then **Render video**. **Not yet** or Escape closes confirmation without starting a job.
5. Watch progress, play the **actual rendered MP4**, and download it. Export history includes each saved revision. Identical repeated requests reuse the same logical render.
6. **Project JSON** saves a backup; **Restore** imports it as a new project. Images are deliberately not embedded in JSON: reattach your own images after moving to another computer.

## What really works

- English / Simplified Chinese UI and a published command grammar.
- Multi-turn brief collection with cancellation, persistent projects and 20-step storyboard undo.
- Three editable scenes with per-scene duration, order, title, caption, accent, image and animation.
- Real 20 fps H.264 MP4: 960×540 landscape / 540×960 portrait, silent, local Pillow + FFmpeg rendering.
- Text entrance/fade and animated shapes; uploaded-image zoom. No generated speech, sound, stock-video retrieval or neural video model.
- Render confirmation checks the exact revision. Progress, cancellation, deduplication, failure/retry and restart interruption states are real.
- Each completed render has a JSON manifest with input snapshot and SHA-256.

The CSS preview is an **illustrative live preview**, not a pixel-identical encoding. Only the Rendered video tab shows the actual MP4. Long text is bounded and renderer line wrapping may truncate it with an ellipsis; shorten a headline/caption if needed. Tone changes the stored tone and visual palette; it does not pretend to rewrite prose intelligently. Emoji glyphs depend on installed fonts. Chinese uses Microsoft YaHei on Windows, Noto CJK on this tested Linux environment, or PingFang on macOS. Set `EVOBRIDGE_FONT` to a suitable local font if necessary.

## Supported commands

| English | 中文 |
|---|---|
| Create a project | 创建项目 |
| Cancel (while entering a brief) | 取消 |
| Shorten scene 2 | 把第2段改短 |
| Set scene 2 to 3 seconds | 第2段设为3秒 |
| Tone warm / bold / calm | 换成温暖语气 / 活力语气 / 平静语气 |
| Text 2: Your new caption | 文本2：你的新字幕 |
| Title 2: Your new headline | 标题2：你的新标题 |
| Move 3 to 1 | 移动3到1 |
| Undo | 撤回上次修改 |
| Export | 导出 |
| Help | 帮助 |

Unmatched commands return a recoverable error and keep the saved storyboard. A new brief supports 6–45 seconds; individual scenes can be edited to 1–20 seconds with a total 3–45 seconds.

## Verify, inspect and judge

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/create_evidence.py
node --check static/app.js   # optional static JS syntax check
```

The first command uses only Python's standard `unittest`; no extra test dependency. The second renders three distinct projects, performs two edits each, tests repeat/cancel/failure/retry, writes `samples/` and `evidence/render-tests.json`; if available, ffprobe additionally verifies codec, dimensions and duration. Tests require no third-party account.

- `samples/cafe.mp4`, `samples/garden-zh.mp4`, `samples/makers.mp4`: actual rendered samples, paired with input/hash JSON and decoded video frames.
- `docs/ARCHITECTURE.md`: design, security and known limits.
- `docs/JUDGING.md`: English project description, track, material changes, AI tooling disclosure and submission status.
- `docs/DEMO_SCRIPT.md`: under-three-minute English demo script with Chinese guide.
- `docs/FRICTION_LOG.md`: observed development friction, without invented Alexa SDK usage.
- `docs/TEST_REPORT.md` / `status.json`: preserved historical build results and a separately dated current-status update.
- [Public verification summary](evidence/PUBLIC_VERIFICATION.md): historical test results and staging rechecks; raw logs are excluded. `evidence/render-tests.json` retains synthetic-render measurements.

## Submission and browser verification — 2026-10-11

**Submitted to the Amazon hackathon on Devpost.** The project page showed “Project submitted!” and “SUBMITTED TO”; the refreshed project list also showed “SUBMITTED”. This confirms platform submission, not an organizer eligibility or judging decision.

- [Submitted project](https://devpost.com/software/evobridge-creator-assistant)
- [Public English demo on Vimeo](https://vimeo.com/1234797768): 2:33, 1080p, edited from real browser captures. It clearly discloses the deterministic Alexa+ simulation and non-neural motion graphics. The demonstrated local MP4 is 11 seconds at 960×540.
- A private Linux Codespace (2 cores, 8 GB) passed 17 Python unit tests and JavaScript syntax checking. Real-browser checks covered storyboard editing, undo, captions, aspect-ratio changes, render confirmation, rendering, playback/download, refresh persistence, JSON backup/restore, cancellation/retry and idempotency.
- Browser testing used a one-line, uncommitted working-copy adaptation allowing the exact proxy Origin `https://localhost:8711`; loopback Host and session-token checks remained enforced. **That adaptation is not in the public source.** This is a bounded Linux browser check, not proof that the unchanged source works through every hosted proxy.
- Vimeo was public and embeddable, finished transcoding, and playback advanced in the signed-in browser. The Devpost embed also played. Independent anonymous playback was not established because the separate check was bot-blocked.

Windows/macOS execution, mobile layout and personal-image upload remain unverified. No actual Alexa service, device, SDK or runtime LLM is implemented. Historical failures and the missing pre-event baseline are retained in [public verification](evidence/PUBLIC_VERIFICATION.md) and the test/provenance reports.

## Privacy, storage and licenses

Source code is MIT; the preserved upstream license is in `vendor/EVOVID-LICENSE`. The public upstream is [EvoVid Pocket](https://github.com/2929496964-wq/evovid-pocket), snapshot `31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`. `evobridge/job_store.py` is reused from its desktop SQLite store; renderer concepts were adapted, and the web application, command state machine and project workflow were added here. See `docs/PROVENANCE.md` for the exact baseline limitation.

Only synthetic sample text and programmatic shapes are included. No personal photographs, credentials, model weights, paid API access or private EvoVid data are included. System fonts are not redistributed. Dependency licenses remain separate; see `THIRD_PARTY_NOTICES.md`.

Projects, imported sanitized images, jobs and exports are in `data/` next to `run.py` (or your explicit `--data` directory). HTTP clients cannot select filesystem paths. This package does not publish, upload or submit anything. Do not expose the development server to the internet.

---

# 中文使用说明

**EvoBridge是Alexa+网页模拟体验，不接入真实Alexa+服务或设备。** 使用AI辅助开发；运行时采用明确、有限的确定性规则，不假装大模型。真正的项目修改和MP4渲染在本机完成。视频是文字、几何图形和可选图片组成的动效，**不是神经网络文生视频**。

## 启动

1. 先安装Python 3.11或3.12（本次实际测试3.12.14）。
2. Windows双击`start.bat`；Linux/macOS运行`bash start.sh`。
3. 打开 **http://127.0.0.1:8711**，保持命令窗口运行。端口可通过`PORT`环境变量或`--port`参数更改。
4. 首次启动会从PyPI安装固定版本、校验hash的Pillow和imageio-ffmpeg。后者在支持的平台自带FFmpeg，通常无需另外安装。已有系统FFmpeg优先使用。无需账号、API密钥、模型下载或付费。
5. 安装后可直接运行`.venv\Scripts\python.exe run.py`（Windows）或`.venv/bin/python run.py`（Linux/macOS），完全离线使用。Ctrl+C退出，重开自动恢复项目与历史。

## 创作与导出

点击右上“中文”切换界面。选示例或输入「创建项目」，依次填写主题、受众、时长、语气。输入「把第2段改短」「换成温暖语气」「撤回上次修改」可真正修改分镜数据。点击分镜，在右侧编辑标题、字幕、时长、色彩和动效；箭头可调整顺序；上传自己的图片后点击缩略图即可应用。

点击「导出视频」，检查版本与时长后确认。关闭确认框不会开始渲染。进度完成后可播放、下载真实无声H.264 MP4，同时获取包含输入快照与SHA-256的JSON证据。重复点击复用同一个逻辑渲染。可取消正在运行的任务，失败可重试。重新打开应用会恢复已保存分镜；中断的渲染明确标记为interrupted，不假装完成。

「项目JSON」可备份分镜，「恢复」会导入为一个新项目。为避免隐式文件访问，JSON不嵌入图片，跨机器恢复时需重新添加自己的素材。视频预览中的CSS动效仅供编辑参考，实际MP4请看「实际导出」页。

## 当前验证边界

2026-10-11已完成Amazon的Devpost正式提交，平台显示“Project submitted!”并在刷新列表后显示“SUBMITTED”。[作品页](https://devpost.com/software/evobridge-creator-assistant)与[2分33秒英文演示](https://vimeo.com/1234797768)已公开。私人Linux Codespace中的真实浏览器已验证分镜编辑、撤销、字幕、画幅、渲染、播放/下载、刷新持久化、备份恢复、取消重试和幂等，17项Python单测及JS语法检查通过。测试工作副本只增加精确代理Origin白名单，未提交到公开源码；loopback Host和session-token检查仍保留。演示由真实浏览器画面剪辑而成，明确说明确定性Alexa+模拟及非神经动效。Windows/macOS实机、移动端和个人图片上传仍未验证；独立匿名播放被bot检查阻断，不能声称已通过。平台提交成功不代表主办方已确认资格或评审通过。旧测试历史及缺失的赛前基线限制仍保留。

该目录与其他参赛版本隔离。源码MIT开源，保留公开EvoVid上游版权；不含私人主版、密钥、私人素材或模型权重。完整英文材料见docs目录，中文操作可对照上面的双语命令表。
