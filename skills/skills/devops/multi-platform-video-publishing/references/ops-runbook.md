# 多平台视频自动分发 - 登录与运维参考

## 登录流程标准化

### 一键登录脚本
```bash
# 位置: /home/kan/shared/social-auto-upload/login_all_platforms.sh
#!/usr/bin/env bash
set -euo pipefail

ACCOUNT="her2home"
PLATFORMS=("douyin" "bilibili" "xiaohongshu" "kuaishou")

for p in "${PLATFORMS[@]}"; do
    echo "=== 登录 $p ==="
    sau "$p" login --account "$ACCOUNT" || echo "$p 登录失败，继续下一个"
done

echo "=== 验证所有平台 ==="
for p in "${PLATFORMS[@]}"; do
    sau "$p" check --account "$ACCOUNT" && echo "$p: OK" || echo "$p: INVALID"
done
```

### 单平台登录验证
```bash
sau douyin check --account her2home
sau bilibili check --account her2home
sau xiaohongshu check --account her2home
sau kuaishou check --account her2home
```

## Cookie 管理
- 存储目录：`/home/kan/shared/social-auto-upload/cookies/`
- 文件命名：`<platform>_<account>.json`（如 `douyin_her2home.json`）
- 二维码临时文件：`douyin_<account>_login_qrcode_<timestamp>.png`
- **抖音二维码必须通过 HTTP 链接在手机浏览器打开扫码**，终端 ASCII 码不可靠

## 定时分发架构

### 状态去重
- 状态文件：`/home/kan/shared/her2home/.publish_state.json`
- Key：文件名（stem），Value：上传时间戳 + 平台结果
- 同名文件不重复上传

### 视频元数据 JSON 模板
```json
{
  "title": "隔天信号弹 2026-06-28：AI突破+热点追踪",
  "description": "本期内容... #隔天信号弹 #AI资讯 #科技新闻",
  "tags": ["隔天信号弹", "AI资讯", "科技新闻", "热点追踪"],
  "schedule": "2026-06-29 08:30",
  "thumbnail": "video_20260628.png"
}
```
- 字段：`title`、`description`、`tags`、`schedule`（可选，格式 `YYYY-MM-DD HH:MM`）、`thumbnail`（可选，默认同名 png）
- B站分区固定：`--tid 249` (科技/数码)

## 平台发布参数差异

| 平台 | CLI 命令 | 封面参数 | 定时参数 | 备注 |
|------|----------|----------|----------|------|
| 抖音 | `sau douyin upload` | `--thumbnail-portrait` | `--schedule "YYYY-MM-DD HH:MM"` | 竖版 3:4 |
| B站 | `sau bilibili upload` | `--thumbnail-landscape` | `--schedule "YYYY-MM-DD HH:MM"` | `--tid 249` 横版 16:9 |
| 小红书 | `sau xiaohongshu upload` | `--thumbnail` | `--schedule "YYYY-MM-DD HH:MM"` | 1:1 或 3:4 |
| 快手 | `sau kuaishou upload` | `--thumbnail` | `--schedule "YYYY-MM-DD HH:MM"` | 横版 16:9 |

## 常见故障排查

### 抖音二维码过期/登录失败
1. 确认已应用补丁（见 `references/douyin-qrcode-login-fix.md`）
2. 运行登录，**马上**打开最新 PNG HTTP 链接扫码
3. 等待「登录成功」日志，验证 `sau douyin check --account her2home` 返回 `valid`

### Cookie 失效
```bash
# 单平台重新登录
sau douyin login --account her2home

# 全平台重新登录
./login_all_platforms.sh
```

### 上传后未定时发布
- 检查 `schedule` 字段格式：`YYYY-MM-DD HH:MM`（24 小时制）
- 服务器时区必须为 `Asia/Shanghai`
- 平台审核可能延迟发布，日志查看：`sau <platform> list --account her2home`

### ⚠️ auto_publish.py 扫到旧视频而非新视频

**症状**：脚本总是重试 `test_video_*.mp4` 或 `video_20260627.mp4`，不处理当前期视频。

