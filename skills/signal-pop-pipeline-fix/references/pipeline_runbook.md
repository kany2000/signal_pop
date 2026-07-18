# Signal Pop 监控流水线 - 运行记录与关键点

## 流水线架构

```
人工选题 (虾小图)
    │
    ▼
/home/kan/shared/signal_pop/filtered_news.json  ← 人工投放入口
    │
    ▼
monitor_pipeline.py (cron 每 10 分钟)
    │
    ├─► 复制到 data/filtered_news.json
    ├─► generate_script.py daily → output/daily/signal_pop_daily_YYYYMMDD.txt
    ├─► tts_mimo.py --female → output/daily/signal_pop_daily_YYYYMMDD_female.mp3
    ├─► tts_mimo.py --male   → output/daily/signal_pop_daily_YYYYMMDD_male.mp3
    └─► 归档 → archive/filtered_news_YYYYMMDD_HHMMSS.json
```

## 关键设计决策

### 1. 内容 Hash 去重
- 使用 SHA-256 对文件全内容计算 hash
- 避免 mtime 变化导致的误判（如文件复制、同步工具修改时间戳）
- 状态文件：`/home/kan/signal_pop/.pipeline_state.json`

### 2. 原子性归档
- 先计算 stat/hash，再执行 `shutil.move()`
- 避免移动后无法 stat 原路径的 FileNotFoundError

### 3. 双声道 TTS 并行化潜力
当前串行执行（女声 → 男声），未来可优化为并行：
```python
# 并行版本示例
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=2) as executor:
    executor.submit(run_tts, "female")
    executor.submit(run_tts, "male")
```

## 常见问题排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 重复生成同期内容 | hash 计算错误或状态文件丢失 | 检查 `.pipeline_state.json` 完整性 |
| TTS 超时 | MiMo API 响应慢 | 增加 timeout 或添加重试逻辑 |
| 归档失败 | 权限不足 | 确保 archive 目录可写 |
| 无新文件但反复触发 | 状态文件损坏 | 删除 `.pipeline_state.json` 重建 |

## 环境依赖
- Python 3.11+
- `opencc-python-reimplemented` (filter_news.py)
- `requests` (generate_script.py, tts_mimo.py)
- `ffmpeg` (tts_mimo.py MP3 转换)
- 环境变量：`MIMO_API_KEY`, `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`

## 部署检查清单
- [ ] 共享目录存在：`/home/kan/shared/signal_pop/`
- [ ] 归档目录存在：`/home/kan/shared/signal_pop/archive/`
- [ ] 输出目录存在：`/home/kan/signal_pop/output/daily/`
- [ ] 状态文件可写：`/home/kan/signal_pop/.pipeline_state.json`
- [ ] cron 任务已配置并测试通过

## 已部署 Cron 任务记录 (2026-06-22)

| 任务名 | Job ID | 计划 | 方式 | 状态 |
|--------|--------|------|------|------|
| signal-pop-monitor | 9967e8b8c86f | `*/10 * * * *` | Monitor (human-in-the-loop) | 已启用 |
| signal-pop-weekly | 7968abe94f69 | `0 9 * * 6` (周六 09:00) | Weekly 生成 | 已启用 |
| signal-pop-daily-news | 02d2c8d722bb | `30 8 * * 1,3,5` | 脚本方式 (兼容) | 已启用 |
| signal-pop-weekly-news | b231e16a2ec3 | `0 9 * * 6` | 脚本方式 (兼容) | 已启用 |
| signal-pop-daily-check | d065a67164a0 | `0 9 * * 1,3,5` | 健康检查 | 已启用 |

> **推荐流程**: Monitor 方式为主。虾小图在发布日将 `filtered_news.json` 放入 `/home/kan/shared/signal_pop/`，monitor 任务在 10 分钟内自动完成全流水线。脚本方式 cron 保留作为兼容/回退。