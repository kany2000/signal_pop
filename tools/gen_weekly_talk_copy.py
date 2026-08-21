#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末特别版 · 8 平台发布文案（双人对话版，15 条）

输出到 output/weekly/{PREP_DATE}/
用法：python tools/gen_weekly_talk_copy.py [PREP_DATE]

本期 15 条新闻（第 15 名 → 第 1 名），标题同步自新闻稿：
  archive/signal_pop_weekly_special_20260821.txt / talk_segments.json
B站时间轴由音频 wav 实际时长推算（rank 播报段索引 = 6 + 2*(15-rank)）。
"""
import os
import sys
import wave
import re

PROJECT_ROOT = "E:/projects/signal_pop"
PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20260821"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
AUDIO_DIR = os.path.join(OUT_DIR, "audio")

from datetime import datetime, timedelta
PUB_DT = datetime.strptime(PREP_DATE, "%Y%m%d") + timedelta(days=1)
PUB_FMT = f"{PUB_DT.month}月{PUB_DT.day}日"

# 15 条新闻（第15名 → 第1名）
NEWS = [
    "村字号赛事激活县域经济",          # 15
    "雷鸟 iO AI 眼镜发布",             # 14
    "滴滴升级司机服务门店",            # 13
    "豆包上新技能·连接器",             # 12
    "智慧医疗打通资源壁垒",            # 11
    "国产预制算力 24 小时投运",        # 10
    "淘宝闪购跑腿升级",                # 9
    "僵尸卡漏洞：过期卡被复活",        # 8
    "商汤开源 SenseNova U1.5",         # 7
    "2 人买 3 座拒让座争议",           # 6
    "谦合益邦 4 层 3D DRAM 回片",      # 5
    "质量强链十大项目启动",            # 4
    "固态电池首项国际标准",            # 3
    "边缘行者 2 定档 10.20",           # 2
    "财政部五年加码科技投入",          # 1
]

TITLE = f"【周末特别版】阿信+小蓝聊本周｜{NEWS[14]}、{NEWS[13]}……15件大事"
DESC = "本周15件大事，阿信小蓝（信蓝组合）边聊边盘！一报一评，有梗有观点～"


def seg_duration(idx):
    wav = os.path.join(AUDIO_DIR, f"_s{idx:03d}.wav")
    try:
        with wave.open(wav, "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 3.0


def bili_timeline():
    """按 rank 播报段（seg_idx = 6 + 2*(15-rank)）推算 B站分段时间轴。"""
    lines = []
    for rank in range(15, 0, -1):
        seg_idx = 6 + 2 * (15 - rank)
        start = sum(seg_duration(i) for i in range(seg_idx))
        mm = int(start // 60)
        ss = int(start % 60)
        lines.append(f"{mm:02d}:{ss:02d} 第{rank}名 {NEWS[15 - rank]}")
    return "\n".join(lines)


def write(name, content):
    with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ {name} ({len(content)} chars)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 抖音
    dy = f"""标题：{TITLE}

简介：{DESC}

🎙️ 本周15件大事，信蓝组合开聊！
1️⃣ 村字号赛事激活县域经济
2️⃣ 雷鸟 iO AI 眼镜发布（首发2349）
3️⃣ 滴滴升级司机服务门店
4️⃣ 豆包上新技能·连接器
5️⃣ 智慧医疗打通资源壁垒
6️⃣ 国产预制算力24小时投运
7️⃣ 淘宝闪购跑腿升级
8️⃣ 僵尸卡漏洞：过期卡被"复活"
9️⃣ 商汤开源 SenseNova U1.5
🔟 2人买3座拒让座引争议
11. 谦合益邦4层3D DRAM回片
12. 质量强链十大项目启动
13. 固态电池首项国际标准
14. 边缘行者2定档10.20
15. 财政部五年加码科技投入（研发3.9万亿）

#隔天信号弹 #周末特别版 #信蓝组合 #新闻脱口秀 #科技 #民生 #财经 #文化 #AI #固态电池
"""
    write("douyin.md", dy)

    # 快手
    ks = f"""标题：【周末特别版】信蓝组合聊本周15件大事

简介：阿信+小蓝，一报一评，陪你看遍本周！

🔥 本周15条（倒序）：
① 财政部五年加码科技投入
② 边缘行者2定档10.20
③ 固态电池首项国际标准
④ 质量强链十大项目启动
⑤ 谦合益邦4层3D DRAM回片
⑥ 2人买3座拒让座争议
⑦ 商汤开源 SenseNova U1.5
⑧ 僵尸卡漏洞：过期卡被复活
⑨ 淘宝闪购跑腿升级
⑩ 国产预制算力24小时投运
11. 智慧医疗打通资源壁垒
12. 豆包上新技能·连接器
13. 滴滴升级司机服务门店
14. 雷鸟 iO AI 眼镜发布
15. 村字号赛事激活县域经济

#隔天信号弹 #周末特别版 #信蓝组合 #新闻盘点 #科技 #民生
"""
    write("kuaishou.md", ks)

    # B站（时间轴）
    timeline_text = bili_timeline()
    bili = f"""{TITLE}

📌 分段时间轴：
{timeline_text}

💬 阿信报新闻，小蓝唠重点——信蓝组合，有梗有观点！

#隔天信号弹 #周末特别版 #信蓝组合 #新闻脱口秀 #科技 #文化 #财经
"""
    write("bilibili.md", bili)

    # 小红书
    xhs = f"""宝子们！周末特别版来啦📺✨

