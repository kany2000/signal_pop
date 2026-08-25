#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""信号弹·每日版 20260825 配图生成器（Sensenova 原图带水印输出，不做任何去水印处理）

- 读取 curated 新闻条目 → 调用 win_pipeline_images.gen_all_images
- 输出到 output/daily/20260825/images/ ：00.jpg(历史) + 01~15.jpg(新闻) + opening_bg.jpg + ending_bg.jpg
- 严格遵循铁律：保留 Sensenova 原始带水印图，不模糊/不 inpaint，交用户自清
"""
import os
import sys
import json

ROOT = "E:/projects/signal_pop"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)

from win_pipeline_images import gen_all_images  # noqa: E402

PREP = "20260825"
OUT_DIR = os.path.join(ROOT, "output", "daily", PREP, "images")

NO_TXT = ", no text, no words, no letters, no numbers, no captions, no UI, clean image without any writing"

ITEMS = [
    {
        "num": 0,
        "title": "历史上的今天：1973年8月26日 中国第一台百万次集成电路计算机试制成功",
        "visual_prompt": (
            "1970s Chinese computer laboratory, large mainframe computer with rows of blinking indicator "
            "lights and magnetic tape units, Chinese engineers in 1970s clothing working at the console, "
            "retro beige computer room, documentary photography, warm fluorescent lighting, historical atmosphere"
            + NO_TXT
        ),
    },
    {
        "num": 1,
        "title": "OpenAI Codex用户突破2000万，Claude Code居Agent榜首",
        "visual_prompt": (
            "modern software developer workspace at night, dual monitors showing code editors with syntax "
            "highlighting and terminal windows, glowing blue and purple ambient light, abstract flow of code "
            "tokens and neural network nodes above the screens, AI programming assistant concept, cinematic "
            "tech photography" + NO_TXT
        ),
    },
    {
        "num": 2,
        "title": "阿里800亿港元配售新股，所得100%投向全栈AI",
        "visual_prompt": (
            "futuristic data center campus representing AI infrastructure investment, rows of glowing server "
            "racks with blue light, abstract golden capital flowing as light streams into the servers, harbor "
            "skyline at dusk in background, financial technology and artificial intelligence convergence, cinematic"
            + NO_TXT
        ),
    },
    {
        "num": 3,
        "title": "夜间旅游出圈，文旅消费从门票经济迈向综合消费",
        "visual_prompt": (
            "vibrant Chinese night tourism scene, ancient town with traditional architecture illuminated by warm "
            "lanterns and colorful light installations, drone light show in the night sky, crowds of silhouetted "
            "visitors, festive bokeh lights, cinematic travel photography" + NO_TXT
        ),
    },
    {
        "num": 4,
        "title": "加拿大暂停与美贸易谈判，将对等征收50%关税",
        "visual_prompt": (
            "abstract geopolitical trade tension concept, symbolic border crossing with cargo containers and "
            "freight trucks, dramatic overcast sky, a wooden crate with a glowing tariff emblem, cool blue and "
            "grey tones, cinematic" + NO_TXT
        ),
    },
    {
        "num": 5,
        "title": "中国机器人连刷人类世界纪录，2026世界机器人大会多项赛事表现抢眼",
        "visual_prompt": (
            "humanoid robots competing on a sports stadium track, robot athletes sprinting on a running track "
            "with spotlights, futuristic robotics competition arena, thousands of spectators silhouettes, "
            "dynamic motion, cinematic wide shot, no people" + NO_TXT
        ),
    },
    {
        "num": 6,
        "title": "低空经济迈入新兴支柱产业，广州竞逐天空之城",
        "visual_prompt": (
            "futuristic low-altitude economy over a modern Chinese megacity, multiple eVTOL flying vehicles and "
            "delivery drones cruising above skyscrapers at golden hour, aerial city perspective, clean energy "
            "aviation, cinematic" + NO_TXT
        ),
    },
    {
        "num": 7,
        "title": "官方确认湖南扶老人遭索赔店主无过错，法律不能和稀泥",
        "visual_prompt": (
            "warm-hearted neighborhood convenience store scene, a kind female shopkeeper helping an elderly "
            "person who feels unwell, small neighborhood shop interior with shelves, compassionate community "
            "atmosphere, soft natural lighting, documentary photography" + NO_TXT
        ),
    },
    {
        "num": 8,
        "title": "四川宜宾发生4.7级地震，震感明显暂无重大灾情",
        "visual_prompt": (
            "seismic monitoring and emergency response scene, a calm riverside town at dawn with subtle "
            "structural cracks on a building wall, a geology survey vehicle and earthquake early-warning "
            "equipment, rescue team silhouettes, muted earthy tones, documentary photography" + NO_TXT
        ),
    },
    {
        "num": 9,
        "title": "中国羽毛球世锦赛男双时隔8年再夺金",
        "visual_prompt": (
            "badminton men's doubles championship moment, two Chinese athletes celebrating with a gold medal "
            "on a badminton court, shuttlecock frozen mid-air, indoor arena with dramatic floodlights, victory "
            "atmosphere, sports photography" + NO_TXT
        ),
    },
    {
        "num": 10,
        "title": "美国对多晶硅衍生品加征15%关税、设最低进口价",
        "visual_prompt": (
            "modern solar polysilicon manufacturing, rows of glowing silicon ingots and solar wafers in a "
            "cleanroom, stacks of solar panels, abstract trade barrier concept with a shield of light, cool "
            "industrial tones, cinematic" + NO_TXT
        ),
    },
    {
        "num": 11,
        "title": "英伟达Groq 3 LPX全面投产，Vera Rubin算力跃升",
        "visual_prompt": (
            "massive AI data center with rows of GPU server racks glowing green and blue, futuristic compute "
            "infrastructure, streams of light representing token generation, dramatic tech photography, no people"
            + NO_TXT
        ),
    },
    {
        "num": 12,
        "title": "奔县游乡村游成下沉市场消费新热点",
        "visual_prompt": (
            "idyllic Chinese rural tourism, a picturesque small county town with traditional houses surrounded "
            "by green rice fields and mountains, a cozy homestay with a wooden balcony, slow-travel atmosphere, "
            "warm daylight, documentary photography" + NO_TXT
        ),
    },
    {
        "num": 13,
        "title": "今年我国早稻总产量2817.4万吨，夏粮基础进一步夯实",
        "visual_prompt": (
            "golden rice paddy harvest in full swing, vast fields of ripe rice under blue sky, agricultural "
            "abundance, a combine harvester working in the field, rural China scenery, warm sunlight, "
            "documentary photography" + NO_TXT
        ),
    },
    {
        "num": 14,
        "title": "善用Windows 11的云剪贴板与虚拟桌面，多任务更高效",
        "visual_prompt": (
            "modern Windows 11 desktop computer screen showing multiple virtual desktops and a clipboard "
            "history panel, clean operating system interface with task view, glowing blue accent on monitor, "
            "software UI concept, sharp focus, dark elegant workspace, no hands, no people" + NO_TXT
        ),
    },
    {
        "num": 15,
        "title": "AI使用指南：用记忆层让Claude Code与Codex无缝协作",
        "visual_prompt": (
            "abstract concept of shared AI memory across multiple AI agents, glowing interconnected memory "
            "nodes passing a stream of context between two stylized robot avatars, neural network lattice in "
            "dark space, futuristic collaboration visualization, cinematic" + NO_TXT
        ),
    },
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    gen_all_images(ITEMS, OUT_DIR)
    print("===== 20260825 配图生成完成（原始带水印图，待用户自清） =====")


if __name__ == "__main__":
    main()
