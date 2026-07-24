---
name: multi-platform-video-publishing
description: 多平台视频自动发布自动化技能。覆盖抖音、B站、小红书、快手、视频号、百家号、TikTok、YouTube 等主流平台的视频上传、定时发布、多账号管理、无头模式运行。基于 social-auto-upload (13k⭐) 项目构建。
category: devops
tags:
  - social-media
  - video-publishing
  - automation
  - douyin
  - bilibili
  - xiaohongshu
  - kuaishou
  - tiktok
  - youtube
---

# 多平台视频自动发布自动化

## 适用场景
- 内容创作者/运营需要将同一视频一键分发到多个平台
- 服务器无人值守定时发布
- AI Agent 驱动的自动化内容分发管线
- 多账号矩阵管理

## 核心工具：social-auto-upload
- **GitHub**: https://github.com/dreammis/social-auto-upload (13k⭐)
- **CLI 入口**: `python -m sau_cli douyin|bilibili|xiaohongshu|kuaishou|tencent|youtube ...`
- **支持平台**: 抖音、B站、小红书、快手、视频号、百家号、TikTok、YouTube
- **核心能力**: 视频上传、封面图、定时发布、多账号、无头模式、AI Agent Skill 化

## 部署标准流程

### 1. 环境准备（Linux / 服务器）
```bash
# 克隆项目到共享文件夹
cd /home/kan/shared
git clone https://github.com/dreammis/social-auto-upload
cd social-auto-upload

# 安装 Python 依赖（可编辑模式）
uv pip install -e .   # 或 pip install -e .

# 安装无头浏览器
patchright install chromium
```

#### Playwright 浏览器下载失败 → 使用系统 Chrome symlink

当 `playwright install chromium` 从 CDN 下载超时（国内服务器常见）：

```bash
# 1. 确认系统已安装 Chrome
/opt/google/chrome/chrome --version
# Google Chrome 149.0.7827.200

# 2. 创建 playwright 期望的目录并 symlink
# 版本号从报错中提取，如 chromium-1208
mkdir -p /home/kan/.cache/ms-playwright/chromium-1208/chrome-linux64
ln -sf /opt/google/chrome/chrome /home/kan/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
```

### 1b. 环境准备（Windows 本地登录/调试）
**用途**：抖音/B站/小红书/快手等平台登录扫码需有头浏览器，Windows 本地跑最稳。

```powershell
# 1. 复制项目到 Windows（从共享文件夹）
cp -r \\\\10.10.10.30\\shared\\social-auto-upload E:\\projects\\
cd E:\\projects\\social-auto-upload

# 2. 安装依赖（避免 C++ 编译工具报错）
pip install playwright
playwright install chromium
```

### 2. 配置文件
```bash
cp conf.example.py conf.py
# 编辑 conf.py：设置 BASE_DIR、代理、调试模式等
```

### 3. CLI 入口关键点
**必须在项目目录 `/home/kan/shared/social-auto-upload` 下运行**，`conf.py` 需存在。

**真实入口**：`python -m sau_cli` 或 `python sau_cli.py`（项目自带 CLI 模块）。

⚠️ **PyPI `sau` 包（`pip install sau`）是 AWS EC2 卷导出工具，完全不同项目**。

**Wrapper 修复**（加到 PATH 后可直接用 `sau`）：
```bash
cat > /home/kan/shared/social-auto-upload/sau_wrapper.sh << 'EOF'
#!/bin/bash
export PYTHONPATH=/home/kan/shared/social-auto-upload
exec python3 -m sau_cli "$@"
EOF
chmod +x /home/kan/shared/social-auto-upload/sau_wrapper.sh
ln -sf /home/kan/shared/social-auto-upload/sau_wrapper.sh ~/.local/bin/sau
```

### 4. 首次登录（扫码，仅需一次）
```bash
sau douyin login --account <account_name> --headless
sau bilibili login --account <account_name>
sau xiaohongshu login --account <account_name> --headless
sau kuaishou login --account <account_name> --headless
```
- Cookie 自动持久化到 `cookies/` 目录
- 后续运行自动复用，无需重复扫码

## 自动化管线设计

### 文件约定
```bash
/home/kan/shared/her2home/
├── video_YYYYMMDD.mp4          # 视频文件
├── video_YYYYMMDD.png          # 封面图（必须与视频同名！）
└── video_YYYYMMDD.json         # 元数据
```

**⚠️ 封面命名硬性要求**：`video_YYYYMMDD.png`（auto_publish.py 按视频同名查找 `.png`/`.jpg`）。`cover_YYYYMMDD.png` 会被跳过。

### 元数据 JSON 格式
```json
{
  "title": "隔天信号弹 7.06｜标题",
  "desc": "简介内容...",
  "tags": "隔天信号弹,AI,科技资讯",
  "schedule": "2026-07-06 08:00"
}
```