阿信+小蓝（信蓝组合）合体营业！
15件本周大事，边聊边盘，有梗有观点👇

📜 本期精选：
1️⃣ 财政部五年加码科技投入（研发经费超3.9万亿）
2️⃣ 边缘行者2定档10.20（纸巾备好）
3️⃣ 固态电池首项国际标准由中国牵头
4️⃣ 质量强链十大项目启动（166项攻关）
5️⃣ 谦合益邦4层3D DRAM回片
6️⃣ 2人买3座拒让座引争议
7️⃣ 商汤开源 SenseNova U1.5
8️⃣ 僵尸卡漏洞：过期卡都能"诈尸"付款
9️⃣ 淘宝闪购跑腿升级
🔟 国产预制算力24小时投运
11. 智慧医疗打通资源壁垒
12. 豆包上新技能·连接器
13. 滴滴升级司机服务门店
14. 雷鸟 iO AI 眼镜发布
15. 村字号赛事激活县域经济

你最喜欢哪条？评论区聊聊呀💬
记得关注不迷路，每周六8点见～

#隔天信号弹 #周末特别版 #信蓝组合 #新闻盘点 #固态电池 #边缘行者 #科技新闻 #民生新闻 #文化 #财经 #AI
"""
    write("xiaohongshu.md", xhs)

    # 知乎
    zh = f"""隔天信号弹 | 周末特别版：阿信+小蓝聊本周（{PUB_FMT}）

本周 15 件大事，信蓝组合一报一评：

1. 财政部宣布未来五年持续加大科技投入，2025 年全国研发经费已超 3.9 万亿
2. 《赛博朋克》衍生动画《边缘行者 2》定档 10 月 20 日
3. 我国牵头立项固态电池首项国际标准
4. 2026 年质量强链十大标志性项目启动，部署 166 项攻关任务
5. 网易孵化芯片公司谦合益邦自研 4 层 3D DRAM 堆叠存算一体芯片回片
6. 2 人买 3 座拒绝让座，律师：合法购票即享有排他使用权
7. 商汤开源 8B 参数多模态大模型 SenseNova U1.5，原生支持 4K
8. 安全研究曝出"僵尸卡"漏洞，过期银行卡可被"复活"付款
9. 淘宝闪购跑腿（原蜂鸟跑腿）品牌升级
10. 国产"预制算力"工厂预制率超 90%，24 小时投运
11. 智慧医疗打通资源壁垒，高水平诊疗送到百姓身边
12. 豆包工作任务上新"技能·连接器·工作伙伴"
13. 滴滴升级线下司机服务门店体系
14. 雷鸟发布 iO AI 眼镜，首发价 2349 元
15. 村字号赛事持续上新，激活县域经济

关注「隔天信号弹」，每周六 8 点，信蓝组合陪你看遍本周大事。
"""
    write("zhihu.md", zh)

    # 英文平台
    en_title = f"Weekend Special | Xin & Lan Talk This Week | {NEWS[14]}, {NEWS[13]}... 15 Big Stories"
    fb = f"""Weekend Special: Xin & Lan Talk This Week 🎙️

Two anchors (Xin + Lan = "XinLan Combo") chat about the TOP 15 stories of the week — one reports, one reacts!

🔹 Ministry of Finance to boost sci-tech spending over next 5 years (R&D > 3.9 trillion yuan)
🔹 Cyberpunk spin-off "Edgewalkers 2" set for Oct 20
🔹 China leads 1st international standard for solid-state batteries
🔹 Top 10 quality-chain projects launched (166 tasks)
🔹 NetEase's Qianhe Yibang tapes out 4-layer 3D DRAM chip
🔹 "Zombie card" flaw revives expired bank cards
🔹 SenseNova U1.5 open-source multimodal model (4K)
🔹 Taobao flash errand service upgrade
🔹 Prefab computing power, live in 24 hours
🔹 Smart healthcare breaks resource barriers

#SignalPop #WeekendSpecial #XinLanCombo #NewsTalk #China #Tech
"""
    write("facebook.md", fb)

    yt = f"""Weekend Special | Xin & Lan Talk This Week | TOP 15 Stories of the Week

Two anchors (Xin + Lan) chat about this week's 15 biggest stories — one reports the news, the other drops hot takes. A news talk show, weekend edition!

Highlights: Ministry of Finance boosts sci-tech spending (R&D > 3.9 trillion yuan), "Edgewalkers 2" set for Oct 20, China leads solid-state battery standard, and more.

Subscribe for the weekly Saturday 08:00 edition!

#SignalPop, #WeekendSpecial, #NewsTalk, #China, #Tech, #Culture, #XinLanCombo, #Top15
"""
    write("youtube.md", yt)

    tw = f"""🎙️ Xin & Lan Talk This Week — Weekend Special!

TOP 15 stories, one reports, one reacts:
🔹 Sci-tech spending boost (R&D > 3.9T)
🔹 Edgewalkers 2 set for Oct 20
🔹 Solid-state battery standard (China)
🔹 Quality-chain top 10 projects
🔹 SenseNova U1.5 open-source

Watch the full talk ▶️
#SignalPop #WeekendSpecial #NewsTalk #China
"""
    write("twitter.md", tw)

    print(f"\n全部 8 平台文案已生成到 {OUT_DIR}/")


if __name__ == "__main__":
    main()
