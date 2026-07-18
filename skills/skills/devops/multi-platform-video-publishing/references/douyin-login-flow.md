---
title: Douyin Login & Upload Flow
description: 抖音扫码登录、二维码固定链接、视频上传完整流程
---

# 抖音登录 & 上传完整流程（2026-06-30 会话总结）

## 核心架构
- 基于 **Playwright `storage_state`**（`cookies/douyin_her2home.json`）
- 登录需 **有头浏览器**（无头会撞反爬墙 → 误判 cookie 失效）
- 二维码 **2-3 分钟失效**，脚本每 30 秒自动刷新 + 固定软链指向最新文件

---

## 1️⃣ 首次登录（Windows 本地，有桌面环境）

```powershell
cd E:\projects\social-auto-upload
python sau_cli.py douyin login --account her2home
```

### 执行过程
1. 弹出 **有头 Chromium** → 打开 `https://creator.douyin.com/`
2. 终端打印 **ASCII 二维码**（Windows Terminal 支持 UTF-8）
3. 同时生成 PNG：`cookies/douyin_her2home_login_qrcode_YYYYMMDD_HHMMSS.png`
4. **固定软链** 自动创建/更新：
   ```
   douyin_her2home_latest_qrcode.png -> douyin_her2home_login_qrcode_20260628_230919.png
   ```
5. 手机抖音 APP 扫码 → 确认授权
6. 检测到 URL 含 `/creator-micro` 且无登录文案 → 登录成功
7. 保存 `storage_state` 到 `cookies/douyin_her2home.json`

### 远程扫码最佳实践
| 方式 | 地址 | 优势 |
|------|------|------|
| **Tailscale（推荐）** | `http://100.84.133.58:8080/social-auto-upload/cookies/douyin_her2home_latest_qrcode.png` | 已有节点，手机开 Tailscale 直接访问，无需刷新 |
| 局域网 | `http://10.10.10.30:8080/social-auto-upload/cookies/douyin_her2home_latest_qrcode.png` | 内网直连 |
| ngrok | 临时隧道 | 需认证，配置繁琐 |

**关键**：打开固定链接，**无需刷新**，对着屏幕用抖音扫一扫。

---

## 2️⃣ 验证登录态

```bash
sau douyin check --account her2home
```
输出 `cookie有效` 即可上传。

---

## 3️⃣ 视频上传（立即发布）

```bash
sau douyin upload-video --account her2home \
  --file /path/to/video_20260630.mp4 \
  --title "隔天信号弹 20260630" \
  --desc "这里是隔天信号弹，今日关注：..." \
  --tags "新闻,时事,AI科技,隔天信号弹" \
  --thumbnail-portrait /path/to/cover_20260630.png
```

- `--tags` 用**英文逗号**分隔，最多 10 个
- `--thumbnail-portrait` 竖版封面 3:4（可选，抖音也支持自动截帧）
- 视频 ≤ 15 分钟，≤ 4 GB，建议 1080p H.264

---

## 4️⃣ 定时发布（可选）

```bash
sau douyin upload-video --account her2home \
  --file /path/to/video_20260630.mp4 \
  --title "隔天信号弹 20260630" \
  --tags "新闻,时事,AI科技" \
  --schedule "2026-07-01 08:30"
```
- `--schedule` 格式：`YYYY-MM-DD HH:MM`（24 小时制）
- 后台勾选「定时发布」并填入时间

---

## 5️⃣ 图文/笔记发布（如需要）

```bash
sau douyin upload-note --account her2home \
  --images /path/to/img1.jpg,/path/to/img2.jpg \
  --title "标题" \
  --note "正文内容 #话题1 #话题2"
```

---

## ⚠️ 坑点速查表

| 问题 | 现象 | 解决/规避 |
|------|------|-----------|
| Cookie 校验无头误判失效 | `cookie_auth` 返回 False，实则有效 | 代码强制 `headless=False` 校验；Linux 需 `DOUYIN_COOKIE_AUTH_HEADLESS=true` + 虚拟显示 |
| 二维码 2 分钟过期 | 手机扫码提示「二维码失效」 | 脚本每 30 秒主动点「刷新」+ 软链自动指向最新 PNG |
| 触发短信/二次验证 | 浏览器弹验证码输入框 | 脚本检测到 `input[placeholder*="验证码"]` → 人工输码，脚本继续等待 |
| 上传页表单 40 秒才渲染 | 选完视频后卡住 | 代码给 `title_input.wait_for(120s)` 超时 |
| 自主声明必选 | 发布页底部「请选择自主声明」 | 代码自动勾选「内容为个人观点或见解」，失败只 warning 不中断 |
| Linux 无头上传 | 无桌面环境 | `xvfb-run -a python sau_cli.py ...` 或配置虚拟显示 |

---

## 文件落盘位置（共享文件夹同步）

```
/home/kan/shared/social-auto-upload/cookies/
├── douyin_her2home.json                    # storage_state（核心登录态）
├── douyin_her2home_latest_qrcode.png       # 固定软链 → 最新二维码
└── douyin_her2home_login_qrcode_*.png      # 历史二维码文件
```

同步到共享文件夹后，Linux 定时任务直接复用 `douyin_her2home.json` 无需重复登录。

---

## 自动化管线集成（每期视频）

马小v 产出 → `/home/kan/shared/her2home/`：
```
video_20260630.mp4      # 视频
video_20260630.png      # 封面（建议同时准备横版/竖版）
video_20260630.json     # 元数据 {title, desc, tags, schedule}
```

上传命令（由 Agent 或 cron 执行）：
```bash
cd /home/kan/shared/social-auto-upload
DATE=20260630
sau douyin upload-video --account her2home \
  --file /home/kan/shared/her2home/video_${DATE}.mp4 \
  --title "$(jq -r .title /home/kan/shared/her2home/video_${DATE}.json)" \
  --desc "$(jq -r .desc /home/kan/shared/her2home/video_${DATE}.json)" \
  --tags "$(jq -r .tags /home/kan/shared/her2home/video_${DATE}.json)" \
  --thumbnail-portrait /home/kan/shared/her2home/video_${DATE}.png \
  --schedule "$(jq -r .schedule /home/kan/shared/her2home/video_${DATE}.json)"
```