### 自动分发脚本核心逻辑 (`auto_publish.py`)
1. **扫描**目录下 `*.mp4`
2. **匹配**同名 `.png/.jpg` 封面 + `.json` 元数据
3. **去重**检查 `.publish_state.json` 记录
4. **顺序**调用 `sau` 上传（B站 → 快手 → YouTube，间隔 5-10 秒）
5. **记录**成功/失败状态，失败下轮重试

### 平台特殊处理（内置在 auto_publish.py）

| 平台 | `--schedule` | 失败处理 |\n|------|-------------|----------|\n| B站 | 支持 | 正常上传 |\n| 快手 | 支持 + `--headless` | 浏览器缺失时 symlink 系统 Chrome |\n| 视频号 | 支持 | 见下方「视频号登录排错」和「视频号登录代码修复」 |\n| YouTube | ❌ 不支持 | 自动降级为 `--visibility private`，手动改公开 |\n| 抖音/小红书 | 待接入 | 需先登录，cookies 路径待统一 |\n\n**Signal Pop 定时规则：所有平台 `--schedule` 必须设为出稿日+1天 08:30。** 例：出稿日07/24 → 定时07/25 08:30。YouTube 不支持 schedule，降级为 private 手动改。

### 微信视频号（WeChat Channels / Tencent）

CLI 入口: `sau tencent <action> --account <name>`

**支持的操作：**
| 操作 | 命令 | 说明 |
|------|------|------|
| 登录 | `sau tencent login --account <name> [--headed]` | 弹窗扫码（`--headed`，非 `--no-headless`），cookie 持久化到 `cookies/tencent_uploader/` |
| 校验 | `sau tencent check --account <name>` | 检查 cookie 是否有效 |
| 上传 | `sau tencent upload-video --account <name> --file <path> --title <title>` | 上传视频+封面+定时发布 |

**上传参数：**
| 参数 | 必填 | 说明 |
|------|------|------|
| `--account` | ✅ | 账号名 |
| `--file` | ✅ | 视频路径 |
| `--title` | ✅ | 标题（≤30字） |
| `--short-title` | ❌ | 短标题（≤16字，默认从title截取） |
| `--desc` | ❌ | 简介描述 |
| `--tags` | ❌ | 逗号分隔标签 |
| `--schedule` | ❌ | 定时发布 `YYYY-MM-DD HH:MM` |
| `--thumbnail` | ❌ | 3:4竖版封面 |
| `--thumbnail-landscape` | ❌ | 4:3横版封面 |
| `--thumbnail-portrait` | ❌ | 3:4竖版封面（别名） |
| `--category` | ❌ | 原创内容分类 |
| `--draft` | ❌ | 存草稿不发布（flag） |

### 视频号登录排错

**参数名陷阱**：sau 用 `--headed`（不是 `--no-headless`）。默认 headless（无浏览器窗口）。`--headed` 弹出 Chrome 窗口显示二维码。

```powershell
sau tencent login --account signalpop --headed   # ✅ 正确
sau tencent login --account signalpop --no-headless  # ❌ unrecognized arguments
```

**登录代码崩修（2026-07-11 实测）**：新版视频号页面 DOM 结构变了，扫码登录流有三个崩溃点。修法见 `references/wechat-channels-cookie-export.md` 的「登录代码修复记录」章节。核心思路：**让 QR 码提取失败不致命**——`--headed` 模式下浏览器窗口里的二维码用户肉眼可见，扫完后 cookie 照样自动保存。

**各平台登录机制差异**：

| 平台 | 登录方式 | 是否走 Playwright 弹窗 | 需不需要修 main.py |
|------|---------|----------------------|------------------|
| 视频号 | Playwright 弹窗 → 微信扫码 | ✅ | 页面改版时需修选择器 |
| B站 | `biliup` 终端打印 QR 码（biliup 子进程） | ❌ 纯终端，不弹窗 | 无 — biliup 独立维护 |
| 快手 | Playwright 弹窗 → 扫码（跟视频号类似） | ✅ | 如遇新版选择器失效同样需修 |
| 抖音 | Playwright 弹窗 → 扫码 | ✅ | 已有独立 fix 参考 |

如果快手也遇到二维码提取失败，修法跟视频号完全一样：`uploader/ks_uploader/main.py` 中把 QR 提取改为 try/except 非致命。

**症状**：二维码已生成并保存为 PNG，微信扫码后浏览器无响应，300秒后超时退出。或报错「未获取到视频号登录二维码地址」（页面改版选择器失效）。

**排查顺序**：

1. **账号资质** — 登录的微信必须已开通视频号（微信→发现→视频号→右上角人像→创作者中心）。普通微信号扫了码也会卡住，这不是 Bug。

2. **无头/有头模式** — 默认 headless（不弹窗），二维码存在磁盘 PNG。Windows 推荐加 `--headed` 弹浏览器窗口扫码：
   ```powershell
   sau tencent login --account signalpop --headed
   ```

3. **二维码路径** — 保存到 `cookies/tencent_<account>_tencent_login_qrcode_<timestamp>.png`。如果终端没弹二维码 ASCII（解析失败），手工打开这个 PNG 用微信扫。

