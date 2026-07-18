---
name: signal-pop-image-generation
description: 信号弹新闻配图自动化。为 signal_pop daily/weekly 新闻稿生成新闻配图。Sensenova-u1-fast 首引擎，Pollinations 备选降级。
---

# 信号弹新闻配图自动化

为 Signal Pop (隔天信号弹) 新闻稿自动生成配图。

## 定时任务

- **Cron job ID:** `92ef826414c5`
- **Schedule:** `30 9 * * 0,2,4,5` (每周日/二/四/五 09:30)
- **触发时机:** 新闻稿 09:00 出稿后 30 分钟自动运行
- **触发脚本:** `gen_news_images.py`（自动匹配，适合无人值守 cron）

## 数据源

- **Daily:** `/home/kan/shared/signal_pop/archive/signal_pop_daily_YYYYMMDD.txt`
- **Weekly:** `/home/kan/shared/signal_pop/archive/signal_pop_weekly_YYYYMMDD.txt`

## 输出路径

- **Daily 配图:** `/home/kan/shared/signal_pop/archive/img_YYYYMMDD/` (01.jpg ~ NN.jpg, 2752×1536)
- **Weekly 配图:** `/home/kan/shared/signal_pop/archive/img_weekly_YYYYMMDD/`

## 配图引擎（2026-07-12 更新）

**Sensenova-u1-fast 优先 → Pollinations 备选降级**

```
gen_image(prompt, seed)
  ├─ Sensenova-u1-fast POST → 2752×1536 PNG → 转 JPEG → 返回 ✓
  └─ 失败 → Pollinations 1280×720 → 返回 ✓
```

### Sensenova API

- **端点**: `https://token.sensenova.cn/v1/images/generations`
- **Key**: `sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ`
- **模型**: `sensenova-u1-fast`（固定）
- **尺寸**: `2752x1536`（16:9），支持 11 种固定比例：
  `1664x2496(2:3) 2496x1664(3:2) 1760x2368(3:4) 2368x1760(4:3) 1824x2272(4:5) 2272x1824(5:4) 2048x2048(1:1) 2752x1536(16:9) 1536x2752(9:16) 3072x1376(21:9) 1344x3136(9:21)`
- **prompt**: 最大 4096 tokens
- **n**: 默认 1
- **请求格式**: OpenAI-compat JSON
- **耗时**: ~30s/张
- **中文字符渲染**: 清晰锐利
- **人像**: 仍有变形风险（同 Pollinations），优先用无人物场景

### 客户端

脚本 `/home/kan/shared/signal_pop/scripts/sensenova_client.py` 提供 `gen_image(prompt, seed)` 和 `gen_image_file(prompt, out_path, seed)` 两个函数，内置 Sensenova→Pollinations 降级。可直接调用：

```python
from sensenova_client import gen_image_file
path, source = gen_image_file("news studio, modern", "/tmp/out.jpg", seed=42)
# source == "sensenova" 或 "pollinations" 或 "failed"
```

### 降级触发条件

- Sensenova API 返回 error / timeout / 无 URL / 图片 < 10KB
- 自动回退到 Pollinations 1280×720
- 两者都失败 → 抛出异常，cron 日志可追踪

## 主脚本

**`/home/kan/shared/signal_pop/scripts/gen_news_images.py`** — 自动版（cron 调用）

- 正则 `^第N条，类别。标题。` 提取标题
- `keyword_map` 匹配关键词生成英文 prompt
- 每条 `gen_image(prompt, n*37)` → Sensenova 优先
- 已存在图片跳过（幂等）
- 同时处理 daily 和 weekly 两份新闻稿
- 输出 2752×1536 16:9 JPEG（Sensenova 成功时），或 1280×720（降级时）

**`/home/kan/shared/signal_pop/scripts/gen_custom_images.py`** — 手动定制版

- 编辑 `prompts` 数组为每条新闻写独立英文 prompt
- 同样走 Sensenova→Pollinations 降级
- 适合需要精细控制每条配图场景时使用

## 与视频管线关系

```
新闻稿 → gen_news_images.py (Sensenova) → img_YYYYMMDD/01-10.jpg
        → tts_mimo 语音 → build_daily_video.py 合成MP4 → her2home/ → auto_publish 分发
```

## Prompt 编写规则

- **基于标题具体场景**：描述画面细节而非抽象概念
- **每条 prompt 开头不同**：描述维度差异化（光线/人物/地点/动作）
- **避免通用模板**：不要 "AI technology concept" 这种万能词
- **中文地名/人名**：用英文表达（"White House" "China"）
- **风格后缀可选**：newspaper illustration / documentary photo / cinematic / flat illustration
- **地理类配图必须准确**：用卫星鸟瞰 + 真实地理坐标 + 海岸线/海峡等具体描述

## 人脸变形规避（重要）

Sensenova 和 Pollinations 在正面人脸时都可能变形。**策略：**

- **优先选无人的场景**：用建筑/风景/静物代替有人场景
- **"no people" 关键词**：prompt 末尾加 `, no people, empty scene`
- **背影/侧面可接受**：如果必须有人，用背影或极侧角度
- **人群用远景**：小比例背景人物不会触发脸部变形
- **正面特写避免**：永远不要用 "close-up portrait" "a man smiling" 等提示
- **遇变形立即换**：不要等"下次重试"，立刻换无人物 prompt 重生成

### Prompt 示例

| 原始（可能崩脸） | 改进（无脸） |
|---|---|
| A doctor checking medicine | A hospital pharmacy with medicine bottles on shelves, clean lighting, no people |
| Customers eating at hotpot restaurant | Interior of a restaurant with steam rising, warm lighting, empty tables |
| A scientist working in lab | A chemistry laboratory with glass equipment and blue liquid, no people |
| Movie star at premiere | Movie theater screen with red curtain and empty seats, dramatic spotlight |

## 质量监控清单

- **脚本执行状态** — `cronjob list` 看 `last_status`
- **图片数量** — `ls archive/img_YYYYMMDD/*.jpg | wc -l`（daily=10，weekly=5）
- **图片大小** — 每张 50KB+（Sensenova 成功时 ~500KB-1MB）
- **内容匹配度** — vision 工具抽检 3-5 张

## 注意事项

1. **日期必须匹配** — 脚本按当天日期找文件
2. **周六 weekly 不在 cron 中** — 周六 weekly 新闻稿需手动跑脚本
3. **脚本是幂等的** — 重复运行会覆盖已有图片
4. **Gateway 启动依赖** — cron scheduler 在 Hermes gateway 启动后才激活（gateway 09:01 启动）
5. **Sensenova 耗时约 30s/张** — 10 张全量约 5 分钟，cron 的 600s 超时足够