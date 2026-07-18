#!/usr/bin/env python3
"""
Signal Pop — 新闻过滤
按热度和多样性筛选新闻
"""
import os
import json
import sys
import argparse
import html
import re

try:
    from opencc import OpenCC
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False

# 繁体转简体转换器
if HAS_OPENCC:
    cc = OpenCC('t2s')
else:
    cc = None

# 过滤关键词：体育、娱乐八卦、财经行情、博彩广告
SPAM_KEYWORDS = [
    # 体育赛事
    "世界杯", "世杯", "FIFA", "欧冠", "英超", "西甲", "意甲", "德甲", "法甲",
    "NBA", "CBA", "奥运", "亚运", "网球", "高尔夫", "F1", "一级方程式",
    "裁判", "进球", "比分", "赛程", "积分榜", "出线", "淘汰赛", "小组赛",
    # 娱乐八卦
    "票房", "电影", "影片", "上映", "演员", "明星", "综艺", "选秀",
    "玩具总动员", "漫威", "迪士尼", "好莱坞", "奥斯卡", "金鸡奖", "华表奖",
    # 财经行情（非新闻类）
    "美元指数", "期铜", "期货", "收盘", "开盘", "涨停", "跌停", "主力资金",
    "北向资金", "融资余额", "融券余额", "换手率", "市盈率", "市净率",
    "LME", "COMEX", "NYMEX", "现货黄金", "现货白银", "WTI", "布伦特",
    # 博彩/广告
    "点击浏览", "即时更新", "精彩进球", "即时比数", "万勿错过",
    "竞猜", "投注", "赔率", "盘口", "水位", "博彩", "体彩", "福彩",
    # 低质内容
    "测试", "quiz", "Quiz", "是什么", "是什么类型", "你是什么",
]

def is_spam(title, summary):
    """检测是否为垃圾/低质内容"""
    text = (title + " " + summary).lower()
    for kw in SPAM_KEYWORDS:
        if kw.lower() in text:
            return True
    # 检测全英文标题（可能未翻译）
    if re.match(r'^[A-Za-z\s\.,\-\'\?]+$', title.strip()) and len(title) > 5:
        return True
    # 检测以英文单词开头且包含典型英文结构的标题
    if re.match(r'^[A-Z][a-z]+\s+[a-z]+', title.strip()) and len(title.split()) >= 3:
        # 进一步检查是否包含中文字符
        if not re.search(r'[\u4e00-\u9fff]', title):
            return True
    # 检测包含大量英文单词、无中文的标题（如 "James Burrows, legendary director of Cheers and Fr"）
    words = title.split()
    english_words = sum(1 for w in words if re.match(r'^[A-Za-z\.\,\-]+$', w))
    if len(words) >= 4 and english_words / len(words) > 0.7 and not re.search(r'[\u4e00-\u9fff]', title):
        return True
    return False


def to_simplified(text):
    """繁体转简体"""
    if cc and text:
        return cc.convert(text)
    return text


def decode_html(text):
    """解码 HTML 实体"""
    return html.unescape(text) if text else text

