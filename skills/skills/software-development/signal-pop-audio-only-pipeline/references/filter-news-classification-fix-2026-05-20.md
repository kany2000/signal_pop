# Filter News Classification Fix (2026-05-20)

## Problem

Daily news pipeline was producing only **7 items instead of 10**, causing broadcast script to have fewer stories than expected.

**User complaint**: "你给我的是10条新闻，为什么播报文稿才7条？"

## Root Causes (Three Bugs)

### Bug 1: `filter_news.py` argparse default value

```python
# WRONG (line 90):
parser.add_argument("--top", type=int, default=7, help="保留新闻条数")
top_n = args.top if args.top else top_n  # if args.top=0, this fails too!

# CORRECT:
parser.add_argument("--top", type=int, default=None, help="保留新闻条数")
top_n = args.top if args.top is not None else top_n  # handles 0 correctly
```

**Impact**: When `generate_audio_only.sh` called `filter_news.py --mode daily` without `--top`, argparse used default=7, bypassing the mode-based logic that should set top_n=10.

### Bug 2: `generate_audio_only.sh` didn't pass `--top` for daily mode

```bash
# WRONG (line 66):
if [ "$MODE" == "weekly" ]; then
    python3 "$SRC_DIR/filter_news.py" --mode "$MODE" --top 12
else
    python3 "$SRC_DIR/filter_news.py" --mode "$MODE"  # ← missing --top 10
fi

# CORRECT:
if [ "$MODE" == "weekly" ]; then
    python3 "$SRC_DIR/filter_news.py" --mode "$MODE" --top 12
else
    python3 "$SRC_DIR/filter_news.py" --mode "$MODE" --top 10
fi
```

### Bug 3: Single-label classification starved tech category

Original logic:
```python
def classify(entry):
    title = entry["title"] + entry.get("summary", "")
    if any(k in title for k in domestic_keywords):
        return "domestic"  # ← stops here, never checks tech
    elif any(k in title for k in tech_keywords):
        return "tech"
    else:
        return "international"
```

**Problem**: Items matching BOTH `domestic_kw` AND `tech_kw` (e.g., "华泰证券：光储板块...") were labeled `domestic` only. This caused:
- `domestic` pool: 4 items (correct)
- `tech` pool: 2 items (should be 3+)
- `international` pool: many items

When allocating `daily=10` as `domestic=4, tech=2, international=4`, the result was only 10 items total, but the filtering logic couldn't fill all slots because `tech` was undersized.

**Additional issue**: Many tech/finance keywords were missing from `tech_kw`:
- Missing: "美联储", "美债", "收益率", "PCB", "光储", "碳酸锂", "网络安全", "Mythos", "TPU", "瑞穗", "美光", "意法半导体", "Humain", "Anthropic", "黑石", "Alphabet"

Items like "美债收益率冲破5%防线" and "华泰证券：光储板块..." were classified as `international` instead of `tech`.

## Solution

### 1. Fix argparse default

```python
parser.add_argument("--top", type=int, default=None, help="保留新闻条数")
args = parser.parse_args()

# mode 决定默认条数：daily=10, weekly=12
top_n = 12 if args.mode == "weekly" else 10
# --top 参数可覆盖默认
top_n = args.top if args.top is not None else top_n
```

### 2. Fix shell script to always pass `--top`

```bash
if [ "$MODE" == "weekly" ]; then
    python3 "$SRC_DIR/filter_news.py" --mode "$MODE" --top 12
else
    python3 "$SRC_DIR/filter_news.py" --mode "$MODE" --top 10
fi
```

### 3. Implement multi-label classification

