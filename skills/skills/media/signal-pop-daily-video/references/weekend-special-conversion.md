# 周末特别版新闻稿 → 标准 TTS/视频 格式转换

每周五制作周末特别版（15条，Markdown 格式 `signal_pop_weekly_special_YYYYMMDD.txt`）。转换需要两步。

## 第一步：检测新闻稿

```bash
read_file("archive/signal_pop_weekly_special_YYYYMMDD.txt")
# 确认标题含【周末特别版】、3 个分类、5 条评论观点
```

## 第二步：写入转换脚本

一次性写入 `/tmp/convert_weekly_special.py`。核心转换逻辑：

1. 按行解析 `N. **标题**` 结构，提取编号、标题、正文、评论
2. 按编号范围分配分类标签（1-5:科技新闻, 6-10:国内新闻, 11-15:国际新闻）
3. 评论行标识为 `👉 *[主播观点]*：`，提取后加 `主播观点：` 前缀
4. 日期使用 `DATE+1`（发布日），开场用 `PUB_STR` + `PUB_WD`
5. 输出到 `archive/signal_pop_daily_YYYYMMDD.txt`

### 常见解析残留

转换后必须检查输出的内容：

- **分类行残留**：`据综合报道，【国内与社会】。` → regex 清除
- **Markdown 分段标记**：`---` → 整行跳过
- **元数据行**：`🎙️ 今天主播：图图`、`✨ 互动话题`、`感谢您的关注` → 整行跳过
- **双句号**：`。。` → regex replace

清洗小脚本模式：

```python
import re
text = open(path).read()
text = re.sub(r'据综合报道，.*?。', '', text)  # 分类残留
text = re.sub(r'。。', '。', text)                # 双句号
lines = [l for l in text.split('\n') if re.match(r'^[\*🎙️✨\-━]', l) is None]
text = '\n'.join(filter(None, lines))
```

## 参考：2026-07-10 的转换结果

- 输入：`archive/signal_pop_weekly_special_20260710.txt`（35行，15条+5条评论）
- 输出：`archive/signal_pop_daily_20260710.txt`（22行，15条）
- 最终 TTS：1444 chars, 16 segments, ~4分46秒
- 配图：15张+opening，用 Pollinations batch 生成（每条新闻独立场景，避免重复）