**根因**：`.publish_state.json` 中旧视频某平台标记失败（如抖音 `false`），且旧 `.mp4` 文件物理存在于 `her2home/` 目录中 → `find_new_videos()` 认为它们未发布完，优先重试。

**修复**（两步缺一不可）：
```bash
# 1. 移走所有旧视频/封面/元数据
mkdir -p /home/kan/shared/her2home/archive_old
mv /home/kan/shared/her2home/video_20260*.mp4 /home/kan/shared/her2home/archive_old/
mv /home/kan/shared/her2home/video_20260*.png /home/kan/shared/her2home/archive_old/
mv /home/kan/shared/her2home/video_20260*.json /home/kan/shared/her2home/archive_old/
mv /home/kan/shared/her2home/test_* /home/kan/shared/her2home/archive_old/
mv /home/kan/shared/her2home/cover_*.png /home/kan/shared/her2home/archive_old/ 2>/dev/null

# 2. 清理 .publish_state.json，只保留本期
#    eg: {"published": {"video_20260707.mp4": {"time":"...","platforms":{}}}}
```

### ⚠️ Playwright 浏览器版本不匹配

`sau` 用 `patchright` 1.58.2，需要 chromium-1208。
全局 `playwright install chromium` 装的是 chromium-1223，版本不对。

```bash
# 看 sau 用哪个包
pip list | grep -iE "playwright|patchright"

# 用对应的包名装浏览器
python3 -m patchright install chromium   # sau 用 patchright
# 或
python3 -m playwright install chromium   # sau 用 playwright
```

### ⚠️ 抖音 Missing X Server

```bash
# 每次运行分发前必须设置
export DOUYIN_COOKIE_AUTH_HEADLESS=true
python3 auto_publish.py
```

### 各平台实测结果 (2026-07-07)

| 平台 | 状态 | 耗时 | 备注 |
|------|------|------|------|
| B站 | ✅ 跳过(已发) | — | 定时 07-08 08:30 |
| 快手 | ✅ 成功 | ~5min | cookie 有效，`--headless` 正常 |
| 小红书 | ❌ 挂死 | 850s timeout | `div.d-modal.cover-modal` 弹窗等不到，headless 可能触发风控 |
| 抖音 | ❌ 报错 | 失败 | `cookie_auth` 需 `DOUYIN_COOKIE_AUTH_HEADLESS=true`；上传后封面弹窗 timeout |

### 超时策略

`auto_publish.py` 对每个平台 `subprocess.run(..., timeout=600)`。
快手上传约 3-5 分钟，勉强够。若超时改为单独跑每个平台：
```bash
export DOUYIN_COOKIE_AUTH_HEADLESS=true
timeout 900 sau kuaishou upload-video --account her2home ... --headless --schedule "YYYY-MM-DD HH:MM"
```

### 分发策略：仅手动一次性触发

- 视频就绪后手动跑 `python3 auto_publish.py`
- **绝对不要设周期性 cron** — 用户明确要求不能多次触发
- 失败后重试也只手动跑一次

## 目录结构
```
/home/kan/shared/
├── social-auto-upload/          # 克隆的 social-auto-upload 仓库（已打补丁）
│   ├── cookies/                 # 登录凭证 + 二维码图片
│   ├── uploader/douyin_uploader/main.py  # 已修复 Bug
│   ├── login_all_platforms.sh   # 一键登录脚本
│   ├── auto_publish.py          # 自动分发核心脚本
│   └── sau_wrapper.sh           # CLI 入口包装（PYTHONPATH 修正）
├── her2home/                    # 马小v 投递目录
│   ├── video_YYYYMMDD.mp4
│   ├── video_YYYYMMDD.png
│   ├── video_YYYYMMDD.json
│   ├── archive_old/             # 归档旧视频（防止混淆） 
│   └── .publish_state.json      # 去重状态
└── signal-pop-hyperframes/      # Signal Pop 视频生成管线（另一套系统）
```

## 关键路径
- `sau` CLI：`/home/kan/shared/social-auto-upload/venv/bin/sau` (symlink → `sau_wrapper.sh`)
- Python 环境：`/home/kan/shared/social-auto-upload/venv/bin/python`
- Patchright Chromium：已安装在 venv 内
