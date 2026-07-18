# 2026-06-29 运营实操记录

## 视频文件流转路径
```
马小v 生成 → /home/kan/shared/upload/signal_pop_daily_20260629.mp4
          → 手动复制重命名 → /home/kan/shared/her2home/video_20260629.mp4
封面图已在 → /home/kan/shared/her2home/cover_20260629.png
          → 手动重命名 → /home/kan/shared/her2home/video_20260629.png
JSON 元数据 → 可选，无则用默认值
```

## 关键操作步骤
1. **找到视频**：`find /home/kan/shared -name "*20260629*.mp4" -size +100k`
2. **复制重命名**：`cp /home/kan/shared/upload/signal_pop_daily_20260629.mp4 /home/kan/shared/her2home/video_20260629.mp4`
3. **重命名封面**：`mv /home/kan/shared/her2home/cover_20260629.png /home/kan/shared/her2home/video_20260629.png`
4. **确认无误后**：用户给口头确认 "可以发布了"
5. **执行分发**：`cd /home/kan/shared/social-auto-upload && python auto_publish.py`

## 今日故障与修复
| 故障 | 原因 | 修复 |
|------|------|------|
| 脚本报 "缺少封面" | 封面叫 `cover_20260629.png`，脚本找 `video_20260629.png` | 重命名封面文件 |
| 小红书/快手上传失败 | Playwright Chromium 未安装 | `playwright install chromium` |
| B站上传成功但定时时间可能不对 | JSON 中无 schedule 字段，脚本用默认明天 08:30 | 需检查/补充 JSON 元数据 |

## 发布结果（2026-06-29 22:45）
- ✅ Bilibili：成功（定时 2026-06-30 08:30）
- ❌ 小红书：失败（Playwright chromium 缺失）
- ❌ 快手：失败（Playwright chromium 缺失）
- ⏭️ 抖音：未尝试（前序失败）

## 待办
- [ ] 安装 `playwright install chromium` 修复小红书/快手
- [ ] 补齐 `video_20260629.json` 元数据（标题、简介、标签、定时时间）
- [ ] 重跑分发脚本完成三平台发布
- [ ] 如需 YouTube，修改 `auto_publish.py` PLATFORMS 加入 `"youtube"` 并确保 Cookie 有效