OUTPUT_DIR = "/home/kan/signal_pop/data"
DATA_DIR = "/home/kan/signal_pop/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def filter_news(raw_entries, top_n=10, min_length=10):
    """
    过滤新闻：
    1. 去除标题过短或重复
    2. 过滤体育/娱乐/财经行情/博彩等垃圾内容
    3. 解码 HTML 实体、繁体转简体
    4. 按来源均衡分布（国内/国际/科技）
    5. 保留摘要最完整的
    """
    seen_titles = set()
    filtered = []

    # 1. 去重 + 长度过滤 + 垃圾内容过滤 + 清理
    for e in raw_entries:
        title = decode_html(e["title"]).strip()
        title = to_simplified(title)
        summary = decode_html(e.get("summary", "")).strip()
        summary = to_simplified(summary)

        if len(title) < min_length:
            continue
        if is_spam(title, summary):
            continue
        # 简单相似度去重（标题前30字相同则视为重复）
        key = title[:30]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        e["title"] = title
        e["summary"] = summary
        filtered.append(e)

    # 分类标签
    domestic_kw = ["中国", "国内", "北京", "上海", "广东", "A股", "我国", "东风", "岚图", "爱尔眼科", "华泰证券", "国金证券", "万倍认购", "PCB", "港股", "机器人", "港交所", "特斯拉", "苹果", "华为", "抖音", "京东", "阿里", "腾讯", "百度", "字节", "小米", "比亚迪", "宁德时代", "人形机器人"]
    tech_kw = ["AI", "人工智能", "ChatGPT", "GPT", "科技", "iPhone", "华为", "芯片", "大模型", "OpenAI", "模型", "融资", "算力", "数据中心", "互联网", "FF", "Faraday", "SpaceX", "特斯拉", "英伟达", "英特尔", "机器人", "Humain", "Anthropic", "Gemini", "DeepSeek", "MiniMax", "黑石", "谷歌", "Alphabet", "美联储", "加息", "降息", "美债", "收益率", "PCB", "光储", "碳酸锂", "算力套餐", "网络安全", "Mythos", "TPU", "瑞穗", "美光", "意法半导体"]
    international_kw = ["美国", "欧洲", "英国", "法国", "德国", "日本", "韩国", "以色列", "伊朗", "俄罗斯", "乌克兰", "特朗普", "普京", "拜登", "美联储", "沙特", "PIF"]

    def classify(entry):
        title = entry["title"] + entry.get("summary", "")
        # 多标签：同时包含 domestic 和 tech 时，同时标记两个类别
        cats = []
        if any(k in title for k in domestic_kw):
            cats.append("domestic")
        if any(k in title for k in tech_kw):
            cats.append("tech")
        if not cats:
            cats.append("international")
        return cats  # 返回列表，支持多标签

    for e in filtered:
        e["category"] = classify(e)

    # 均衡各类别的数量（daily=10条：国内3，国际4，科技3）
    by_cat = {"domestic": [], "international": [], "tech": []}
    for e in filtered:
        cats = e.get("category", []) if isinstance(e.get("category"), list) else [e.get("category", "international")]
        for cat in cats:
            if cat in by_cat:
                by_cat[cat].append(e)

    # 去重（同一新闻可能在多个类别出现，取前N条时不重复）
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

    if top_n == 10:
        # daily: domestic=3, tech=3, 剩余用 international 补足到10
        n_domestic = min(3, len(by_cat["domestic"]))
        n_tech = min(3, len(by_cat["tech"]))
        n_international = top_n - n_domestic - n_tech
    elif top_n >= 10:
        # weekly (12+条): 灵活分配
        n_domestic = min(5, len(by_cat["domestic"]))
        n_tech = min(4, len(by_cat["tech"]))
        n_international = top_n - n_domestic - n_tech
    else:
        n_domestic = min(2, len(by_cat["domestic"]))
        n_tech = min(1, len(by_cat["tech"]))
        n_international = top_n - n_domestic - n_tech

    result = []
    result += pick_from(by_cat["domestic"], n_domestic, seen_ids)
    result += pick_from(by_cat["tech"], n_tech, seen_ids)
    result += pick_from(by_cat["international"], n_international, seen_ids)

    # 如果还不够 top_n，从剩余里补（排除已选）
    remaining = [e for e in filtered if id(e) not in seen_ids]
    result += remaining[:top_n - len(result)]

    return result[:top_n]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=7, help="保留新闻条数")
    parser.add_argument("--mode", default="daily", choices=["daily", "weekly"], help="daily=7条 weekly=10条")
    args = parser.parse_args()

    # mode 决定默认条数：daily=10, weekly=12
    top_n = 12 if args.mode == "weekly" else 10
    # --top 参数可覆盖默认
    top_n = args.top if args.top is not None else top_n

    raw_path = f"{DATA_DIR}/raw_feed.json"
    if not os.path.exists(raw_path):
        print(f"[filter] ❌ {raw_path} 不存在，请先运行 fetch_news.py", file=sys.stderr)
        sys.exit(1)

    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)

    print(f"[filter] 原始 {len(raw)} 条新闻 → 过滤为 {top_n} 条")

    filtered = filter_news(raw, top_n=top_n)

    out_path = f"{DATA_DIR}/filtered_news.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"[filter] ✅ 已保存到 {out_path}")
    for i, e in enumerate(filtered, 1):
        cats = e.get("category", [])
        if isinstance(cats, list):
            cat_str = "/".join(cats)
        else:
            cat_str = str(cats)
        print(f"  {i}. [{cat_str}] {e['title'][:50]}")


if __name__ == "__main__":
    main()
