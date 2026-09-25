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
        "xiaolan": "一天迁移68万行代码，打工人直呼过瘾；不过工具越强咱们越得保住真本事，别把脑子彻底外包了。",
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

# 本期（20260925）逐条定制双视角评论：按 img 精确匹配，覆盖板块模板，去重且针对内容
COMMENTS = {
    "news_01.jpg": {
        "xiaolan": "秋捕开网鱼虾满舱，大豆玉米机收铺开，这金秋丰收的场景看着就让人踏实。",
        "axin": "江浙水产日发万斤带动增收，东北粮仓开镰丰收在望，农业稳产保供是经济最坚固的压舱石。",
    },
    "news_02.jpg": {
        "xiaolan": "虚假标签和问题食品零容忍，市场监管动真格的，咱们吃进嘴里的每一口才能更安心。",
        "axin": "常态化抽检结合平台源头治理，重拳打击以次充好，食品安全必须用最严标准兜住底线。",
    },
    "news_03.jpg": {
        "xiaolan": "部分小银行逆势给存款加息，这羊毛到底能不能薅？现在利息稍微高一点点都格外显眼。",
        "axin": "季末考核下的阶段性揽储而已，大行趋势没变，大额存单甚至出现长短倒挂，存钱更得看清锁定期限。",
    },
    "news_04.jpg": {
        "xiaolan": "以前车企卷百公里加速，现在直接卷造机器人，以后买车该不会直接送个贴身家务保姆吧？",
        "axin": "汽车的三电、智驾算法和传感器供应链与机器人重合度超70%，车间又是天然训练场，做人形机器人确实是最顺理成章的第二曲线。",
    },
    "news_05.jpg": {
        "xiaolan": "40多年融化11万亿吨冰，海平面肉眼可见地抬升，大自然敲响的警钟越来越急促了。",
        "axin": "42项卫星观测坐实了极端气候影响，超八成冰体加速滑入海洋，减碳和极地保护真不能再停留在口头上了。",
    },
    "news_06.jpg": {
        "xiaolan": "老牌餐饮每次有点风吹草动就容易上热搜，还是希望良心企业能挺过消费阵痛，把菜品踏实做好。",
        "axin": "5.19%的直接股权出质属于企业正常的融资动作，官方也辟谣了倒闭传闻，客观看待餐饮业的周期调整，不信谣不传谣。",
    },
    "news_07.jpg": {
        "xiaolan": "96G大显存只要不到七成价格，民间华强北硬核狂飙，大模型玩家的钱包总算有救了。",
        "axin": "双面贴颗粒加定制固件，跑本地大模型确实解渴；不过改装卡的技术稳定性和保修还是得留三分清醒，咱们先看行业实测。",
    },
    "news_08.jpg": {
        "xiaolan": "医生不用敲一行代码，嘴上说说就能定制治病救人的AI工具，这才是科技真正造福生活的样子。",
        "axin": "专属医院系统把多学科会诊压缩到分钟级，让一线临床专家从使用者变成开发者，医疗AI落地走出了实打实的新路子。",
    },
    "news_09.jpg": {
        "xiaolan": "42光年的粒子尾迹，天关卫星这一把直接揪住了脉冲星的狐狸尾巴，很有宇宙高铁狂飙的画面感了。",
        "axin": "天地双镜联手打破了宇宙线四散的百年假说，高能粒子在磁轨道定向疾驰，中国空间科学这波突破含金量极高。",
    },
    "news_10.jpg": {
        "xiaolan": "超七成患者从不吸烟、女性还占了多数，这二手烟和油烟杀伤力真不小，吓得我赶紧去翻了翻体检单。",
        "axin": "钟南山院士也强调了，体检偶发的结节九成以上都是良性，别过度恐慌；中年女性定期做低剂量螺旋CT、科学随访才是正解。",
    },
    "news_11.jpg": {
        "xiaolan": "代码隐私争议直接开源接受全行业监督，这波整改速度和透明度给技术圈打了样。",
        "axin": "切断本地自动上传、清空云端快照，开源接受第三方审计，在数据安全红线面前，唯有彻底透明才能重塑开发者信任。",
    },
    "news_12.jpg": {
        "xiaolan": "月租1500起还能天天有人打扫卫生，没有黑中介套路，年轻人租房听着真香。",
        "axin": "1500多在偏远分店，市区核心地段依然要三五千；加上商用水电和没有厨房，酒店系长租能不能打破传统租赁格局，还得看长效运营。",
    },
    "news_13.jpg": {
        "xiaolan": "大家听到了吗？咱们信号弹现在的播音用的就是阿里千问语音，这波大降价等于官方直接给咱们生产线省钱啦！",
        "axin": "TTS降七成、ASR降九成五，把全双工实时交互做到白菜价，中美AI巨头这一轮卷价格，最终受益的都是普通创作者。",
    },
    "news_14.jpg": {
        "xiaolan": "漂泊海外数十载，十二件珍贵文物终于平安回家，看着心里暖洋洋的。",
        "axin": "在国际公约框架下由警方查获并促成归还，这是法理与文明对话的正向成果，守护文化根脉永远在路上。",
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
