# social-auto-upload 实战记录 (2026-07-01)

基于 dreammis/social-auto-upload (13k⭐) 在 `/home/kan/shared/social-auto-upload/` 的实测。

## 环境依赖
- Python 3.10+
- **patchright** (不是 playwright) — `pip install patchright && patchright install chromium`
- 无头服务器需 Xvfb 或有桌面环境机器做登录

## 平台实测状态 (2026-07-11)

| 平台 | 状态 | 支持 --schedule | 关键参数 | 备注 |
|------|------|-----------------|----------|------|
| **bilibili** | ✅ | 是 | `--tid 249` (科技/数码) | Cookie 稳定 |
| **kuaishou** | ✅ | 是 | `--headless` 必填 | Cookie 稳定 |
| **youtube** | ⚠️ | **否** | `--visibility private` | Cookie 过期，**登录需有桌面环境** |
| **douyin** | ⏳ | 未测 | 需 Windows 有头模式 | `sau douyin login --account her2home` |
| **xiaohongshu** | ⏳ | 未测 | - | 待测试 |
| **tencent (视频号)** | ✅ | 是 | `--account her2home` | headless-shell 出 QR PNG 发用户扫码，cookie 自动存 |

## 视频号登录 (tencent headless 2026-07-12 验证)

**关键发现**：headless 服务端完全可处理视频号登录，不需要桌面环境。

**前提**：`conf.py` 必须设 `LOCAL_CHROME_PATH` 指向 headless-shell（见 `signal-pop-pipeline` 的 Chrome/Playwright 节）。

**流程**：
```bash
# 1. 本机跑（不需 X11）
sau tencent login --account her2home
# 输出:
#   🖼️ 二维码已经准备好啦，已保存到: cookies/tencent_her2home_tencent_login_qrcode_*.png
#   🧍 请扫码，小人正在耐心等待登录完成

# 2. 把生成的 PNG 发给用户手机（聊天工具）
# 3. 用户微信扫码 → 手机确认 → 登录成功
# 4. 验证
sau tencent check --account her2home
```

**二维码过期处理**：程序自动检测过期并刷新，每3秒轮询，默认300次（~15分钟）。用户来扫时可能过期——等用户准备好再跑命令。

**cookie 持久化**：`cookies/tencent_uploader/her2home`（无后缀文件，Playwright storage_state 格式）。后续 `sau tencent upload-video` 直接使用。`tencent_setup()` 自动调 `cookie_auth()` 校验。

**发布命令**：
```bash
sau tencent upload-video --account her2home \
  --file /home/kan/shared/her2home/video_20260712.mp4 \
  --title "隔天信号弹 7.13｜标题" \
  --desc "简介..." \
  --tags "隔天信号弹,科技资讯,AI" \
  --schedule "2026-07-14 08:30"
```

**auto_publish.py 集成**：`PLATFORMS` 列表中含 `"tencent"`，`build_upload_cmd()` 对 tencent 用 `--headless` 参数。注意 `tencent_uploader/main.py` 的 `_build_launch_kwargs()` 在 `LOCAL_CHROME_PATH` 有值时用 `executable_path` 而非 `channel="chrome"`，所以 headless-shell 被执行。

## 关键 CLI 参数差异

### bilibili (最完整)
```bash
sau bilibili upload-video --account her2home \
  --file video.mp4 --title "标题" --desc "简介" \
  --tags "tag1,tag2" --tid 249 --schedule "2026-07-02 14:00"
```

### kuaishou (需 headless)
```bash
sau kuaishou upload-video --account her2home \
  --file video.mp4 file video.mp4 --title "标题" --desc "简介" \
  --tags "tag1,tag2" --thumbnail cover.png --headless \
  --schedule "2026-07-02 14:00"
```

### youtube (无 schedule)
```bash
sau youtube upload-video --account her2home \
  --file video.mp4 --title "标题" --desc "简介" \
  --tags "tag1,tag2" --visibility private --headless
# 上传后去 YouTube Studio 手动设置定时
```

## 登录流程

```bash
# 首次/Cookie 过期时
sau bilibili login --account her2home
sau kuaishou login --account her2home
sau youtube login --account her2home  # 必须有显示器
sau douyin login --account her2home   # Windows 有头模式
sau xiaohongshu login --account her2home
```

Cookie 存放：`/home/kan/shared/social-auto-upload/cookies/{platform}_her2home.json`

## 常见错误 & 修复

| 错误 | 原因 | 修复 |
|------|------|------|
| `Executable doesn't exist at ... chromium-1208` | patchright 版本不匹配 — `playwright install chromium` 装的是 v1223 不是 v1208 | 用 `pip list | grep -iE 'playwright|patchright'` 确认 sau 的包 → `patchright install chromium` |
| `Missing X server or $DISPLAY` | 无头服务器跑 YouTube 登录 | 换有桌面环境的机器登录 |
| `unrecognized arguments: --schedule` | YouTube CLI 不支持 | 去掉 `--schedule`，用 `--visibility private` |
| `Cookie is missing or expired` | Cookie 过期 | 重新跑 login 命令 |
| `auto_publish.py` 扫描到旧视频而非新视频 | 旧视频标记部分平台失败 → 脚本认为未完成 | 编辑 `.publish_state.json` 移除旧视频条目，只保留新 `video_YYYYMMDD.mp4` |

## 状态文件去重机制

- 文件：`/home/kan/shared/her2home/.publish_state.json`
- 逻辑：按**视频文件名**去重，同名文件绝不重复上传
- **重试失败需手动删状态条目**：
  ```bash
  # 编辑 .publish_state.json，删除对应 video_xxx.mp4 的整个对象
  python auto_publish.py  # 再次扫描会重新上传
  ```

## 自动分发脚本 (auto_publish.py)

位置：`/home/kan/shared/social-auto-upload/auto_publish.py` (同步到 skill 的 `scripts/auto_publish.py`)

特点：
- 顺序上传 (避免浏览器冲突)
- 仅上传已认证平台 (PLATFORMS = ["bilibili", "kuaishou", "youtube"])
- 读取同名 .json 元数据 (title/desc/tags/schedule)
- 成功写入 .publish_state.json

🚫 **严禁设周期性 cron** — 只允许手动一次性 `python auto_publish.py`。用户明确要求不要多次触发发布任务（快手每天发视频影响体验）。失败后也只跑一次重试，不设自动重试。

## 视频/封面/元数据命名规范

```
/home/kan/shared/her2home/
├── video_20260701.mp4      # 视频
├── video_20260701.png      # 封面 (1920x1080 16:9)
├── video_20260701.json     # 元数据
└── .publish_state.json     # 发布状态
```

元数据 JSON 模板：
```json
{
  "title": "隔天信号弹 7.01｜标题",
  "desc": "简介内容...",
  "tags": "隔天信号弹,科技资讯,AI,新闻",
  "schedule": "2026-07-02 14:00"
}
```