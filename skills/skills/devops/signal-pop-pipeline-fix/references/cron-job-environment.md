# Cron Job 环境依赖管理 (2026-06-29 新增)

## 问题背景

Cron 任务在系统最小环境下运行，**不加载用户的 `.bashrc` / `.profile`**，也**不激活虚拟环境**。导致：

- `pip install` 的包在 cron 中找不到 (`ModuleNotFoundError: No module named 'feedparser'`)
- `python3` 使用系统 Python，而非项目虚拟环境
- 环境变量缺失 (`PATH`、`HOME`、自定义 `PYTHONPATH` 等)

## 现状排查 (2026-06-29)

```bash
# Crontab 条目
30 8 * * * /home/kan/.hermes/hermes-agent/signal_pop_project/scripts/generate_audio_only.sh daily >> /home/kan/.hermes/hermes-agent/signal_pop_project/logs/cron_daily.log 2>&1
```

**失败日志**：
```
ModuleNotFoundError: No module named 'feedparser'
```

**原因**：`generate_audio_only.sh` 直接调用 `python3 src/fetch_news.py`，使用系统 Python，缺少 `feedparser` 等依赖。

## 修复方案

### 方案 1：在脚本内显式激活虚拟环境 (推荐)

```bash
#!/bin/bash
set -euo pipefail

# 激活项目虚拟环境
VENV_PATH="/home/kan/.hermes/hermes-agent/signal_pop_project/venv"
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
else
    # 回退：尝试用户级虚拟环境
    source "$HOME/.hermes/hermes-agent/venv/bin/activate" 2>/dev/null || true
fi

# 后续 python3 即使用 venv 中的解释器及包
python3 src/fetch_news.py
```

### 方案 2：Crontab 中指定完整 Python 路径

```bash
# 先确认 venv python 路径
/home/kan/.hermes/hermes-agent/signal_pop_project/venv/bin/python3 -c "import feedparser; print(feedparser.__version__)"

# Crontab 写完整路径
30 8 * * * /home/kan/.hermes/hermes-agent/signal_pop_project/venv/bin/python3 /home/kan/.hermes/hermes-agent/signal_pop_project/scripts/generate_audio_only.sh daily >> /home/kan/.hermes/hermes-agent/signal_pop_project/logs/cron_daily.log 2>&1
```

### 方案 3：在脚本开头安装缺失依赖 (临时/一次性)

```bash
# 仅作应急，不建议常态化
python3 -c "import feedparser" 2>/dev/null || pip3 install -r requirements.txt
```

## 验证清单

- [ ] `crontab -l` 确认计划时间
- [ ] 手动执行脚本验证：`bash /path/to/generate_audio_only.sh daily`
- [ ] 查看日志：`tail：`tail -f /path/to/cron_daily.log`
- [ ] 确认输出文件生成：`ls -la output/daily/signal_pop_daily_latest.*`

## 关键路径记录

| 组件 | 路径 |
|------|------|
| 项目根目录 | `/home/kan/.hermes/hermes-agent/signal_pop_project/` |
| 虚拟环境 | `/home/kan/.hermes/hermes-agent/signal_pop_project/venv/` |
| 依赖文件 | `/home/kan/.hermes/hermes-agent/signal_pop_project/requirements.txt` |
| 入口脚本 | `/home/kan/.hermes/hermes-agent/signal_pop_project/scripts/generate_audio_only.sh` |
| 日志目录 | `/home/kan/.hermes/hermes-agent/signal_pop_project/logs/` |
| 输出目录 | `/home/kan/.hermes/hermes-agent/signal_pop_project/output/` |

## 依赖包列表 (requirements.txt)

```
feedparser==6.0.10
python-dotenv==1.0.1
requests==2.31.0
moviepy==2.0.1
edge-tts==7.2.8
openai==2.31.0
```

> **注意**: `moviepy` 依赖 `ffmpeg` 系统包，需确保宿主机已安装：`apt-get install -y ffmpeg`

---

### 本次会话新增 (2026-06-29)
- `signal-pop-daily-check` cron 失败: `ModuleNotFoundError: No module named 'feedparser'`
- 修复: `pip install feedparser==6.0.10` (系统 Python 临时修复)
- 同时验证 `patchright` 依赖已在 venv，cron 需用 venv Python 运行
- 根因: cron 任务直接用 `python3` 调用脚本，未激活 venv，系统 Python 缺包

## 相关技能引用

- `devops/signal-pop-pipeline-fix` — 主流水线修复技能
- `devops/cronjob-troubleshooting` — 通用 Cron 任务排查方法论