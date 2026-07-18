---
name: signal-pop-news-select
description: 从 RSS 抓取的新闻池中挑选最适合做成视频的稿件。按时效性、热度、话题多样性、来源均衡、质量过滤等多维度 AI 筛选，输出结构化新闻列表供下游管线使用。
tags:
  - signal-pop
  - news-pipeline
  - content-selection
  - chinese-nlp
  - ai-filtering
category: software-development
---

# Signal Pop 新闻稿选择

## 用途

从 `filter_news.py` 输出的 `filtered_news_*.json` 中，用 AI 挑选 **10 条**最适合做成视频的新闻，输出结构化 JSON，可直接喂给 `generate_script.py`。

## 选择标准

| 维度 | 权重 | 说明 |
|------|------|------|
| 时效性 | ★★★★★ | 优先选 48h 内的新闻，剔除旧闻/过期事件 |
| 话题多样性 | ★★★★ | 均衡覆盖 domestic / international / tech，避免扎堆同一话题 |
| 来源均衡 | ★★★ | 分散不同 RSS 源（腾讯/澎湃/BBC/36kr/路透），不集中一家 |
| 内容质量 | ★★★★ | 摘要完整含数据/细节，拒绝标题党、空洞、营销软文 |
| 热度/影响力 | ★★★ | 优先选涉及大公司、政策变化、重大事件、社会广泛关注的 |
| 适合播报 | ★★★ | 适合口播的叙事型新闻，拒绝纯数据行情、赛况、榜单 |

## 排除规则

- 体育赛事（世界杯/欧冠/NBA/奥运等）
- 娱乐八卦（电影/明星/综艺/票房）
- 财经行情（指数/期货/汇率/涨跌）
- 博彩/广告/竞猜内容
- 全英文标题（未翻译）
- 摘要过短（<50 字）或纯重复内容
- 明显旧闻（日期早于 7 天前）
- 纯技术参数发布（无社会影响）

## 用法

### 方式一：指定 JSON 文件路径

```
/signal-pop-news-select path=E:/projects/signal_pop/archive/filtered_news_20260716_153642.json
```

### 方式二：粘贴 JSON 内容

直接将 `filtered_news_*.json` 的内容粘贴到对话中，skill 会自动识别。

## 输出格式

```json
[
  {
    "title": "新闻标题",
    "link": "原文链接",
    "source": "来源名称",
    "published": "2026-07-16T10:30:00",
    "summary": "摘要正文（100字以内）",
    "category": ["domestic"],
    "selection_reason": "选择理由：时效性高、涉及民生政策、影响面广"
  }
]
```

## 工作流程

```
用户输入 JSON 或文件路径
        │
        ▼
  Step 1: 解析输入
  - 读取 JSON 文件或解析粘贴内容
  - 提取每条新闻的 title/summary/source/published/category
        │
        ▼
  Step 2: AI 初筛
  - 应用排除规则（体育/娱乐/行情/过期/低质）
  - 标记并剔除不合格条目
        │
        ▼
  Step 3: AI 精选
  - 从合格池中按 6 维标准打分
  - 确保话题多样性（domestic 4-5条 / international 3-4条 / tech 2-3条）
  - 确保来源分散
  - 取 Top 10
        │
        ▼
  Step 4: 输出
  - 显示选中列表及每条选择理由
  - 输出 JSON 格式文本（可直接复制到 generate_script.py）
  - 可选：直接写入文件供下游使用
```

## 输出示例

```
✅ 精选完成，共 10 条

┌────┬──────────────────────────────────┬──────────┬─────────────┐
│ #  │ 标题                            │ 来源     │ 分类        │
├────┼──────────────────────────────────┼──────────┼─────────────┤
│  1 │ 国务院发布促进民营经济发展报告  │ 澎湃新闻 │ domestic    │
│  2 │ 欧盟对华电动汽车加征关税生效    │ 路透中文 │ international│
│  3 │ 华为发布新一代AI芯片昇腾910C    │ 36kr     │ tech        │
│ ...│ ...                              │ ...      │ ...         │
└────┴──────────────────────────────────┴──────────┴─────────────┘

JSON 输出已就绪，可直接复制或写入文件。
```

## 与管线集成

选中后可直接管道到下游：

```bash
# 保存到文件供 generate_script.py 使用
python -c "import json; json.dump(selected_items, open('E:/projects/signal_pop/data/selected_news.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)"

# 直接喂给脚本生成器
python src/generate_script.py 20260716 daily
```

## 注意事项

- 输入文件必须是 `filter_news.py` 输出的标准格式
- 如果新闻池不足 10 条合格条目，按实际数量输出
- 允许用户指定偏好（如：侧重科技新闻、或增加国际新闻比例）
- 允许用户手动增删调整后再输出