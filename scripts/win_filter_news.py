#!/usr/bin/env python3
"""Signal Pop — 临时新闻过滤脚本（Windows版）"""
import os, sys, json, html, re

DATA_DIR = "E:/projects/signal_pop/output"
OUTPUT_DIR = "E:/projects/signal_pop/output"

SPAM_KEYWORDS = [
    "世界杯", "FIFA", "欧冠", "英超", "西甲", "NBA", "CBA", "奥运", "亚运",
    "票房", "电影", "上映", "演员", "明星", "综艺", "选秀",
    "美元指数", "期铜", "期货", "收盘", "开盘", "涨停", "跌停",
    "竞猜", "投注", "赔率", "博彩", "体彩", "福彩",
    "测试", "quiz",
]

def is_spam(title, summary):
    text = (title + " " + summary).lower()
    for kw in SPAM_KEYWORDS:
        if kw.lower() in text:
            return True
    words = title.split()
    english_words = sum(1 for w in words if re.match(r'^[A-Za-z\.\,\-]+$', w))
    if len(words) >= 4 and english_words / len(words) > 0.7 and not re.search(r'[一-鿿]', title):
        return True
    return False

def filter_news(raw_entries, top_n=10):
    seen_titles = set()
    filtered = []
    for e in raw_entries:
        title = html.unescape(e["title"]).strip()
        summary = html.unescape(e.get("summary", "")).strip()
        if len(title) < 5:
            continue
        if is_spam(title, summary):
            continue
        key = title[:30]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        e["title"] = title
        e["summary"] = summary
        filtered.append(e)

    domestic_kw = ["中国", "国内", "北京", "上海", "广东", "A股", "我国", "华为", "抖音", "京东", "阿里", "腾讯", "百度", "小米", "比亚迪", "宁德时代", "机器人"]
    tech_kw = ["AI", "人工智能", "ChatGPT", "GPT", "科技", "iPhone", "华为", "芯片", "大模型", "OpenAI", "模型", "融资", "算力", "数据中心", "英伟达", "谷歌", "DeepSeek", "特斯拉", "SpaceX", "机器人"]
    international_kw = ["美国", "欧洲", "英国", "法国", "德国", "日本", "韩国", "以色列", "伊朗", "俄罗斯", "乌克兰", "特朗普", "普京", "拜登"]

    def classify(entry):
        title = entry["title"] + entry.get("summary", "")
        cats = []
        if any(k in title for k in domestic_kw): cats.append("domestic")
        if any(k in title for k in tech_kw): cats.append("tech")
        if not cats: cats.append("international")
        return cats

    for e in filtered:
        e["category"] = classify(e)

    by_cat = {"domestic": [], "international": [], "tech": []}
    for e in filtered:
        for cat in e.get("category", ["international"]):
            if cat in by_cat:
                by_cat[cat].append(e)

    seen_ids = set()
    def pick_from(cat_list, n, seen):
        result = []
        for e in cat_list:
            if id(e) not in seen:
                seen.add(id(e))
                result.append(e)
            if len(result) >= n: break
        return result

    n_domestic = min(3, len(by_cat["domestic"]))
    n_tech = min(3, len(by_cat["tech"]))
    n_international = top_n - n_domestic - n_tech

    result = []
    result += pick_from(by_cat["domestic"], n_domestic, seen_ids)
    result += pick_from(by_cat["tech"], n_tech, seen_ids)
    result += pick_from(by_cat["international"], n_international, seen_ids)
    remaining = [e for e in filtered if id(e) not in seen_ids]
    result += remaining[:top_n - len(result)]
    return result[:top_n]

def main():
    raw_path = os.path.join(DATA_DIR, "raw_feed.json")
    if not os.path.exists(raw_path):
        print(f"[filter] {raw_path} 不存在")
        sys.exit(1)
    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)
    print(f"[filter] 原始 {len(raw)} 条")
    filtered = filter_news(raw, top_n=10)
    out_path = os.path.join(OUTPUT_DIR, "filtered_news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    print(f"[filter] 筛选出 {len(filtered)} 条")
    for i, e in enumerate(filtered, 1):
        print(f"  {i}. {e['title'][:60]}")
    print(f"[filter] -> {out_path}")

if __name__ == "__main__":
    main()