#!/usr/bin/env python3
"""
Signal Pop — 脚本生成
把过滤后的新闻生成为播报文本

用法: python3 generate_script.py [制作日期YYYYMMDD] [daily|weekly]
  制作日期: cron 运行的当天（如 20260709）
  发布日期 = 制作日期 + 1 天（视频开头播报用发布日期）
"""
import os
import json
import sys
import re
from datetime import datetime, timedelta

DATA_DIR = "/home/kan/signal_pop/data"
OUTPUT_DIR = "/home/kan/signal_pop/output"
MINIMAX_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.xiaomimimo.com/v1")

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

def normalize_for_tts(text: str) -> str:
    text = re.sub(r'（-\s*(\d+(?:\.\d+)?)\s*元）', r'跌\1元', text)
    text = re.sub(r'\(-\s*(\d+(?:\.\d+)?)\s*元\)', r'跌\1元', text)
    return text

def call_llm(prompt: str) -> str:
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key:
        return ""
    try:
        import requests
        resp = requests.post(
            f"{MINIMAX_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "MiniMax-Text-01", "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 2000, "temperature": 0.3},
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[llm] ⚠️ Error: {e}")
    return ""

def generate_daily_script(news_items, prod_date=None):
    """
    生成每日播报脚本
    prod_date: 制作日期 YYYYMMDD，缺省 = 今天
    发布日期 = 制作日期 + 1 天（视频开头播报用发布日期）
    """
    if prod_date is None:
        prod_date = datetime.now().strftime("%Y%m%d")
    prod_dt = datetime.strptime(prod_date, "%Y%m%d")
    pub_dt = prod_dt + timedelta(days=1)

    prod_str = prod_dt.strftime("%Y年%m月%d日")
    prod_weekday = WEEKDAYS[prod_dt.weekday()]
    pub_str = pub_dt.strftime("%Y年%m月%d日")
    pub_weekday = WEEKDAYS[pub_dt.weekday()]

    candidates = news_items[:30]

    prompt = f"""
    你是一个极其严谨的新闻播报员。今天是 {prod_str} ({prod_weekday})。
    请从以下新闻列表中挑选出 10 条真正发生在 2026 年 7 月 7 日至 7 月 9 日之间的重要新闻。

    ⚠️ 绝对禁止包含任何 2026 年 7 月 7 日之前的旧闻（即使它在 RSS 列表中）。
    如果新闻内容明显是去年的或更早的，必须剔除。

    输出格式要求（严格遵守）：
    第1条，[类别]新闻。[标题]。
    据 [来源] 报道，[摘要（100字以内）]。

    (重复直到第10条)

    候选列表：
    {json.dumps(candidates, ensure_ascii=False)}
    """

    # 尝试用 LLM 精选；如果没有配置 key，则直接基于本地数据降级处理
    filtered_content = call_llm(prompt)
    if not filtered_content:
        # 降级：直接取前 10 条候选新闻，按固定格式输出
        lines = []
        for idx, item in enumerate(candidates[:10], 1):
            title = item.get("title", "")
            source = item.get("source", "")
            summary = item.get("summary", "")
            category = "综合"
            if any(k in title for k in ["科技", "技术", "AI", "芯片"]):
                category = "科技"
            elif any(k in title for k in ["财经", "市场", "经济"]):
                category = "财经"
            elif any(k in title for k in ["体育", "球", "奥运"]):
                category = "体育"
            elif any(k in title for k in ["天气", "气候", "灾害"]):
                category = "天气"
            elif any(k in title for k in ["医疗", "健康", "病毒"]):
                category = "健康"
            lines.append(f"第{idx}条，[{category}]新闻。{title}。据 {source} 报道，{summary[:100]}")
        filtered_content = "\n".join(lines)

    # 视频开头播报：用发布日期（制作日 +1）
    header = f"这里是隔天信号弹，今天是{pub_str}，{pub_weekday}。\n以下是今天的主要新闻。\n\n"
    footer = "\n\n以上是本期的信号弹，我们下期见。"

    return header + filtered_content + footer

def main():
    prod_date = sys.argv[1] if len(sys.argv) > 1 else None
    mode = sys.argv[2] if len(sys.argv) > 2 else "daily"

    raw_path = f"{DATA_DIR}/raw_feed.json"
    if not os.path.exists(raw_path):
        print("No raw feed found.")
        return

    with open(raw_path, "r", encoding="utf-8") as f:
        news_items = json.load(f)

    script = generate_daily_script(news_items, prod_date)

    subdir = "daily"
    mode_dir = f"{OUTPUT_DIR}/{subdir}"
    os.makedirs(mode_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d")
    txt_path = f"{mode_dir}/signal_pop_daily_{ts}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(script)

    print(f"[script] ✅ 脚本已保存：{txt_path}")
    print(f"\n{'='*40}\n{script}\n{'='*40}")

if __name__ == "__main__":
    main()
