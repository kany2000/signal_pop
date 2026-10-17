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
import hashlib

PROJECT_ROOT = "E:/projects/signal_pop"

# 阿信/小蓝 双视角观点（板块"回退候选池"仅作未命中 COMMENTS 时的兜底；本期各条已在 COMMENTS 精确定制）
#
# 2026-09-11 重构：原"固定说词"改为候选池 + 按制作日种子轮换抽取，
# 目标——① 不同期口播不雷同；② 同一期内不重复同一句；③ 措辞更口语自然，去 AI 模板感。
# （用户仍可在 dialogue_script.txt 里逐句手改得更贴合）

def _prep_date_from_path(parsed_path):
    """从 parsed_news.json 路径里抠出制作日 8 位日期，作轮换种子。"""
    m = re.search(r"weekly[\\/](\d{8})", parsed_path or "")
    return m.group(1) if m else "20260912"


def _variant(pool, used, st, phase=0):
    """候选池取一句：优先选本期内未用过的；st[0] 为轮换指针（按制作日种子初始化），
    phase 错开各栏目起点，避免多个栏目同取第0句。"""
    n = len(pool)
    if n == 0:
        return ""
    s = (st[0] + phase) % n
    for k in range(n):
        cand = pool[(s + k) % n]
        if cand not in used:
            st[0] = (s + k + 1) % 9973
            return cand
    st[0] = (s + 1) % 9973
    return pool[s]


