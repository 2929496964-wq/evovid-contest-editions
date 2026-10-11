# EvoVid Taste Director · 文化偏好分镜导演

> Public-source copy: raw execution logs, internal QA material, runtime/session data and old source-package inventories are excluded. Historical pass/fail and live/fixture boundaries are preserved in [public verification](evidence/PUBLIC_VERIFICATION.md). The new root [manifest](../PUBLIC-MANIFEST.json) inventories this exact copy.

独立本地应用：公开影视/音乐参考 → 用户确认实体 → Qloo文化关联与主题 → 三份原创策划 → 可编辑四镜分镜 → 项目保存/偏好重规划 → 真实动效MP4导出。

## 当前真实状态

- **DEMO可完整运行**，数据为作者制作的合成样例，所有ID/关联均不冒充Qloo返回；不会生成假的affinity分数。
- 已实现**真实Qloo REST适配器**，合同测试通过，但**没有申请、创建、读取或使用真实Qloo凭据，没有完成真实API联调**。
- LIVE模式无key、鉴权失败、限流或超时均停止并说明，绝不悄悄变成DEMO。
- 策划是可检查的确定性工具工作流，**没有调用LLM**。实体消歧、工具选择、约束检查、用户反馈重规划都有结构化轨迹。
- MP4是真正生成的**静音几何动效分镜**，不是神经文生视频，也不包含参考电影片段或音乐。
- 本轮没有公开push、部署、注册凭据或最终提交。赛事所需公开源码与公网demo仍待授权后执行。

## Windows启动

安装官方Python 3.12（优先）或3.11后，直接双击`start.bat`：首次会自动安装锁定依赖，再启动应用，成功安装不会额外暂停；失败会提示并停止。安装器优先3.12并回退3.11；本轮实际测试的是3.12。浏览器地址为`http://127.0.0.1:8714`。

## Linux / macOS启动

```sh
./start.sh  # 首次自动安装锁定依赖
# 不自动打开浏览器：
PORT=8714 ./start.sh --no-browser
```

默认仅监听本机回环地址。安装器只从官方PyPI安装锁定包，不下载模型。优先用系统FFmpeg，否则使用已安装imageio-ffmpeg包内二进制。`PORT`可改端口，`.venv`不进入交付压缩包。

## 一次完整体验

1. 选择DEMO，搜索`Moonlight`，自己选择2016或2002版本，观察重名消歧。
2. 搜索`Spirited Away`或音乐类别的`Daft Punk`，明确加入1–4个参考。
3. 填创作目标、时长、比例、节奏与设备预算，生成三种方向。
4. 文化关联与EvoVid创作解释分层展示。affinity只表示文化关联分数，不能解释成个人喜爱概率。
5. 选择一个方向，修改四个镜头的标题、画面、时长和运镜，保存。
6. 播放画布预览，导出实际H.264 MP4，也可下载JSON完整项目/去密钥轨迹或Markdown brief。
7. 移除参考并加入`Interstellar`，点击重规划。新项目会保留前后主题、参考变更与重新查询记录。
8. 项目由SQLite保存，刷新可恢复；取消或重启中断会明确标注，需主动重试，不伪装成功。

其他样例：Amélie、Arrival、The Grand Budapest Hotel、Björk、Tycho。未知DEMO搜索词真实显示没有样例。

## 安全配置

只有运营者获授权后，才在**服务端进程环境**安全注入`QLOO_API_KEY`，不在聊天发送、不放浏览器、不存Git或命令行参数。`.env.example`仅为空值说明，程序不会主动查找或读取本地密钥文件。发行说明要求的host/配额仍需核验。赛事版按[官方hackathon key指南](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide#getting-your-api-key)固定REST主机为`https://hackathon.api.qloo.com`，不自动换主机或跟随重定向。

Qloo只收到经用户确认的公开作品/艺名搜索词、已确认实体ID及固定参数。姓名、邮箱、账号、设备ID、位置历史及主版私密数据不应输入；创作目标保留本地，不传Qloo。显式勾选与格式检查只是最小化措施，不能保证自动识别一切个人数据。

匿名浏览器会话隔离项目与下载，默认本地使用；清除cookie会失去原会话入口，因此重要项目请导出。公开部署需HTTPS、容量限制、外部测试与授权，见[部署说明](docs/DEPLOYMENT.md)。

## 验证与未完成事项

运行`python -m unittest discover -s tests -v`。真实MP4渲染、会话隔离、重规划、错误边界和合同测试已覆盖；详见`status.json`和[实测记录](docs/VERIFICATION.md)。真实Qloo网络调用、Windows实际启动、Docker构建、真实浏览器视觉验收仍未验证。当前执行环境的浏览器受限，不把DOM模拟当作真实浏览器测试。

基于公开MIT EvoVid Pocket提交`31255c83ff1f57143c5cf819c6e7a6bf8fc12fbe`，保留上游许可证；未复制私人素材/状态/凭据。参考文化作品不代表素材授权。英文说明、架构/合规矩阵及发布阻断项见[English README](README.md)。
