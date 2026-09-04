#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末版 · 新闻条目 -> 双主播对话稿生成器

读取 parsed_news.json（周末版新格式），生成：
  1) dialogue_script.txt   —— 阿信：/小蓝： 对话行，供 gen_dual_tts 消费
  2) dialogue_segments.json —— 逐句 [{speaker, text, bg}]，供 export_weekly_remotion 取背景图

双主播人设：
  阿信（男/理性）：政策、数据、事实定调一句
  小蓝（女/情绪）：共情、吐槽、轻松一句
护栏：灾难/民生类用克制共情，不玩梗不抖机灵；娱乐类可轻松犀利。
（观点为模板生成，用户可在 dialogue_script.txt 中逐句替换为更贴合的表达）
"""

import json
import os
import sys
import re

PROJECT_ROOT = "E:/projects/signal_pop"

# 阿信/小蓝 双视角观点（按板块给基调，灾难民生克制）
AXIN = {
    "科技": "这条我觉得含金量很高，说明赛道又往前迈了一步，值得长期盯。",
    "民生": "说到底都是民生账，政策能不能落地、执行到不到位才是关键。",
    "时事": "数字摆在这，影响面不小，后续处置和复盘很关键。",
    "娱乐": "热度是真高，不过咱们吃瓜归吃瓜，别被节奏带跑了。",
}
XIAOLAN = {
    "科技": "科技党狂喜！就希望别又只是 PPT，早点能真用上才香。",
    "民生": "听着心里一紧，普通人真的不容易，希望好消息能兑现。",
    "时事": "天呐太揪心了，盼灾区的人都平平安安的。",
    "娱乐": "哈哈这瓜我嗑了，不过真假咱们让子弹再飞一会儿。",
}
# 突发消息双主播定调（克制共情，不玩梗）；小蓝回评按期定制（键 breaking.jpg，未命中回退默认句）
BRK_AXIN = "先给大家插播一条突发消息。"
BRK_XIAOLAN = "看到这消息我心里一沉，愿前方的人都能平安。"
BRK_COMMENTS = {
    "breaking.jpg": {
        "xiaolan": "发布当天自家服务先集体宕机，这个‘AGI时代’的开局也太黑色幽默了。",
    },
}

# 本期（20260904）逐条定制双视角评论：按 img 精确匹配，覆盖板块模板，去重且针对内容
# （板块模板 XIAOLAN/AXIN 作为未命中时的回退；下期可沿用此结构补充新条目）
COMMENTS = {
    "news_01.jpg": {
        "xiaolan": "两天两批4810件棉衣运到灾区，高原夜里冷，这些衣服是真救命的东西。",
        "axin": "调配8000件、4810件已到，救援效率看得见，后续安置和灾后重建还得持续盯。",
    },
    "news_02.jpg": {
        "xiaolan": "129亿美元买下一个开源社区，黄仁勋这手笔吓人，还好他承诺不把AI关进围墙。",
        "axin": "开源生态是AI世界的公共地基，收购之后保持开放还是走向封闭，全球开发者都盯着。",
    },
    "news_03.jpg": {
        "xiaolan": "296亿美元贷款，字节这是要憋大招啊，就不知道这钱最后砸向哪个赛道。",
        "axin": "亚洲第二大美元贷款，说明机构对字节的现金流有信心，AI和全球化大概率是去向。",
    },
    "news_04.jpg": {
        "xiaolan": "猪肾扛了9个月还等到人体供肾，医学这一步走得太不容易了，为研究团队点赞。",
        "axin": "异种移植从实验走向临床案例，器官等待名单上的希望又多了一分，意义在里程碑级。",
    },
    "news_05.jpg": {
        "xiaolan": "好友超一万才能看单删，这是大佬的烦恼，咱们普通人只求别被静悄悄删掉。",
        "axin": "功能向少数重度用户倾斜可以理解，但‘防错过’这种全量优化才是真普惠。",
    },
    "news_06.jpg": {
        "xiaolan": "量子物体下落也被引力管着，听着平平无奇，实际是人类第一次亲眼‘看到’它。",
        "axin": "在微观尺度验证爱因斯坦的等效原理，量子引力实验往前挪了一小步，基础物理一大步。",
    },
    "news_07.jpg": {
        "xiaolan": "从广州出发六年三城，希音终于敲钟了，广东老乡出海的天花板又高了。",
        "axin": "小单快反的供应链飞轮是它的护城河，上市之后能不能持续，看跨境规则的脸色。",
    },
    "news_08.jpg": {
        "xiaolan": "厄尔尼诺又来了，还可能变超强，看来秋天的衣服得多备几件厚实的。",
        "axin": "超强厄尔尼诺意味着极端天气概率抬升，农业和防灾预案要提前走一步。",
    },
    "news_09.jpg": {
        "xiaolan": "50万的MPV配4个激光雷达，李想这是把‘冰箱彩电大沙发’卷成‘驾驶舱’了。",
        "axin": "叫‘iPhone时刻’是营销话术，但高端MPV智能化提速是实打实的趋势。",
    },
    "news_10.jpg": {
        "xiaolan": "华虹一个月多5.5万片，国产芯片这扩产速度，看得人踏实。",
        "axin": "成熟制程扩产直接利好车规和工业芯片，产能瓶颈缓解，供应链韧性上了一个台阶。",
    },
    "news_11.jpg": {
        "xiaolan": "大学生美术展都办到进京展了，400多件作品里还有数字艺术，想去打卡！",
        "axin": "新生代把画笔伸进了数字世界，这批作品就是未来十年审美的预览，值得一看。",
    },
    "news_12.jpg": {
        "xiaolan": "骗子都混进家长群当‘班主任’了，开学季大家看到收款码先核实再转账！",
        "axin": "冒充老师诱导转账是老套路新变种，群主开个实名验证，能挡住大半风险。",
    },
    "news_13.jpg": {
        "xiaolan": "晚买一个月贵一千，AI把存储芯片买断货了，这波涨价属实没想到。",
        "axin": "算力挤占存储产能是结构性缺口，短期难解，刚需的话趁早下手更划算。",
    },
    "news_14.jpg": {
        "xiaolan": "每晚9点后编程额度全免，白嫖写代码的窗口期，程序员们冲啊！",
        "axin": "夜间错峰免单是漂亮的获客策略，对学生党和独立开发者是真金白银的福利。",
    },
}


def extract_stats(body, max_n=3):
    """从「本周之最」正文自动抽取数字统计卡数据（count-up 动效用）。

    用户在 parsed_news.json 的 summary 条目显式给 "data": [{num, suffix, label}]
    时优先用用户的；否则走本函数兜底：抽 数字+单位，标签取数字前 ≤12 字上下文。
    过滤：纯单数字（无单位）当噪声跳过；1900-2100 的裸年份跳过。
    """
    unit_pat = (
        "万人|亿人|万元|亿元|亿美元|万美元|亿美元|万|亿|%|℃|美元|元|倍|人|部|种|款|"
        "GB|TB|G|km|kg|nm|英寸|寸|帧|辆|架|艘|届|场|倍"
    )
    stats = []
    for m in re.finditer(rf"(\d[\d,]*(?:\.\d+)?)\s*({unit_pat})?", body):
        digits = m.group(1).replace(",", "")
        unit = m.group(2) or ""
        try:
            num = float(digits)
        except ValueError:
            continue
        if not unit and (num < 10 or 1900 <= num <= 2100):
            continue  # 单数字噪声 / 裸年份
        label = body[max(0, m.start() - 12) : m.start()]
        label = re.sub(r"^[，。、；：—\-\s（）()\"\"'‘’“”]+", "", label).strip()
        if len(label) < 2:
            label = "本周之最"
        stats.append(
            {
                "num": int(num) if num.is_integer() else num,
                "suffix": unit,
                "label": label[:12],
            }
        )
        if len(stats) >= max_n:
            break
    return stats


def split_agenda(body):
    """「下周看点」正文 → 日程行列表（③ 日程卡用）。

    优先用 parsed_news.json watch 条目显式 "agenda": [...]；否则按 ；/;
    拆分并去掉「看点一：」类前缀。
    """
    rows = [x.strip() for x in re.split(r"[；;]", body) if x.strip()]
    rows = [re.sub(r"^看点[一二三四五六七八九十0-9]+\s*[：:、.]\s*", "", r).rstrip("。") for r in rows]
    return [r for r in rows if r]


def build(parsed_path, out_dlg, out_seg=None):
    items = json.load(open(parsed_path, encoding="utf-8"))
    lines = []
    segs = []

    def add(speaker, text, bg=""):
        # 清理选题稿残留的配额标记，如「（八卦×1）」「（科技×4）」
        text = re.sub(r"[（(][^（）()]*×\d+[）)]", "", text).strip()
        lines.append(f"{speaker}：{text}")
        segs.append({"speaker": speaker, "text": text, "bg": bg})

    add("阿信", "大家好，我是阿信。")
    add("小蓝", "我是小蓝，周末特别版又跟大家见面啦。")

    brk = next((it for it in items if it["type"] == "breaking"), None)
    if brk:
        add("阿信", f"{BRK_AXIN}{brk['title']}。{brk['body']}", "breaking.jpg")
        bc = BRK_COMMENTS.get("breaking.jpg", {})
        add("小蓝", bc.get("xiaolan") or BRK_XIAOLAN, "breaking.jpg")

    news_items = [x for x in items if x["type"] == "news"]
    for idx, it in enumerate(news_items):
        img = it["img"]
        c = COMMENTS.get(img, {})
        lead = "进入本周要闻" if idx == 0 and not brk else ("接着聊本周要闻" if idx == 0 else f"接着聊{it['section']}")
        add("阿信", f"{lead}。{it['title']}。{it['body']}", img)
        add("小蓝", c.get("xiaolan") or XIAOLAN.get(it["section"], "这事儿挺有意思的。"), img)
        add("阿信", c.get("axin") or AXIN.get(it["section"], "确实值得持续关注。"), img)

    sm = next((it for it in items if it["type"] == "summary"), None)
    if sm:
        add("阿信", f"本周之最——{sm['body']}", "summary.jpg")
        # ② 数字滚动卡数据：用户显式 data 优先，否则从正文自动抽取
        segs[-1]["data"] = sm.get("data") or extract_stats(sm["body"])
        add("小蓝", "总结得到位，这一周信息量确实大。", "summary.jpg")

    wt = next((it for it in items if it["type"] == "watch"), None)
    if wt:
        add("阿信", f"下周看点——{wt['body']}", "watch.jpg")
        # ③ 日程卡数据：用户显式 agenda 优先，否则按分号拆正文
        segs[-1]["agenda"] = wt.get("agenda") or split_agenda(wt["body"])
        add("小蓝", "这几个我蹲了，到时候接着聊。", "watch.jpg")

    iv = next((it for it in items if it["type"] == "interactive"), None)
    if iv:
        add("阿信", f"最后给大家留一个互动话题。{iv['body']}", "interactive.jpg")
        add("小蓝", "欢迎在评论区聊聊你的看法。", "interactive.jpg")

    # 每期精选（固定收尾栏目，20260904 起新增）：有趣网站推荐
    pk = next((it for it in items if it["type"] == "pick"), None)
    if pk:
        add("阿信", f"每期精选——{pk['body']}", "pick.jpg")
        add("小蓝", "好玩的我先冲了，网址就在视频简介里，咱们下期见！", "pick.jpg")

    with open(out_dlg, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    if out_seg:
        json.dump(segs, open(out_seg, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[dialogue] {len(lines)} 句 -> {out_dlg}")


if __name__ == "__main__":
    p = sys.argv[1]
    o = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.join(PROJECT_ROOT, "output", "weekly", "20260828", "dialogue_script.txt")
    )
    s = os.path.join(os.path.dirname(o), "dialogue_segments.json")
    build(p, o, s)