def _opening(pool, date_str, phase=0, used=None):
    """开场白专用：按**制作日的周序号**取模，保证连续多期绝不重复。

    2026-10-16 用户反馈「我是小蓝，这周的硬货和瓜都给你们备齐了」每期都在念。
    根因有两层：① 池子只有 4 句；② 纯随机选句，相邻两期有概率撞车
    （实测 8 期里有 2 期完全重复）。这里改用「日期 → 周序号」确定性映射，
    相邻期必然落在不同池位上。

    date_str: 制作日 8 位字符串（20261016）
    phase:    错开同一期两个主播（阿信 0 / 小蓝 1）
    used:     本期已用集合，防同一期内部重复
    """
    n = len(pool)
    if n == 0:
        return ""
    try:
        y, m, d = int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8])
        days = (y * 372 + m * 31 + d)          # 整数日期序号
    except Exception:
        days = abs(hash(date_str)) % 100000
    idx = (days // 7 + phase) % n              # 每 7 天换一句 → 一周内不重复
    if used is not None:
        for k in range(n):
            cand = pool[(idx + k) % n]
            if cand not in used:
                used.add(cand)
                return cand
    cand = pool[idx]
    if used is not None:
        used.add(cand)
    return cand


# 突发消息双主播定调（克制共情，不玩梗）；小蓝回评按期定制（键 breaking.jpg，未命中回退候选池）
BRK_AXIN = "先来看今天的特别报道。"
BRK_XIAOLAN_POOL = [
    "看到这消息我心里一沉，愿前方的人都能平安。",
    "这事儿听着就揪心，先盼着人都平安。",
    "一上来就是重锤，心里跟着紧了一下。",
    "先把这个最要紧的消息放最前面。",
]
BRK_COMMENTS = {
    "breaking.jpg": {
        "xiaolan": "从百名开外一路打到登顶，这股韧劲儿真提气；不过她赛后说状态还在回升，前面的路还长着呢。",
    },
}

# 未命中 COMMENTS 时的回退候选池：按板块给多句口语化表达，期内不重复、跨期轮换。
XIAOLAN_POOL = {
    "科技": [
        "科技党狂喜，就盼别又只是 PPT，早点真用上才香。",
        "这波科技线我吃进去了，落地速度才是真章。",
        "技术宅直接关注，但咱们看疗效不看发布会。",
        "科技圈这操作，有点东西。",
    ],
    "民生": [
        "听着心里一紧，普通人真的不容易，盼好消息能兑现。",
        "民生无小事，落到口袋里才是真暖。",
        "这事儿跟咱日子挂钩，得替大伙盯紧。",
        "普通人视角：别整虚的，实惠到位就行。",
    ],
    "时事": [
        "天呐太揪心了，盼前方的都平平安安。",
        "这事牵动的人不少，后续处置得看仔细。",
        "看得心头一紧，愿一切平安。",
        "局势还在变，咱们接着关注。",
    ],
    "娱乐": [
        "这瓜我嗑了，真假让子弹再飞会儿。",
        "热度是真高，但别被节奏带跑。",
        "吃瓜归吃瓜，脑子得在线。",
        "这事儿有后续，我蹲着。",
    ],
}
AXIN_POOL = {
    "科技": [
        "这条我觉得含金量很高，赛道又往前迈了一步，值得长期盯。",
        "技术本身不稀奇，能规模落地才是真门槛。",
        "产业链这次动得挺快，后面看商业化。",
        "方向是对的，就看谁先把体验做扎实。",
    ],
    "民生": [
        "说到底都是民生账，政策落不落地、执行到不到位才是关键。",
        "文件好写，基层接得住才算数。",
        "惠民这事，透明和可持续比一时热闹重要。",
        "账算得清，老百姓才有体感。",
    ],
    "时事": [
        "数字摆在这，影响面不小，后续处置和复盘很关键。",
        "事件不小，关键看后续怎么收口。",
        "各方都在盯，信息得等权威口径。",
        "影响是长期的，别只看眼前。",
    ],
    "娱乐": [
        "热度是真高，不过咱们吃瓜归吃瓜，别被节奏带跑了。",
        "流量归流量，反转常有，别急着站队。",
        "热闹是热闹，咱留半分清醒。",
        "瓜可以嗑，但别当真太快。",
    ],
}

# 各栏目"固定收尾句"候选池（每期轮换、期内不重复）
# 2026-10-16：开场白池从 4 句扩到 12 句。原池只有 4 句，按日期种子轮换
# 很快撞车，用户反馈「我是小蓝，这周的硬货和瓜都给你们备齐了」每期都在念。
# 同时去掉「我是XX」式自我介绍开场——周末版每期都重新自我介绍很怪，
# 改成直接切内容语感，自我介绍只在首次或换声线时才需要。
OPEN_AXIN_POOL = [
    "大家好，我是阿信。",
    "各位周末好，我是阿信。",
    "又到周末，我是阿信。",
    "哈喽，阿信准时上线。",
    "周末这档又开场了，我是阿信。",
    "阿信这边信号就位，咱们直接开聊。",
    "先给各位问个好，阿信来也。",
    "周中攒下的瓜，这周一起聊。",
    "欢迎回来，我是阿信，这周依旧老规矩。",
    "阿信打卡，本周硬菜马上上桌。",
    "灯一开人就位，欢迎来到周末特别版。",
    "久违的一期长聊，今天咱们慢慢拆。",
]
OPEN_XIAOLAN_POOL = [
    "我是小蓝，周末特别版又跟大家见面啦。",
    "小蓝准时报到，这期周末特别版走起。",
    "我是小蓝，这周的硬货和瓜都给你们备齐了。",
    "小蓝来啦，坐稳，这期信息量有点猛。",
    "小蓝拎着热乎的来了，这期不灌水。",
    "刚坐下就等不及想开聊，这期看点不少。",
    "小蓝举手发言，先说结论：这周有料。",
    "别眨眼，今天这几条一个都不少。",
    "小蓝今天话少，但每句都在点上。",
    "开场先打个招呼，重头戏马上开始。",
    "小蓝蹭个开场，重点都在后面几条。",
    "这期的热闹，我先替你们感受了一半。",
]
SUMMARY_XIAOLAN_POOL = [
    "总结得到位，这一周信息量确实大。",
    "好家伙，这一周大事一件接一件。",
    "信息密度拉满，我先码住慢慢消化。",
    "一周干货有点多，得回炉捋一遍。",
]
WATCH_XIAOLAN_POOL = [
    "这几个我蹲了，到时候接着聊。",
    "下周的这几个，我笔记本已经记上了。",
    "这几个看点我先关注着，有进展再唠。",
    "下周的坑我先占好，咱们持续追踪。",
]
INTERACTIVE_XIAOLAN_POOL = [
    "欢迎在评论区聊聊你的看法。",
    "这题没标准答案，评论区等你们的高见。",
    "你怎么看？评论区咱们接着聊。",
    "说说你的态度，我在评论区翻牌。",
]
PICK_XIAOLAN_POOL = [
    "好玩的我先冲了，网址就在视频简介里，咱们下期见！",
    "这个我先玩为敬，链接放简介了，下期见！",
    "宝藏站奉上，网址在简介，咱们下期接着逛。",
    "这站我先码了，链接丢简介里，下期见！",
]

# 本期（20260925）逐条定制双视角评论：按 img 精确匹配，覆盖板块模板，去重且针对内容
COMMENTS = {
    # 20261016 期：按本期实际播报顺序逐条精写（勿用历史序号模板）
    "news_01.jpg": {  # 具身智能地铁 VELLINK
        "xiaolan": "地铁自己会看路况、自己排班表，这感觉科幻又实用；要是早十年上线，咱们通勤能省多少个早高峰的哈欠。",
        "axin": "关键在于它不是加装个传感器就算数，而是把感知、决策、执行串成闭环，节能超一成这个数字才是运营方真正买单的理由。",
    },
    "news_02.jpg": {  # 广交会 CF 奖
        "xiaolan": "820RR 百公里 2.81 秒，站台边看人抬着车走那画面也太帅了；不过我更想要那个 20 分钟做完的胶囊胃镜。",
        "axin": "一个代表中国制造的极致性能，一个代表下沉医疗的普惠方向，这两座至尊金奖恰好卡在产业升级的两端。",
    },
    "news_03.jpg": {  # 库克会见
        "xiaolan": "库克这趟来得很实在，供应链、创新生态、智能制造、绿色制造四件事全谈上了；希望这些承诺能变成实打实的岗位和产线。",
        "axin": "苹果在华 98% 的供应链支出、187 家供应商里 70 多家扎根广东，深圳河套实验室投了超 10 亿，这个基本盘值得继续加码。",
    },
    "news_08.jpg": {  # 广交会开幕
        "xiaolan": "逛展攻略我已经收藏了，去年的新能源车 今年变成机器人军团了；34 万境外采购商这个数，说明全球生意还是在往这儿聚。",
        "axin": "规模没扩但质量在换挡，新产品占比 23.2%、绿色产品 26% 双双创高，这个信号比展位数量更有含金量。",
    },
    "news_04.jpg": {  # 蛟龙号
        "xiaolan": "4500 米深海不是谁想去就能去，蛟龙号已经是第 466 次下潜了；每次看它入水的画面都还是得起鸡皮疙瘩。",
        "axin": "选在海浪升到三分之二处吊放入海，省动力又安全，这种经验主义积累才是深海作业真正的门槛。",
    },
    "news_05.jpg": {  # 女娲人体模型
        "xiaolan": "2659 万张图、5 到 20 秒建模，这速度。以前拍个数字人要排期几周，现在一杯茶的工夫；不过医疗相关的还是得让专业医生把关。",
        "axin": "从 3DGS 出发加标定几何，走的是既画得像又量得准的中间路线，这才是能真正用起来的路径。",
    },
    "news_06.jpg": {  # 比亚迪闪充
        "xiaolan": "5 分钟充到 70%，这速度真的把咖啡都喝完了；不过产能爬坡得跟上啊，不然订单再火也交付不了。",
        "axin": "9 月新能源销量 46.36 万辆创年内新高，需求端已经验证了，剩下就是二代刀片电池的产能节奏问题。",
    },
    "news_09.jpg": {  # 出口新高
        "xiaolan": "前三个季度出口 23.2 万亿，三季度单季就破 8 万亿，集成电路更是暴涨 99%；不过进口涨得比出口还快，这点挺有意思。",
        "axin": "这恰恰是好信号：进口高 5.9 个百分点说明不是靠压进口换来的。装备制造贡献近九成增量，AI 算力需求是实打实的刚需。",
    },
    "news_07.jpg": {  # AI 大模型霸榜
        "xiaolan": "中国大模型包揽全球前五，而美国这边 Meta 说这套开放权重模型是史上最强——结果三项跑分还被咱们的模型反超，这剧本真够反转的。",
        "axin": "一边是调用量 86.74 万亿 Token、连续 24 周霸榜，一边是开源自称最强却落后 Kimi K3 和 GLM 5.3，用量与利润的分水岭就摆在这儿。",
    },
    "news_10.jpg": {  # 世界灌溉工程遗产
        "xiaolan": "河南那条渠用火烧水激的法子开岩体，福建那边搞出了陂塘圳田的长藤结瓜，两千年前的老智慧现在还这么能打。",
        "axin": "四处全入选、总数来到 46 项，凹岸借离心力自动分离泥沙这类细节，说明古人早就把工程做成了系统科学。",
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
    used = set()
    prep_date = _prep_date_from_path(parsed_path)
    st = [int(hashlib.md5(prep_date.encode()).hexdigest(), 16) % 9973]

    def add(speaker, text, bg=""):
        # 清理选题稿残留的配额标记，如「（八卦×1）」「（科技×4）」
        text = re.sub(r"[（(][^（）()]*×\d+[）)]", "", text).strip()
        # 2026-10-17 纠正发音：网球/球赛比分「7-5、6-4」会被 TTS 念成「七减五、六减四」，转成「7比5、6比4」
        text = re.sub(r"(\d+)-(\d+)", r"\1比\2", text)
        lines.append(f"{speaker}：{text}")
        segs.append({"speaker": speaker, "text": text, "bg": bg})

    # 开场白：用 _opening（按周序号取模，连续多期不重复），不用随机 _variant
    oa = _opening(OPEN_AXIN_POOL, prep_date, phase=0, used=used)
    ox = _opening(OPEN_XIAOLAN_POOL, prep_date, phase=1, used=used)
    add("阿信", oa)
    add("小蓝", ox)

    brk = next((it for it in items if it["type"] == "breaking"), None)
    if brk:
        add("阿信", f"{BRK_AXIN}{brk['title']}。{brk.get('brief') or brk['body']}", "breaking.jpg")
        bc = BRK_COMMENTS.get("breaking.jpg", {})
        bx = bc.get("xiaolan")
        if not bx:
            bx = _variant(BRK_XIAOLAN_POOL, used, st, phase=2); used.add(bx)
        add("小蓝", bx, "breaking.jpg")

    news_items = [x for x in items if x["type"] == "news"]
    for idx, it in enumerate(news_items):
        img = it["img"]
        c = COMMENTS.get(img, {})
        lead = "进入本周要闻" if idx == 0 and not brk else ("接着聊本周要闻" if idx == 0 else f"接着聊{it['section']}")
        # brief = 口播摘要（控制在 80~140 字）；缺失时回退整段 body。
        # 2026-10-16 起铁律：正文 body 只进字幕/画面，不再整段上口播——
        # 实测整段口播会把单条拉到 60~160 秒，整片从 9 分钟膨胀到 21 分钟。
        spoken = it.get("brief") or it["body"]
        add("阿信", f"{lead}。{it['title']}。{spoken}", img)
        xc = c.get("xiaolan")
        if not xc:
            xc = _variant(XIAOLAN_POOL.get(it["section"], []), used, st)
            if xc:
                used.add(xc)
        if not xc:
            xc = "这事儿挺有意思的。"
        ac = c.get("axin")
        if not ac:
            ac = _variant(AXIN_POOL.get(it["section"], []), used, st)
            if ac:
                used.add(ac)
        if not ac:
            ac = "确实值得持续关注。"
        add("小蓝", xc, img)
        add("阿信", ac, img)

    sm = next((it for it in items if it["type"] == "summary"), None)
    if sm:
        add("阿信", f"本周之最——{sm['body']}", "summary.jpg")
        # ② 数字滚动卡数据：用户显式 data 优先，否则从正文自动抽取
        segs[-1]["data"] = sm.get("data") or extract_stats(sm["body"])
        sx = _variant(SUMMARY_XIAOLAN_POOL, used, st, phase=3); used.add(sx)
        add("小蓝", sx, "summary.jpg")

    wt = next((it for it in items if it["type"] == "watch"), None)
    if wt:
        add("阿信", f"下周看点——{wt['body']}", "watch.jpg")
        # ③ 日程卡数据：用户显式 agenda 优先，否则按分号拆正文
        segs[-1]["agenda"] = wt.get("agenda") or split_agenda(wt["body"])
        wx = _variant(WATCH_XIAOLAN_POOL, used, st, phase=5); used.add(wx)
        add("小蓝", wx, "watch.jpg")

    iv = next((it for it in items if it["type"] == "interactive"), None)
    if iv:
        add("阿信", f"最后给大家留一个互动话题。{iv['body']}", "interactive.jpg")
        ix = _variant(INTERACTIVE_XIAOLAN_POOL, used, st, phase=7); used.add(ix)
        add("小蓝", ix, "interactive.jpg")

    # 每期精选（固定收尾栏目，20260904 起新增）：有趣网站推荐
    pk = next((it for it in items if it["type"] == "pick"), None)
    if pk:
        add("阿信", f"每期精选——{pk['body']}", "pick.jpg")
        px = _variant(PICK_XIAOLAN_POOL, used, st, phase=11); used.add(px)
        add("小蓝", px, "pick.jpg")

    # 收尾新环节「大家一起聊经济」（2026-09-20 固化，20260925 起上线）
    econ_md = os.path.join(os.path.dirname(parsed_path), "section_economy_talk_v1.md")
    if os.path.exists(econ_md):
        print(f"  📈 接入「大家一起聊经济」新环节: {econ_md}")
        with open(econ_md, encoding="utf-8") as ef:
            econ_text = ef.read()
        # 提取对白行 **小蓝**：... / **阿信**：...
        dialogue_pattern = re.compile(r"\*\*(阿信|小蓝)\*\*：([^\n]+)")
        matches = dialogue_pattern.findall(econ_text)
        # 幻灯映射：1-3句->slide_1, 4-5句->slide_2, 6-7句->slide_3, 8-11句->slide_4
        for idx, (spk, txt) in enumerate(matches):
            if idx < 3:
                bg_img = "econ_slide_1.jpg"
            elif idx < 5:
                bg_img = "econ_slide_2.jpg"
            elif idx < 7:
                bg_img = "econ_slide_3.jpg"
            else:
                bg_img = "econ_slide_4.jpg"
            add(spk, txt.strip(), bg_img)

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
