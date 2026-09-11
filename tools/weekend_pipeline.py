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
    "breaking":    {"source": "real", "real_url": "", "prompt": "苹果 iPhone Duo 折叠屏手机实机展示：钛金属机身、展开7.6英寸内屏（屏下摄像头无挖孔）、折叠5.4英寸外屏，产品摄影，真实新闻图"},  # iPhone Duo 折叠屏（特别报道）
    "news01":      {"source": "real", "real_url": "", "prompt": "smart city traffic command center with a large video wall showing highway traffic-flow heatmap and slow-vehicle alert zones, aerial view of roads with moving cars, blue tech tone, realistic news photo, no people faces"},  # 成都AI智慧系统治理龟速车（智慧交通系统，车在路上/指挥中心大屏，不进大厅）
    "news02":      {"source": "ai", "real_url": "", "prompt": "abstract glowing AI neural network spiraling into a warning symbol, superintelligence and existential risk metaphor, dark dramatic sci-fi illustration, NO people, NO faces, NO portraits, no readable text"},  # Anthropic研究员因AI生存风险辞职
    "news03":      {"source": "ai", "real_url": "", "prompt": "abstract glowing AI model architecture with flowing data streams and compressed cache metaphor, dark tech illustration, no text, no faces"},  # DeepSeek V4.1 Flash
    "news04":      {"source": "ai", "real_url": "", "prompt": "a glowing concert ticket stub transforming into shopping bags, a dining table and travel landmark icons, golden autumn consumption festival concept, festive glow, abstract, no faces"},  # 票根经济激活金秋消费（理念保留，去文字）
    "news05":      {"source": "ai", "real_url": "", "prompt": "scales of justice combined with AI neural network, legal tech metaphor, dark blue, no faces, no readable text"},  # 最高法涉AI纠纷意见
    "news06":      {"source": "real", "real_url": "", "prompt": "a laser beam linking Earth and the Moon across deep space, glowing communication link, sci-fi realistic visualization, no readable text"},  # 地月双向高速激光通信
    "news07":      {"source": "real", "real_url": "", "prompt": "Liu Xiang at 2004 Athens Olympics podium holding gold medal, real sports news photo, no readable text"},  # 刘翔与上海体育局人事买断
    "news08":      {"source": "real", "real_url": "", "prompt": "Geely Galaxy TT pure electric coupe on display, car product photography, real news image"},  # 吉利银河TT纯电轿跑上市
    "news09":      {"source": "real", "real_url": "", "prompt": "skyline of Shanghai Lujiazui financial district with glowing data charts overlay, blue tone, real news image"},  # 金融强国十五五规划
    "news10":      {"source": "real", "real_url": "", "prompt": "Chinese traditional classics still-life arrangement: a bolt of silk fabric, tea leaves with a teacup, blue-and-white porcelain vases, dried Chinese herbal medicine, and a scenic ancient-town travel view, warm museum lighting, realistic product photography"},  # 六部门历史经典产业政策（丝绸/茶叶/瓷器/中药/旅游）
    "news11":      {"source": "real", "real_url": "", "prompt": "医保服务大厅市民办理参保缴费，工作人员协助操作终端，写实新闻摄影，无人物正脸，无文字"},  # 灵活就业人员职工医保缴费年限按月累计
    "news12":      {"source": "real", "real_url": "", "prompt": "Yunnan landscape with ancient town and terraced fields, travel photography, real image"},  # 云南错峰游淡季不淡
    "news13":      {"source": "real", "real_url": "", "prompt": "a sleek AI smart glasses product shot, futuristic wearable tech, studio lighting, real product image, no readable text"},  # 千问新款AI眼镜虹膜支付
    "news14":      {"source": "real", "real_url": "", "prompt": "busy container terminal with stacked containers and cargo ships, aerial view, real trade port news image"},  # 前8个月货物贸易进出口增长6%
    "news15":      {"source": "real", "real_url": "", "prompt": "global payment network nodes glowing across a world map, cross-border RMB settlement concept, blue tech visualization, no readable text"},  # CIPS跨境支付系统扩容
    "news16":      {"source": "real", "real_url": "", "prompt": "苹果秋季发布会全系新品阵容：iPhone 18 Pro、Apple Watch、AirPods 同台展示，真实产品图"},  # 苹果发布会全系（合并单条）
    "summary":     {"source": "ai", "prompt": "金色领奖台与星形奖杯，彩带飘落与聚光灯，庆典氛围，3D 渲染风格，无文字"},
    "interactive": {"source": "ai", "prompt": "巨大对话气泡与点赞爱心评论图标漂浮，人群剪影仰望，暖金色调，无可读文字"},
    "pick":        {"source": "ai", "prompt": "a cozy online art gallery with famous oil paintings on warm-lit walls, framed canvases and easels, soft 3D render style, museum atmosphere, warm lighting, no text"},
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
            if tag in ("突发消息", "特别报道"):
                cur_block = "breaking"
            elif tag == "本周要闻":
                cur_block = "news"
            elif tag == "本周之最":
                cur_block = "summary"
            elif tag == "下周看点":
                cur_block = "watch"
            elif tag == "互动话题":
                cur_block = "interactive"
            elif tag == "每期精选":
                cur_block = "pick"
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
        if cur_block in ("summary", "watch", "interactive", "pick"):
            label = {"summary": "本周之最", "watch": "下周看点", "interactive": "互动话题", "pick": "每期精选"}[cur_block]
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