```python
# Expanded keyword lists
domestic_kw = ["中国", "国内", "北京", "上海", "广东", "A股", "我国", "东风", "岚图", 
               "爱尔眼科", "华泰证券", "国金证券", "万倍认购", "PCB", "港股", "机器人", 
               "港交所", "特斯拉", "苹果", "华为", "抖音", "京东", "阿里", "腾讯", 
               "百度", "字节", "小米", "比亚迪", "宁德时代", "人形机器人"]

tech_kw = ["AI", "人工智能", "ChatGPT", "GPT", "科技", "iPhone", "华为", "芯片", 
           "大模型", "OpenAI", "模型", "融资", "算力", "数据中心", "互联网", "FF", 
           "Faraday", "SpaceX", "特斯拉", "英伟达", "英特尔", "机器人", "Humain", 
           "Anthropic", "Gemini", "DeepSeek", "MiniMax", "黑石", "谷歌", "Alphabet", 
           "美联储", "加息", "降息", "美债", "收益率", "PCB", "光储", "碳酸锂", 
           "算力套餐", "网络安全", "Mythos", "TPU", "瑞穗", "美光", "意法半导体"]

international_kw = ["美国", "欧洲", "英国", "法国", "德国", "日本", "韩国", 
                    "以色列", "伊朗", "俄罗斯", "乌克兰", "特朗普", "普京", "拜登", 
                    "美联储", "NBA", "世界杯", "F1", "王室", "沙特", "PIF"]

def classify(entry):
    title = entry["title"] + entry.get("summary", "")
    # Multi-label: items can be in multiple categories
    cats = []
    if any(k in title for k in domestic_kw):
        cats.append("domestic")
    if any(k in title for k in tech_kw):
        cats.append("tech")
    if not cats:
        cats.append("international")
    return cats  # ← list, not string
```

### 4. Deduplicated allocation

```python
# Build category pools (items can appear in multiple)
by_cat = {"domestic": [], "international": [], "tech": []}
for e in filtered:
    cats = e.get("category", []) if isinstance(e.get("category"), list) else [e.get("category", "international")]
    for cat in cats:
        if cat in by_cat:
            by_cat[cat].append(e)

# Deduplicated pick
seen_ids = set()

def pick_from(cat_list, n, seen):
    result = []
    for e in cat_list:
        eid = id(e)
        if eid not in seen:
            seen.add(eid)
            result.append(e)
        if len(result) >= n:
            break
    return result

# For daily (top_n=10): domestic=3, tech=3, international=4
n_domestic = min(3, len(by_cat["domestic"]))
n_tech = min(3, len(by_cat["tech"]))
n_international = 10 - n_domestic - n_tech

result = []
result += pick_from(by_cat["domestic"], n_domestic, seen_ids)
result += pick_from(by_cat["tech"], n_tech, seen_ids)
result += pick_from(by_cat["international"], n_international, seen_ids)

# Fill remaining if needed
remaining = [e for e in filtered if id(e) not in seen_ids]
result += remaining[:10 - len(result)]
```

### 5. Update `generate_script.py` to handle multi-label

```python
# In both generate_script() and weekly mode main():
cats = item.get("category", [])
if isinstance(cats, list):
    # Priority: domestic > tech > international
    cat = next((c for c in ["domestic", "tech"] if c in cats), "international")
else:
    cat = cats
cat_cn = categories.get(cat, "其他")
lines.append(f"第{i}条，{cat_cn}新闻。{title}。")
```

## Verification

After fixes, `filter_news.py --mode daily --top 10` produces:

```
[filter] 原始 78 条新闻 → 过滤为 10 条
[filter] ✅ 已保存到 /home/kan/signal_pop/data/filtered_news.json
  1. [domestic] 爱尔眼科：公司需补缴税款3.48亿元、滞纳金1.76亿元
  2. [domestic/tech] 美监管机构暂缓部分银行网络安全检查，以评估Mythos相关风险
  3. [domestic/tech] 华泰证券：光储板块开始步入传统出货旺季，短期高景气有望延续
  4. [tech] 沙特AI公司Humain聘请高盛，为数据中心建设筹措超53亿美元融资
  5. [tech] 美债收益率冲破5%防线 全球债市再现抛售风暴
  6. [tech] 8点1氪丨谷歌推出Gemini 3.5系列模型；DeepSeek回应用户"对话泄露"疑虑
  7. [international] 家得宝称关税退款或有助于抵消燃料成本增加的影响
  8. [international] 麦当劳：部分气候目标无法按期实现，将投资10亿美元用于供应链韧性项目
  9. [international] 美国监管机构提议对银行评级体系进行全面改革
  10. [international] Trump-backed challenger defeats Republican rebel M
```

✅ **10 items** (3 domestic, 3 tech, 4 international)

## Files Modified

- `src/filter_news.py`: argparse fix + multi-label classification + expanded keywords
- `scripts/generate_audio_only.sh`: explicit `--top 10` for daily mode
- `src/generate_script.py`: multi-label category read in both daily and weekly paths
