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
    "breaking":    {"source": "real", "real_url": "", "prompt": "OpenAI GPT-6 发布会现场，真实新闻图"},  # GPT-6 正式发布
    "news01":      {"source": "real", "real_url": "", "prompt": "吉隆灾区救援现场，应急物资运送，真实新闻图"},  # 棉衣驰援吉隆灾区
    "news02":      {"source": "real", "real_url": "", "prompt": "英伟达 NVIDIA 公司标志与数据中心 GPU，真实新闻图"},  # 英伟达收购 Hugging Face
    "news03":      {"source": "metaphor", "prompt": "金融贷款隐喻，成捆美元钞票堆叠与上升的金色箭头，银行金库大门透出金光，电影感光影，无人类，无可读文字，新闻插画风格"},
    "news04":      {"source": "real", "real_url": "", "prompt": "基因编辑猪肾移植手术，医疗手术室场景，真实新闻图"},  # 猪肾摆脱透析
    "news05":      {"source": "real", "real_url": "", "prompt": "微信手机聊天界面特写，真实产品截图"},  # 微信单删回应
    "news06":      {"source": "ai", "prompt": "真空中自由下落的原子干涉仪实验，激光与悬浮原子云，深蓝色物理实验室，科学摄影风格，无人类，无可读文字"},
    "news07":      {"source": "real", "real_url": "", "prompt": "港交所上市敲钟现场，SHEIN 希音，真实新闻图"},  # SHEIN 赴港上市
    "news08":      {"source": "real", "real_url": "", "prompt": "厄尔尼诺海表温度卫星云图，太平洋异常增温，真实气象卫星图"},  # 厄尔尼诺形成
    "news09":      {"source": "real", "real_url": "", "prompt": "理想 MEGA 车型实拍，真实新闻图"},  # 理想 MEGA
    "news10":      {"source": "real", "real_url": "", "prompt": "半导体晶圆厂内部，硅晶圆与洁净室，真实新闻图"},  # 华虹扩建产线
    "news11":      {"source": "real", "real_url": "", "prompt": "全国大学生美术作品展览现场，真实新闻图"},  # 美术进京展
    "news12":      {"source": "metaphor", "prompt": "手机上方悬浮红色盾牌与警告符号，可疑转账气泡，暗色调科技警示插画，无人类无面孔，对话气泡内无任何文字，新闻插画风格"},
    "news13":      {"source": "real", "real_url": "", "prompt": "手机笔记本电脑平板数码产品组合陈列，开学季数码卖场，真实新闻图"},  # 数码三件套涨价
    "news14":      {"source": "ai", "prompt": "程序员深夜书桌，显示器流动彩色代码光影，AI 助手光点悬浮屏前，蓝色科技氛围，无人类面孔，屏幕上无可读文字"},
    "summary":     {"source": "ai", "prompt": "金色领奖台与星形奖杯，彩带飘落与聚光灯，庆典氛围，3D 渲染风格，无文字"},
    "watch":       {"source": "ai", "prompt": "多个发光日程卡片悬浮排列于聚光舞台前，日历与望远镜意象，蓝色科技风，3D 渲染，无可读文字"},
    "interactive": {"source": "ai", "prompt": "巨大对话气泡与点赞爱心评论图标漂浮，人群剪影仰望，暖金色调，无可读文字"},
    "pick":        {"source": "ai", "prompt": "a cute stylized stegosaurus dinosaur in a bright modern museum hall, soft 3D render style, playful and family friendly, warm lighting, no text"},
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