4. **超时机制** — 实现中 `poll_interval=3s, max_checks=100`，合计 **300秒（5分钟）**。二维码通常有效期约 2 分钟，超时后脚本会**自动刷新二维码**（`_is_tencent_qrcode_expired` + `_refresh_tencent_qrcode`），所以理论上可无限等待。但若微信端的 cookie/登录态有问题（如账号未开通视频号），刷新了也没用。

5. **网络问题** — 工具打开 `https://channels.weixin.qq.com` 如果加载不出来（看浏览器是否白屏），检查网络环境。微信视频号管理后台需要能访问 `qq.com`。

**备选方案：自动扫码失败 → 手动 Cookie 导出**
详见 `references/wechat-channels-cookie-export.md`。
- 手动在 Chrome 登录视频号后台
- 用 EditThisCookie 扩展导出 cookie
- 转换格式为 Playwright storage_state JSON
- `sau tencent check --account <name>` 验证

**Windows 环境完整登录流程**：
```powershell
# 1. 有头模式弹窗（推荐）
sau tencent login --account signalpop --headed
# 弹 Chrome 窗口 → 显示二维码 → 用微信扫 → 手机确认 → 自动关闭

# 2. 或从文件扫码（无头）
sau tencent login --account signalpop
# 打开 cookies/ 下最新 PNG 用微信扫
```

### YouTube Cookie 过期解决方案
```bash
# 需有桌面环境的机器（Windows/带 X Server 的 Linux）
sau youtube login --account her2home
```
Headless 服务器无法扫码，必须在有桌面环境的机器操作一次。

### Cron 任务配置
| 任务 | 频率 | 用途 |
|------|------|------|
| 监控文件完整性 | 30 分钟 | 检查视频/封面是否完整、报警 |
| 自动分发 | 30 分钟 | 发现新视频 → 顺序多平台发布 |

**实际调度时间（配合团队节奏）**：
- 虾小图产出新闻稿：08:00-08:30
- 马小v 生成视频：~10:00
- 自动分发检查：**10:30 和 16:30** 两次/天
- 周刊：周六 09:00 发布

## 维护命令
```bash
# 更新项目
cd /home/kan/shared/social-auto-upload && git pull && uv pip install -e .

# 更新浏览器
patchright install chromium

# 查看发布状态
cat /home/kan/shared/her2home/.publish_state.json

# 清除已发布记录（重试失败上传）
python3 -c "
import json
with open('/home/kan/shared/her2home/.publish_state.json') as f:
    s = json.load(f)
s['published'].pop('video_YYYYMMDD.mp4', None)
with open('/home/kan/shared/her2home/.publish_state.json', 'w') as f:
    json.dump(s, f, ensure_ascii=False, indent=2)
"
```

## 关联文件
- `references/social-auto-upload-cli.md` — CLI 完整参数参考
- `references/douyin-qrcode-login-fix.md` — 抖音二维码登录 Bug 修复记录
- `references/douyin-qrcode-fix-patches.md` — 抖音二维码登录 Bug 精确补丁
- `references/youtube-facebook-support.md` — YouTube/Facebook 支持现状与配置
- `references/douyin-login-flow.md` — 抖音登录 & 上传完整流程
- `references/windows-deployment.md` — Windows 本地部署与登录指南
- `references/ops-runbook.md` — 运维实战记录（旧视频污染、浏览器版本、超时、各平台实测）
- `references/wechat-channels-cookie-export.md` — 微信视频号手动 Cookie 导出 + 格式转换（自动登录失败时的备用方案）
- `templates/video_metadata.json.example` — 元数据模板
- `scripts/auto_publish.py` — 自动分发主脚本（含 YouTube --schedule 降级逻辑）
- `scripts/login_all_platforms.sh` — 一键登录脚本

## 实战教训

### 旧视频污染挡住新视频

`auto_publish.py` 扫描 `her2home/` **所有 .mp4**。旧视频若 `.publish_state.json` 中某平台标记失败 → 脚本优先重试旧视频。

**分发前必经步骤**：
```bash
mkdir -p /home/kan/shared/her2home/archive_old
mv /home/kan/shared/her2home/video_20260*.mp4 video_20260*.png video_20260*.json test_* cover_* archive_old/ 2>/dev/null
# 清理 .publish_state.json，只保留本期记录
```

### Playwright/Patchright 浏览器版本不匹配

`sau` 用 `patchright` 1.58.2 → 需要 chromium-1208。
全局 `playwright install chromium` 装 chromium-1223 → **版本不对**。

```bash
pip list | grep -iE "playwright|patchright"  # 看 sau 用哪个
python3 -m patchright install chromium        # sau 用 patchright
```

### 抖音无头 Missing X Server

```bash
export DOUYIN_COOKIE_AUTH_HEADLESS=true
python3 auto_publish.py
```

### 分发策略强制：仅手动一次性触发

- 视频就绪 → `python3 auto_publish.py`
- **绝对不要设周期性 cron** — 用户明确要求不能多次触发
- 失败也只手动重试一次
