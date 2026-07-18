# social-auto-upload CLI 完整参数参考

来源：项目 `docs/CLI.md`，版本 2026-03-24 重构主线

---

## 关键前置条件（本次会话新增）

**必须在项目目录下运行**，且 `conf.py` 已配置：
```bash
cd /home/kan/shared/social-auto-upload
# 正确入口：项目自带 CLI 模块
python -m sau_cli <platform> <subcommand> --account <account_name>
# 或直接运行
python sau_cli.py <platform> <subcommand> --account <account_name>
```

⚠️ **PyPI `sau` 是另一个工具（AWS EC2 卷导出器），不是本项目 CLI**。安装了也不能用 `sau` 命令直接跑。

**Wrapper 修复**（把入口加到 PATH）：
```bash
cat > /home/kan/shared/social-auto-upload/sau_wrapper.sh << 'EOF'
#!/bin/bash
export PYTHONPATH=/home/kan/shared/social-auto-upload
exec python3 -m sau_cli "$@"
EOF
chmod +x /home/kan/shared/social-auto-upload/sau_wrapper.sh
ln -sf /home/kan/shared/social-auto-upload/sau_wrapper.sh ~/.local/bin/sau
```

---

## 通用参数
```bash
python -m sau_cli <platform> <subcommand> --account <account_name> [--debug] [--headless|--headed]
```
- `--debug`: 失败时保留更多调试信息
- `--headless`: 无头模式（默认）
- `--headed`: 有头模式（需人工看页面时用）

---

## 抖音
```bash
# 登录（生成二维码 PNG，保存到 cookies/ 目录）
python -m sau_cli douyin login --account <name> [--headless]

# 检查 cookie
python -m sau_cli douyin check --account <name>

# 上传视频
python -m sau_cli douyin upload-video --account <name> \
  --file <video.mp4> \
  --title <标题> \
  --desc <简介> \
  --tags <标签1,标签2> \
  --thumbnail <竖版封面.png> \
  --thumbnail-landscape <横版封面.png> \
  --thumbnail-portrait <竖版封面.png> \
  --product-link <商品链接> \
  --product-title <商品标题> \
  --schedule "YYYY-MM-DD HH:MM"

# 上传图文
python -m sau_cli douyin upload-note --account <name> \
  --images <img1.png> <img2.png> ... \
  --title <标题> \
  --note <正文> \
  --tags <标签1,标签2> \
  --schedule "YYYY-MM-DD HH:MM"
```
- 视频封面：支持双比例 `--thumbnail-landscape` (4:3) + `--thumbnail-portrait` (3:4)
- 图文最多 35 张，不支持 GIF

### 抖音二维码登录访问（本次会话新增）

二维码 PNG 生成在：`cookies/douyin_<account>_login_qrcode_YYYYMMDD_HHMMSS.png`

**局域网访问（共享文件夹 HTTP 服务器 10.10.10.30:8080）**：
```
http://10.10.10.30:8080/social-auto-upload/cookies/douyin_her2home_login_qrcode_20260628_225603.png
```

**Tailscale 远程访问（推荐）**：
```
http://100.84.133.58:8080/social-auto-upload/cookies/douyin_her2home_login_qrcode_20260628_225603.png
```

用手机浏览器打开链接，用抖音 APP「扫一扫」登录。扫码后 cookie 自动持久化到 `cookies/` 目录，后续无需重复登录。

---

## B站
```bash
# 登录（建议本地终端执行，二维码可能显示不全，可打开 qrcode.png 扫码）
sau bilibili login --account <name>

# 检查
sau bilibili check --account <name>

# 上传视频
sau bilibili upload-video --account <name> \
  --file <video.mp4> \
  --title <标题> \
  --desc <简介> \
  --tags <标签1,标签2> \
  --tid <分区ID> \
  --thumbnail <横版封面.png> \
  --schedule "YYYY-MM-DD HH:MM"
```
- 必填 `--tid`（分区ID），如 249=科技/数码
- 首次运行自动下载 `biliup`，后续自动检查更新
- 封面仅横版 16:9

---

## 小红书
```bash
# 登录
sau xiaohongshu login --account <name> [--headless]

# 海外环境切换域名
SAU_XHS_CREATOR_BASE_URL=https://creator.rednote.com sau xiaohongshu login --account <name>

# 检查
sau xiaohongshu check --account <name>

# 上传视频
sau xiaohongshu upload-video --account <name> \
  --file <video.mp4> \
  --title <标题> \
  --desc <简介> \
  --tags <标签1,标签2> \
  --thumbnail <封面.png> \
  --schedule "YYYY-MM-DD HH:MM"

# 上传图文
sau xiaohongshu upload-note --account <name> \
  --images <img1.png> <img2.png> <img3.png> \
  --title <标题> \
  --note <正文> \
  --tags <标签1,标签2> \
  --schedule "YYYY-MM-DD HH:MM"
```

---

## 快手
```bash
# 登录
sau kuaishou login --account <name> [--headless]

# 检查
sau kuaishou check --account <name>

# 上传视频
sau kuaishou upload-video --account <name> \
  --file <video.mp4> \
  --title <标题> \
  --desc <简介> \
  --tags <标签1,标签2> \
  --thumbnail <封面.png> \
  --schedule "YYYY-MM-DD HH:MM"

# 上传图文
sau kuaishou upload-note --account <name> \
  --images <img1.png> <img2.png> <img3.png> \
  --title <标题> \
  --note <正文> \
  --tags <标签1,标签2> \
  --schedule "YYYY-MM-DD HH:MM"
```

---

## 视频号（腾讯）
```bash
sau tencent upload-video --account <name> \
  --file <video.mp4> \
  --title <标题> \
  --desc <简介> \
  --schedule "YYYY-MM-DD HH:MM"
```
- 仅 CLI，无 Skill

---

## YouTube
```bash
# 登录（交互式 Google 账号，浏览器完成）
sau youtube login --account <name>

# 检查
sau youtube check --account <name>

# 上传视频
sau youtube upload-video --account <name> \
  --file <video.mp4> \
  --title <标题> \
  --desc <简介> \
  --tags <tag1,tag2> \
  --playlist <播放列表名> \
  --visibility <public|unlisted|private> \
  --schedule "YYYY-MM-DD HH:MM"
```
- 墙内需在 `conf.py` 设置 `YT_PROXY = "http://127.0.0.1:7890"`
- 上传会等进度 100% 再点发布，防止中途被掐断