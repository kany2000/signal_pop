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
        "xiaolan": "折叠屏iPhone终于等到了，7.6英寸内屏快赶上小平板，就盼真机价格别太劝退。",
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
OPEN_AXIN_POOL = [
    "大家好，我是阿信。",
    "各位周末好，我是阿信。",
    "又到周末，我是阿信。",
    "哈喽，阿信准时上线。",
]
OPEN_XIAOLAN_POOL = [
    "我是小蓝，周末特别版又跟大家见面啦。",
    "小蓝准时报到，这期周末特别版走起。",
    "我是小蓝，这周的硬货和瓜都给你们备齐了。",
    "小蓝来啦，坐稳，这期信息量有点猛。",
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

# 本期（20260904）逐条定制双视角评论：按 img 精确匹配，覆盖板块模板，去重且针对内容
# （板块模板 XIAOLAN/AXIN 作为未命中时的回退；下期可沿用此结构补充新条目）
COMMENTS = {
    "news_01.jpg": {
        "xiaolan": "开车太慢也要被AI点名，以后上快速路可得支棱起来；那位边刷手机边龟速的大哥，真是社死现场。",
        "axin": "用ETC、定位和视频多源数据锁定龟速车，这套AI治理思路挺实，通行效率提升约20%是真金白银。",
    },
    "news_02.jpg": {
        "xiaolan": "连研究员都炒了鱿鱼喊停，这事儿听着比科幻片还真，就希望别真是'狼来了'。",
        "axin": "从内部人辞职喊话到美英立法讨论，放慢自我改进AI的声浪在变大，但超级智能对齐至今没靠谱方案，这才是真问题。",
    },
    "news_03.jpg": {
        "xiaolan": "DeepSeek又放大招，HBM需求砍到四分之一，这性价比卷得友商头皮发麻。",
        "axin": "552B MoE加压缩KV Cache，把部署成本打到地板，开源模型这波是真普惠。",
    },
    "news_04.jpg": {
        "xiaolan": "一张票根又能吃饭又能住店，这羊毛我先把攻略收藏了。",
        "axin": "票根经济把过境流量变成跨场景消费，财政小补贴撬动大盘，比发券高明。",
    },
    "news_05.jpg": {
        "xiaolan": "最高法给AI换脸拟声划红线了，以后'AI复活'、仿冒声音不能随便来，这波规制来得及时。",
        "axin": "首部国家级涉AI司法裁判规则落地，把人格权、声音权写进明文，技术向上向善得有法律兜底。",
    },
    # —— 20260912 期：地月双向高速激光通信（news_06）为本期新选科技硬核条目 ——
    "news_06.jpg": {
        "xiaolan": "40万公里外给月球发激光，一张8K月图12秒就传回来，这速度有点科幻照进现实。",
        "axin": "上行1.25Mbps、下行100Mbps，地月双向激光链路打通，载人登月和月球科研站的信息高速路有了着落。",
    },
    "news_07.jpg": {
        "xiaolan": "刘翔这事看着真唏嘘，雅典奥运金牌得主，退役安置却拉锯了这么多年，好在买断落定、还把11年的补助全捐去救灾了。",
        "axin": "49.4万买断、与体育局再无关联，但他捅破的是退役运动员'在编不在岗'的老伤疤——分广告费不说安置，保障制度得跟上。",
    },
    "news_08.jpg": {
        "xiaolan": "吉利银河TT十几万就能买纯电轿跑，零百3.8秒，这性能价格比有点香。",
        "axin": "800V平台加425kW四驱，10到15万级把性能卷起来，性价比牌打得准。",
    },
    "news_09.jpg": {
        "xiaolan": "金融强国'十五五'规划出炉，2030年要搭好现代金融体系框架，钱往科技和硬科技流的路子更清了。",
        "axin": "科技型企业贷款26.9万亿、同比增近18%，保险资金也要投早投小投硬科技，新质生产力融资底座在夯实。",
    },
    "news_10.jpg": {
        "xiaolan": "丝绸茶叶瓷器中药都出国家政策了，老祖宗的手艺这回真被当宝贝。",
        "axin": "六部门首推历史经典产业意见，'历史经典+旅游'入列，老工艺搭上文旅快车。",
    },
    "news_11.jpg": {
        "xiaolan": "外卖骑手、自由职业者的医保能按月累计了，这回新就业群体参保总算少点后顾之忧。",
        "axin": "超大城市取消户籍限制、平台还能补一点，灵活就业的医保衔接从'断档'往'连续'走对了路。",
    },
    "news_12.jpg": {
        "xiaolan": "9月错峰去云南真聪明，人少价低体验还不打折，我也想请年假了。",
        "axin": "暑期退潮后文旅'淡季不淡'，错峰游从精打细算变成从容出行的共识。",
    },
    "news_13.jpg": {
        "xiaolan": "千问眼镜能刷眼支付了，以后眨个眼就结账，科技感拉满但我也怕忘带脸。",
        "axin": "虹膜识别把身份匹配做细，AI眼镜从'看'走向'付'，穿戴设备的支付场景又近一步。",
    },
    "news_14.jpg": {
        "xiaolan": "前8个月外贸还涨了6%，民企占了外贸半壁多，咱们这外贸韧性真不是吹的。",
        "axin": "28.58万亿、民企进出口增10.5%占55.1%，超大城市之外民营企业正扛着外贸主力军的位置。",
    },
    # —— 20260912 期新增：CIPS 跨境支付扩容（news_15）——
    "news_15.jpg": {
        "xiaolan": "CIPS又签下11家外资银行，人民币跨境支付的朋友圈越拓越大了。",
        "axin": "覆盖133个国家和地区、近5300家法人银行，跨境保函也上线，人民币国际化的地基更实了。",
    },
    "news_16.jpg": {
        "xiaolan": "一场发布会把手机、手表、耳机全更新了，就 Pro 的价格有点劝退，不过陶瓷表回归是真香。",
        "axin": "全系上新还砍掉标准版 iPhone 18，苹果是铁了心冲高端；Ternus 首秀定调'亮新篇'，产品重心全面倒向 Pro 和折叠。",
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
    st = [int(hashlib.md5(_prep_date_from_path(parsed_path).encode()).hexdigest(), 16) % 9973]

    def add(speaker, text, bg=""):
        # 清理选题稿残留的配额标记，如「（八卦×1）」「（科技×4）」
        text = re.sub(r"[（(][^（）()]*×\d+[）)]", "", text).strip()
        lines.append(f"{speaker}：{text}")
        segs.append({"speaker": speaker, "text": text, "bg": bg})

    oa = _variant(OPEN_AXIN_POOL, used, st, phase=0); used.add(oa)
    ox = _variant(OPEN_XIAOLAN_POOL, used, st, phase=1); used.add(ox)
    add("阿信", oa)
    add("小蓝", ox)

    brk = next((it for it in items if it["type"] == "breaking"), None)
    if brk:
        add("阿信", f"{BRK_AXIN}{brk['title']}。{brk['body']}", "breaking.jpg")
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
        add("阿信", f"{lead}。{it['title']}。{it['body']}", img)
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
