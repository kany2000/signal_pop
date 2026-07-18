# social-auto-upload 多平台自动分发部署记录

## 项目概况
- **仓库**: https://github.com/dreammis/social-auto-upload (13k⭐)
- **部署路径**: `/home/kan/shared/social-auto-upload`
- **CLI 入口**: `sau` (已链接到 `/home/kan/.hermes/hermes-agent/venv/bin/sau`)
- **支持平台**: 抖音、B站、小红书、快手、视频号、百家号、TikTok、YouTube

## 核心能力
- ✅ 视频上传 + 封面图 (横版/竖版分平台)
- ✅ 定时发布 (`--schedule "YYYY-MM-DD HH:MM"`)
- ✅ 多账号管理 (`--account <name>`)
- ✅ 无头模式 (服务器可跑)
- ✅ 统一 CLI: `sau douyin|bilibili|xiaohongshu|kuaishou|...`
- ✅ AI Agent Skill 内置 (douyin-upload, bilibili-upload, xiaohongshu-upload, kuaishou-upload)
- ✅ **YouTube 支持**: `sau youtube upload-video --account her2home --file ... --title ... --desc ... --tags ... --thumbnail ... --playlist ... --visibility public` (已实现，`auto_publish.py` 的 `PLATFORMS` 列表未启用，需手动加入 `"youtube"` 即可)

## 部署步骤
```bash
# 1. 克隆安装
cd /home/kan/shared
git clone https://github.com/dreammis/social-auto-upload
cd social-auto-upload
uv pip install -e .

# 2. 安装浏览器 (patchright 而非 playwright)
patchright install chromium  # 官方 CDN 下载，无需镜像

# 3. 配置 conf.py (复制 conf.example.py)
cp conf.example.py conf.py

# 4. 登录各平台 (首次扫码，后续复用 cookies)
./login_all_platforms.sh  # 或逐个: sau douyin login --account her2home --headless
```

**关键坑点 (本次会话新增)**:
- ❌ **必须用 `patchright install chromium`，而非 `playwright install chromium`**: 项目依赖 `patchright` (playwright 的反检测 fork)，安装的是 `chromium-1208` 版本，**`playwright install` 装的是另一套路径，导致 `Executable doesn't exist` 报错**
- ✅ **验证命令**: `python -c "from patchright.async_api import async_playwright; import asyncio; async def t(): async with async_playwright() as p: b = await p.chromium.launch(headless=True); await b.close(); asyncio.run(t())"`

## 修复记录: 抖音登录 Bug
**文件**: `uploader/douyin_uploader/main.py`  
**函数**: `_wait_for_douyin_login()` (line ~173)  
**问题**: `original_url`、`saw_2fa`、`i` 变量未定义  
**修复**: 在循环前初始化三个变量
```python
original_url = page.url
saw_2fa = False
for i in range(max_checks):
```

## 自动分发脚本
**文件**: `/home/kan/shared/social-auto-upload/auto_publish.py`  
**功能**:
- 扫描 `/home/kan/shared/her2home/` 下 `*.mp4` + 同名 `*.png/*.jpg` + `*.json`
- 读取 JSON 元数据 (title, desc, tags, schedule)
- **顺序分发** (非并行，避免浏览器冲突) 到 B站、小红书、快手 (抖音待登录，YouTube CLI 支持但 PLATFORMS 未启用)
- 平台特定参数: 小红书/快手 `--headless` + `--thumbnail`，B站 `--tid 249` 无封面参数
- 发布状态持久化到 `.publish_state.json`，**同一文件名绝不重复上传**
- **人工确认发布流程 (本次会话新增)**: 用户要求**每期视频发布前人工确认** — 完整流水线跑完生成视频后，**不自动分发**，等用户确认 "可以发布" 再执行上传。当前 cron 任务均已暂停，改为手动触发模式。

## Cron 任务 (已部署)
| 任务 | Job ID | 频率 | 用途 |
|------|--------|------|------|
| 监控马小v视频输出 | cbef28c8adaa | 10:30, 16:30 | 检查文件完整性、报警 |
| Signal Pop 自动分发 | 48d0d0f155f1 | 10:30, 16:30 | 扫描新视频并行分发 |

**时间链路**:
- 虾小图 8:00-8:30 出稿
- 马小v ~10:00 出片放入 `/home/kan/shared/her2home/`
- **10:30** 检测分发 (赶次日 8:30 定时发布)
- **16:30** 兜底 (防漏跑/补发)

## 视频投放格式要求
马小v 产出时需放 3 个文件到 `/home/kan/shared/her2home/`:
```
video_YYYYMMDD.mp4      # 视频 (马小v实际产出名: signal_pop_daily_YYYYMMDD.mp4)
video_YYYYMMDD.png      # 封面 (马小v实际产出名: cover_YYYYMMDD.png，**需重命名**为 video_ 前缀)
video_YYYYMMDD.json     # 元数据 (可选，缺失时 auto_publish.py 使用默认值)
```

**关键坑点 (本次会话新增)**:
- ❌ **封面命名必须匹配**: auto_publish.py 扫描 `video_YYYYMMDD.mp4` 时查找同名 `video_YYYYMMDD.png`/`video_YYYYMMDD.jpg`，**`cover_YYYYMMDD.png` 会被忽略导致 "缺少封面" 报错**
- ❌ **JSON 可选但建议提供**: 无 JSON 时标题默认 `隔天信号弹 MM.DD`，简介/标签用内置默认值
- ✅ **修正流程**: 马小v 产出后，需手动 `cp signal_pop_daily_YYYYMMDD.mp4 video_YYYYMMDD.mp4` + `mv cover_YYYYMMDD.png video_YYYYMMDD.png`

**JSON 模板** (`video_YYYYMMDD.json.example`):
```json
{
  "title": "隔天信号弹 6.28｜标题",
  "desc": "简介内容...",
  "tags": "隔天信号弹,AI,科技",
  "schedule": "2026-06-28 08:30"  // 选填，不填默认次日 8:30
}
```

## 登录维护
- Cookies 保存在 `/home/kan/shared/social-auto-upload/cookies/`
- 账号名: `her2home` (统一)
- Cookie 失效时重新执行 `./login_all_platforms.sh` 扫码即可
- 建议定期 `sau douyin check --account her2home` 验证

## 相关文件
- `/home/kan/shared/social-auto-upload/login_all_platforms.sh` — 一键登录 4 平台
- `/home/kan/shared/social-auto-upload/auto_publish.py` — 自动分发主脚本
- `/home/kan/shared/social-auto-upload/sau_wrapper.sh` — sau CLI 包装器 (设置 PYTHONPATH)
- `/home/kan/shared/her2home/.publish_state.json` — 发布状态记录 (自动生成)