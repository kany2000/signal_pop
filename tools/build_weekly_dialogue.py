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
# 突发消息双主播定调（克制共情，不玩梗）
BRK_AXIN = "先给大家插播一条突发消息。"
BRK_XIAOLAN = "看到这消息我心里一沉，愿前方的人都能平安。"

# 本期（20260828）逐条定制双视角评论：按 img 精确匹配，覆盖板块模板，去重且针对内容
# （板块模板 XIAOLAN/AXIN 作为未命中时的回退；下期可沿用此结构补充新条目）
COMMENTS = {
    "news_01.jpg": {
        "xiaolan": "黄仁勋这是要把数据中心直接搬出地球啊，马斯克也真敢接，我就坐等它真上天那天。",
        "axin": "资本和算力绑得越来越紧，轨道数据中心要是成了，整个AI基建的玩法都得变。",
    },
    "news_02.jpg": {
        "xiaolan": "刚毕业一个月就被‘劝退’，这操作也太寒心了，真希望监管能盯住别成惯例。",
        "axin": "校招承诺和现实落差这么大，暴露的还是用工合规的缺口，得有人管。",
    },
    "news_03.jpg": {
        "xiaolan": "这瓜我嗑得有点离谱，长文加起诉，剧本都比电视剧敢写，咱们吃瓜别上头。",
        "axin": "热度是真高，不过真假让子弹飞一会儿，别被流量节奏带跑了。",
    },
    "news_04.jpg": {
        "xiaolan": "天呐太揪心了，接连三个台风往咱这边来，盼沿海的同胞都平平安安的。",
        "axin": "强度叠加、影响面广，渔船回港、应急响应都得跟上，后续复盘也关键。",
    },
    "news_05.jpg": {
        "xiaolan": "OpenAI自己下场造芯了，英伟达这下压力山大，咱们就等看价格战香不香。",
        "axin": "每瓦产出提快一倍，推理成本要是真降下来，中小团队最受益。",
    },
    "news_06.jpg": {
        "xiaolan": "最烦AI客服绕来绕去还甩锅‘自动生成’，这回消协发话，就该给人工留个口子。",
        "axin": "拿‘系统自动回复’当挡箭牌行不通了，责任承接机制得落地，这点消协说到点上了。",
    },
    "news_07.jpg": {
        "xiaolan": "苹果这2nm来得是猛，就是涨价也猛，我的钱包又要遭罪了。",
        "axin": "性能涨近三成、内存顶到512G，冲着本地大模型去的，专业用户会买账。",
    },
    "news_08.jpg": {
        "xiaolan": "小鹏这是真要造‘打工人’机器人了，9亿美元砸下去，2026底量产我可盯着呢。",
        "axin": "单轮私募破纪录，资本用脚投票具身智能，但量产交付才是真考验。",
    },
    "news_09.jpg": {
        "xiaolan": "欧洲这波热浪太吓人了，两万多人超额死亡，愿那边的人都挺过去。",
        "axin": "极端高温从偶发变常态，农业和内河航运先扛不住，城市韧性得重算。",
    },
    "news_10.jpg": {
        "xiaolan": "上海这‘沪八条’挺实在，首付降了、补贴有了，刚需家庭可以好好看看。",
        "axin": "外环外二套首付降到15%，‘金九银十’前松口子，信号意义大于金额。",
    },
    "news_11.jpg": {
        "xiaolan": "一年3600不算多，但‘按季直拨’这个动作好，就怕卡在最后一公里。",
        "axin": "基础标准加‘一卡通’直拨，方向对，关键看地方执行有没有水分。",
    },
    "news_12.jpg": {
        "xiaolan": "9月这批新规跟咱看病买药直接相关，记一下，别到时候白跑一趟。",
        "axin": "基药目录扩到794种、个账药店支付落地，都是贴近日常的实招。",
    },
    "news_13.jpg": {
        "xiaolan": "230万翻132倍，这账算得，资本玩得比戏还精彩，吃瓜群众只有羡慕。",
        "axin": "明星光环叠资本运作，质疑声起来也正常，团队得给市场一个交代。",
    },
    "news_14.jpg": {
        "xiaolan": "金鹰奖提名出来了，8月30号长沙揭晓，这届视后我提前押一波。",
        "axin": "719部参评、暑期档剧集混战，奖项背后也是平台和内容的一场暗拼。",
    },
}



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
        add("小蓝", BRK_XIAOLAN, "breaking.jpg")

    for it in [x for x in items if x["type"] == "news"]:
        img = it["img"]
        c = COMMENTS.get(img, {})
        add("阿信", f"接着聊{it['section']}。{it['title']}。{it['body']}", img)
        add("小蓝", c.get("xiaolan") or XIAOLAN.get(it["section"], "这事儿挺有意思的。"), img)
        add("阿信", c.get("axin") or AXIN.get(it["section"], "确实值得持续关注。"), img)

    sm = next((it for it in items if it["type"] == "summary"), None)
    if sm:
        add("阿信", f"本周之最——{sm['body']}", "summary.jpg")
        add("小蓝", "总结得到位，这一周信息量确实大。", "summary.jpg")

    wt = next((it for it in items if it["type"] == "watch"), None)
    if wt:
        add("阿信", f"下周看点——{wt['body']}", "watch.jpg")
        add("小蓝", "这几个我蹲了，到时候接着聊。", "watch.jpg")

    iv = next((it for it in items if it["type"] == "interactive"), None)
    if iv:
        add("阿信", f"最后给大家留一个互动话题。{iv['body']}", "interactive.jpg")
        add("小蓝", "欢迎在评论区聊聊你的看法，咱们下期见！", "interactive.jpg")

    with open(out_dlg, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    if out_seg:
        json.dump(segs, open(out_seg, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[dialogue] {len(lines)} 句 -> {out_dlg}")


if __name__ == "__main__":
    p = sys.argv[1]
    o = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJECT_ROOT, "output", "weekly", "20260828", "dialogue_script.txt")
    s = os.path.join(os.path.dirname(o), "dialogue_segments.json")
    build(p, o, s)
