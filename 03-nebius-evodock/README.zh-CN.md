# EvoDock 分镜 Agent

> Public-source copy: raw execution logs, internal QA material, runtime/session data and old source-package inventories are excluded. Historical pass/fail and live/fixture boundaries are preserved in [public verification](evidence/PUBLIC_VERIFICATION.md). The new root [manifest](../PUBLIC-MANIFEST.json) inventories this exact copy.

基于公开 MIT EvoVid 分支制作的独立本地版：创作需求 → 分镜规划 → 人工编辑和多轮修订 → 约束校验 → 用户确认 → 实际 MP4 和完整项目包。

**真实状态：本地完整流程可运行；Nebius 真实接入被阻塞，实际模型调用 0 次。** 中国真实居住地的合法服务开户、获授权凭据和费用授权尚未解决。离线夹具、HTTP mock 合同测试均不能作为参赛合格证据。

## 启动

需要 Python 3.11+、带 libx264 的 FFmpeg（PATH 可找到）。无需 GPU、模型下载、Node 或云账户。实测环境为 Linux/Python 3.12；Windows/macOS 启动器已经提供，但尚未在对应系统执行验证。FFmpeg 从 https://ffmpeg.org/download.html 的官方入口获得，本包不下载或捆绑它。

最快方式：Windows 直接双击 start.bat；macOS/Linux 运行 ./start.sh。启动器会检查 Python，首次自动创建 .venv 并安装锁定依赖；失败会保留窗口说明原因，不要求手敲安装命令。FFmpeg 仍需单独从官方入口安装。下列为可选手动方式。

Windows：

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
start.bat
```

macOS/Linux：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
./start.sh
```

打开 http://127.0.0.1:8713 。也可用 install.bat/install.sh 明确执行安装。支持 PORT 环境变量或 `python launcher.py --port 8713 --data-dir data`。默认只监听本机，数据存 SQLite 和本地文件；不公开部署。虚拟环境不应放进源码 ZIP。

## 完整离线体验

1. 选择 DEMO FIXTURE，输入虚构需求，生成实际可编辑分镜。
2. 编辑镜头标题、字幕、秒数、几何素材、动效、配色；可增删、排序并保存。
3. 修订输入 “Make it shorter”、 “Make it warmer”、 “reverse” 可执行确定性变化；其他修订文字替换最后一镜字幕。它不是 LLM，界面明确写明。
4. 查看版本记录，可把旧版本加载为新草稿再保存。
5. 点击 Confirm & render locally 并确认，产出真正 960×540/24fps 的无声 H.264 MP4。可取消；同一版本重复导出复用结果。
6. 下载 ZIP，包含 MP4、海报、SRT、分镜 JSON、完整项目/版本、trace 和 SHA-256 manifest。分享前注意包中含创作需求和编辑记录。
7. 重启后本地项目仍在。三组完全虚构样例、两轮修订、实际样片在 examples/。

DEMO FIXTURE 水印出现在样片每一帧。渲染是本地字形和几何动效，不是神经网络文生视频。中文显示需系统已安装合适字体，可设置 EVODOCK_FONT_PATH；没有捆绑字体，也没有上传私密主版记忆。

## 真实 Nebius 路径

后端实际使用 httpx：官方 GET /models → 用户选择返回的 NVIDIA 精确模型 ID → POST /chat/completions → 校验结构、模型、usage、finish_reason → 保存版本。不会猜模型 ID；不会用 NVIDIA NIM 或其他供应商替代。默认不强行启用 JSON mode；只有官方模型卡支持时才可配置。

缺 key、未授权、超时、401/403/429、非法 JSON、未知素材、负时长、越界路径、假工具、secret 回显均停止并保留已有成果，不会偷偷切换 demo 伪称成功。文本只能作为文字展示，不能执行 HTML/命令。日请求次数/保守 token 预留有上限；429 最多重试一次，超时/5xx 不自动重试有可能已计费的 POST。取消无法保证服务商端退款。

[安全配置细则](docs/provider-setup.md)：合法开户问题解决并另获凭据和运行费用授权后，可在自己的终端运行 tools/run_with_key.py，隐藏输入已有 key；脚本不创建、不保存凭据。不要在聊天中发送 key，不改填国家，不借账号，不用 VPN 绕过地区限制。地域 endpoint 不是服务准入豁免。

## 测试与交付

```sh
python -m unittest discover -s tests -v
python tools/make_samples.py
python tools/verify_package.py examples/project.zip
```

独立 QA、合同测试、本地实测、没有运行的阶段会分别报告。详见 status.json、evidence/、docs/production-readiness.md。trace 哈希链证明本地完整性，不证明 Nebius 外部账单真实性；仍需实际成功请求和 Nebius 控制台 usage 对照。

[英文 README](README.md) 含架构、运行参数、上游 provenance、隐私和限制。上游 MIT commit 为 31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe；未接触或公开 Windows 私密主版，未开户、建 key、付费调用、外网部署、上传代码或提交比赛。
