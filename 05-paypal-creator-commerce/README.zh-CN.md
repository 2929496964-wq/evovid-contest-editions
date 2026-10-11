# EvoVid 创作者商业版 · PayPal Sandbox

> Public-source copy: raw execution logs, internal QA material, runtime/session data and old source-package inventories are excluded. Historical pass/fail and live/fixture boundaries are preserved in [public verification](evidence/PUBLIC_VERIFICATION.md). The new root [manifest](../PUBLIC-MANIFEST.json) inventories this exact copy.

虚构创作需求 → 本地 AI 生成可编辑分镜 → 真实视频预览 → 服务端定价 → Sandbox 测试付款 → 核验完成后导出 MP4。

## 先说当前状态

这是完整的本地开发版，**尚不能声称可参赛提交**。默认离线规划为 **DEMO FIXTURE，不是真实 AI**；付款为 **TEST FIXTURE，非PayPal真实支付**。真实本地 OpenAI-compatible 调用适配器、PayPal Sandbox REST 适配器均已实现并有离线契约测试，但本环境没有执行真实模型推理或真实 Sandbox 买家交易，也没有创建任何凭据或账户。

附带视频是程序实际生成、可播放的动效 MP4，不是神经网络生成的真人素材，也不是实际浏览器界面录像。受环境限制，浏览器引擎/手机视觉与 Windows 启动未实测，详见 `status.json`。

## 安装启动

- 需要 Python 3.11 或以上。首次安装依赖需要网络，不会下载模型。
- Windows：双击 `start.bat`。若找不到 Python，先从 python.org 安装，并勾选加入 PATH。
- Linux/macOS：终端执行 `bash start.sh`。
- 浏览器打开 http://127.0.0.1:8715 。不要关闭启动窗口；Ctrl+C 停止。
- 端口可通过 `PORT` 环境变量或 `.env` 修改。默认仅绑定本机回环，不对局域网或公网开放。
- 已安装后可以直接运行 `.venv/bin/python launcher.py`；Windows 为 `.venv\Scripts\python.exe launcher.py`。

## 离线完整体验

1. 输入虚构品牌需求，保留 DEMO fixture 选项，生成分镜。
2. 调整标题、字幕、时长和颜色，保存新修订。点击 Render preview，得到真实 360×640 带水印 MP4。
3. 打开标明 TEST FIXTURE 的模拟付款。价格由服务器固定为 USD 4.99，每次仅对应当前项目的一个修订。
4. 测试 PENDING、DECLINED、错误金额/币种/商户/订单/项目引用，导出仍锁定。错误核验 REJECTED 是永久拒绝，换一个新项目测试正常流程。
5. 选择“Completed, response lost”模拟成功后响应丢失，再点 Verify existing order。服务器用同一个订单恢复权益，不创建另一笔订单。
6. 匹配且 COMPLETED 后，导出真实 720×1280、12fps、无音轨 MP4。模拟导出的画面带有明确 TEST FIXTURE 标记。
7. 刷新/重启后继续使用同一个浏览器、同一个域名，可恢复项目、订单与权益；编码失败可以重试，不再购买。

项目可下载 JSON，也可恢复 JSON。恢复仅带回创作内容，绝不导入付款权益。修改已购买的项目会创建新修订，新修订仍需自己的有效权益。

## 接入用户已有的本地 AI

将 `.env.example` 复制成 `.env`。填入已经运行的本地服务 `AI_BASE_URL`（例如 http://127.0.0.1:8081/v1）和实际 `AI_MODEL`，重启后选 My local AI model。若已有本地密钥，只在自己的 `.env` 填写，不发聊天、不放源码或录像。

适配器实际调用 `/chat/completions`；模型返回的分镜标题、字幕、时长、色彩直接进入时间线和导出。响应必须通过结构和长度校验，不能携带执行命令/文件路径。模型不可用时会明确报错，绝不偷偷切换模板。此版本只允许本地回环端点，不启用远程收费接口，不自动下载/启动模型。

## PayPal Sandbox

详见 [沙盒配置与验收](docs/sandbox-setup.md)。只有用户已有适用的 Sandbox 商户应用时，才在自己电脑填入 client ID、secret、merchant ID，并设 `PAYMENT_MODE=sandbox`。缺项直接启动失败，不伪装为已接通。

所有 PayPal 网络请求固定指向官方 Sandbox API；审批跳转地址也只允许 Sandbox。服务端先建立并保存内部订单，金额/币种/项目/修订/会话/SKU/幂等键固定。批准不等于已付款：服务端先核验订单详情，再 capture，再查询并核对 COMPLETED、金额币种、商户和订单引用，才能一次性创建导出权益。

模拟和真实 Sandbox 的账本模式隔离。切换模式无法把模拟权益变成真实 Sandbox 权益。此版没有 production 开关、退款、订阅、分账、Webhook 或自动付款代理。

## 验证与限制

安装依赖后运行 `python -m unittest discover -s tests -v`。测试包含真实视频编码、错误金额、重放/并发、丢失响应、跨项目/会话、刷新与重启、模式隔离、CSRF/Origin、导出失败重试。

`evidence/` 保留明确标注的虚构样片、ffprobe 参数与分镜，测试结果见 [公开验证摘要](evidence/PUBLIC_VERIFICATION.md)。原始测试日志、运行账本、会话与内部QA资料未纳入公开源码。后续必须由用户配置现有本地模型与 Sandbox 凭据，实际完成一遍真实端到端流程，并录制不超过 3 分钟的实际屏幕演示，才可勾选对应参赛验收项。没有替用户公开上传、部署或最终提交。

## 本地数据

`data/` 保存数据库和视频，`.env` 保存本地配置，均不要公开。请保留同一个浏览器会话；清除 Cookie 会失去该会话的权益访问。localhost 与 127.0.0.1 的 Cookie 不互通。内容迁移使用 JSON；备份数据库只用于用户私人保存。此版本不是公网多用户服务，不能防御同一电脑管理员。

基于公开 MIT EvoVid Pocket 分支，保留原 MIT LICENSE，增量见 [来源与许可](docs/upstream-and-license.md)。样例品牌/文案/几何动画均为原创虚构；不包含音乐、人物照片、模型权重或私有素材。依赖各遵其许可证，字体来自用户系统，不重新分发。
