#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop — 周末特别版管线驱动（输出到 output/weekly/，不走 daily）
用法：python tools/weekend_pipeline.py [PREP_DATE] [步骤]
步骤: parse | images | tts | all

2026-08-28 重构：支持新版格式
  【突发消息】 + 【本周要闻】(无排名) + 【本周之最】 + 【下周看点】 + 【互动话题】
配图改为混合来源（IMAGE_PLAN）：突发/科技/时事灾难/民生新闻=真实网络图；
娱乐八卦=擦边球隐喻(Sensenova 无真人)；抽象题材=AI(Sensenova)。
"""
import os
import sys
import json
from datetime import datetime, timedelta

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260828"
STEP = sys.argv[2] if len(sys.argv) > 2 else "parse"

SCRIPT_FILE = os.path.join(PROJECT_ROOT, "archive", f"signal_pop_weekly_special_{PREP_DATE}.txt")
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
IMAGES_DIR = os.path.join(OUT_DIR, "images")
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
PARSED_PATH = os.path.join(OUT_DIR, "parsed_news.json")
AUDIO_PATH = os.path.join(AUDIO_DIR, "tts.wav")
OUTPUT_VIDEO = os.path.join(OUT_DIR, f"signal_pop_weekly_{PREP_DATE}.mp4")

PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_DATE_FMT = f"{PUB_DT.year}年{PUB_DT.month:02d}月{PUB_DT.day:02d}日"
PUB_DATE_SHORT = f"{PUB_DT.year}.{PUB_DT.month:02d}.{PUB_DT.day:02d}"
PUB_WEEKDAY = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][PUB_DT.weekday()]

# ============ 周末版配图计划（混合来源） ============
# source:
#   "real"     -> 网络真实高清图（突发/科技产品/时事灾难/民生新闻，禁止 AI 任意生成）
#   "metaphor" -> 擦边球隐喻图（娱乐八卦：Sensenova 生成，明确无真人、无 celebrity 名）
#   "ai"       -> 抽象题材 AI 生成（Sensenova）
# real 项提供 real_url 直接下载；metaphor/ai 提供 prompt 走 Sensenova
IMAGE_PLAN = {
    "breaking":    {"source": "real", "real_url": "https://upload.wikimedia.org/wikipedia/commons/4/4d/2023%E5%B9%B4%E6%B6%BF%E5%B7%9E%E6%B1%9B%E6%83%85_Zhuozhou_flood_01_20230802.jpg"},
    "news01":      {"source": "ai", "prompt": "英伟达 NVIDIA 与 SpaceX 合作概念图，绿色 AI 芯片与银色可重复使用火箭并排飞向太空，地球在背景，未来科技感，无人类，无肖像，无文字，无品牌可读文字，无字母"},
    "news02":      {"source": "ai", "prompt": "office corridor with stacked resignation documents and empty desks, corporate layoff concept, cold blue tone, documentary photography, no text, no people faces"},
    "news03":      {"source": "metaphor", "prompt": "a glowing red 'hot search' trending topic bar on fire on a dark desk, a formal legal letter with a seal stamp and a wooden gavel beside it, dramatic red and gold lighting, NO people, NO faces, NO avatars, NO portraits, NO human silhouette, NO celebrity likeness, no readable text, metaphor for viral online gossip and legal response, news illustration style"},
    "news04":      {"source": "ai", "prompt": "台风突袭东南沿海，狂风暴雨席卷海岸城市，巨浪拍岸，气象灾难新闻摄影，写实纪实风格，无文字"},
    "news05":      {"source": "ai", "prompt": "advanced AI inference chip on glowing blue circuit board, golden and blue tech lighting, macro semiconductor photography, no text no readable letters no words"},
    "news06":      {"source": "ai", "prompt": "customer service robot with a forbidden symbol, consumer rights concept, clean tech illustration, no text, no people"},
    "news07":      {"source": "real", "real_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/MacBook_Pro_13_%28M1%2C_2020%29.jpg/1920px-MacBook_Pro_13_%28M1%2C_2020%29.jpg", "prompt": "Apple M6 chip macro photography, 2nm processor, premium tech product shot"},
    "news08":      {"source": "ai", "prompt": "中国的人形机器人，国产双足人形机器人在现代展厅中央，宇树或优必选风格，背景简洁无人脸，产品摄影，无文字"},
    "news09":      {"source": "real", "real_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Hot_surfaces_during_Europe%27s_heatwave_%27seen%27_by_Sentinel-3_ESA522397.jpg/1920px-Hot_surfaces_during_Europe%27s_heatwave_%27seen%27_by_Sentinel-3_ESA522397.jpg", "prompt": "Europe extreme heatwave, dry cracked land and wildfire smoke, climate disaster news photography"},
    "news10":      {"source": "real", "real_url": "https://upload.wikimedia.org/wikipedia/commons/6/64/Shanghai_skyline_from_the_bund.jpg", "prompt": "Shanghai real estate, modern apartment buildings exterior, housing market, documentary photography"},
    "news11":      {"source": "ai", "prompt": "happy family with baby, child allowance policy concept, warm bright tone, no text, no people faces closeup"},
    "news12":      {"source": "ai", "prompt": "medicine box and health insurance card, new livelihood regulations concept, clean photography, no text"},
    "news13":      {"source": "ai", "prompt": "股权套现金融隐喻，股票走势曲线与现金堆叠，金色财富意象，电影感光影，无文字无可读文字"},
    "news14":      {"source": "real", "real_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/A_Foggy_Tale%2C_winner_of_best_narrative_film%2C_2025_Golden_Horse_Awards_01.jpg/1920px-A_Foggy_Tale%2C_winner_of_best_narrative_film%2C_2025_Golden_Horse_Awards_01.jpg", "prompt": "golden eagle award trophy on stage, Chinese TV awards ceremony, photography"},
    "summary":     {"source": "ai", "prompt": "golden trophy cup with award ribbons on pedestal, celebration confetti, awards ceremony, no text"},
    "watch":       {"source": "ai", "prompt": "futuristic humanoid robots lined up in exhibition hall, robotics expo, sci-fi, no text"},
    "interactive": {"source": "ai", "prompt": "speech bubble with question mark and comment icons floating, audience interaction concept, warm gold tone, no readable text"},
}


def parse_weekly_top(text):
    """解析新版周末版格式：
    【突发消息】/[分类]新闻。标题。上榜理由：xxx
    【本周要闻】/[分类]新闻。标题。上榜理由：xxx  (多条，无排名)
    【本周之最】自由文本
    【下周看点】自由文本
    【互动话题】自由文本
    返回扁平 items（顺序=脚本顺序），含 type/section/title/body/img/img_id/source
    """
    import re as _re
    items = []
    cur_block = None
    news_idx = 0
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("这里是") or line.startswith("以上是"):
            continue
        if line.startswith("【"):
            tag = line.strip("【】")
            if tag == "突发消息":
                cur_block = "breaking"
            elif tag == "本周要闻":
                cur_block = "news"
            elif tag == "本周之最":
                cur_block = "summary"
            elif tag == "下周看点":
                cur_block = "watch"
            elif tag == "互动话题":
                cur_block = "interactive"
            else:
                cur_block = tag
            continue
        m = _re.match(r"^\[(.+?)\]\s*新闻[。.]\s*(.+?)[。.]\s*上榜理由[：:]\s*(.+)$", line)
        if m:
            section = m.group(1).strip()
            title = m.group(2).strip()
            body = m.group(3).strip()
            if cur_block == "breaking":
                items.append({"type": "breaking", "section": section, "title": title, "body": body,
                              "img": "breaking.jpg", "img_id": "breaking"})
            else:
                news_idx += 1
                items.append({"type": "news", "section": section, "title": title, "body": body,
                              "img": f"news_{news_idx:02d}.jpg", "img_id": f"news{news_idx:02d}"})
            continue
        if cur_block in ("summary", "watch", "interactive"):
            label = {"summary": "本周之最", "watch": "下周看点", "interactive": "互动话题"}[cur_block]
            exist = next((it for it in items if it["type"] == cur_block), None)
            if exist:
                exist["body"] = (exist["body"] + " " + line).strip()
            else:
                items.append({"type": cur_block, "section": label, "title": label, "body": line,
                              "img": f"{cur_block}.jpg", "img_id": cur_block})
    for it in items:
        plan = IMAGE_PLAN.get(it["img_id"], {"source": "ai", "prompt": ""})
        it["source"] = plan["source"]
        it["prompt"] = plan.get("prompt", "")
        it["real_url"] = plan.get("real_url", "")
    return items


def step_parse():
    text = open(SCRIPT_FILE, encoding="utf-8").read()
    items = parse_weekly_top(text)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(PARSED_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"[parse] {len(items)} 段 -> {PARSED_PATH}")
    for it in items:
        print(f"  [{it['type']:<9}] {it['section']:<4} {it['title'][:20]} src={it['source']:<8} img={it['img']}")
    return items


def step_images():
    from weekly_images import fetch_weekly_images
    items = json.load(open(PARSED_PATH, encoding="utf-8"))
    os.makedirs(IMAGES_DIR, exist_ok=True)
    fetch_weekly_images(items, IMAGES_DIR)
    print(f"[images] -> {IMAGES_DIR}")


def step_tts():
    """周末版双主播 TTS：先由 build_weekly_dialogue 生成 阿信/小蓝 对话稿，再 gen_dual_tts 合成。"""
    import build_weekly_dialogue
    dlg = os.path.join(OUT_DIR, "dialogue_script.txt")
    build_weekly_dialogue.build(PARSED_PATH, dlg)
    import gen_dual_tts
    gen_dual_tts.main_with(dlg)


if __name__ == "__main__":
    if STEP in ("parse", "all"):
        step_parse()
    if STEP in ("images", "all"):
        step_images()
    if STEP in ("tts", "all"):
        step_tts()
    print("DONE")
