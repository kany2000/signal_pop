#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""20261102 期「大家一起聊经济」· huashu-art-motion 分镜 spec 生成 + 批量渲染拼接。

与 tools/build_econ_huashu.py 同一工艺（theme="ink" 全片统一色板 + 统一安全框 + 长段拆多镜），
但镜头内容按本期「加息浪潮来了，普通人怎么办？」主题重写，并针对 G 盘新路径做了适配：
  · PROJECT_ROOT / HUASHU_ENGINE 改为自动探测（环境变量 SIGNAL_POP_ROOT / SIGNAL_POP_HUASHU_ENGINE）
  · 渲染不再依赖 uv：直接用当前解释器的 playwright（render.py 只依赖 playwright + 标准库）
  · FFMPEG 从项目 bin/ 取

用法：
  python tools/build_econ_huashu_20261102.py            # 生成 spec + 渲染拼接
  python tools/build_econ_huashu_20261102.py --specs-only
"""
import os
import sys
import json
import subprocess

PROJECT_ROOT = os.environ.get("SIGNAL_POP_ROOT", "G:/projects/signal_pop")
HUASHU_ENGINE = os.environ.get(
    "SIGNAL_POP_HUASHU_ENGINE", "G:/projects/_dl/huashu/huashu-art-motion-main/scripts/engine"
)
FFMPEG_BIN = os.path.join(PROJECT_ROOT, "bin", "ffmpeg-9.0.1-essentials_build", "bin")
FFMPEG = os.path.join(FFMPEG_BIN, "ffmpeg.exe")

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "20261102"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
ECON_AUDIO_JSON = os.path.join(OUT_DIR, "econ_audio", "tts_segments.json")
ECON_SPECS_DIR = os.path.join(OUT_DIR, "econ_huashu", "specs")
ECON_CLIPS_DIR = os.path.join(OUT_DIR, "econ_huashu", "clips")
FINAL_BG_MP4 = os.path.join(OUT_DIR, "econ_huashu", "econ_huashu_bg.mp4")

FPS = 30
SAFE = {"top": 76, "bottom": 128, "left": 148, "right": 148}
THEME = "ink"


def _lint_y5(shots):
    """y5_kinetic_type 排版自检（引擎不报错但会静默出问题的三类坑）：
    ① 主词 >4 汉字：字号固定 300px，5 字以上占满 86% 画宽，左边缘撞左上角 data.label；
    ② data.label >3 字：标签固定画在 x=140 固定位，是主词的水平避让位；
    ③ highlight.data.word 不在「当前页主词」里：荧光笔只刷主词，词不在就整下静默失效。
    """
    bad = 0
    for sh in shots:
        if sh["grammar"] != "y5_kinetic_type":
            continue
        pages = sorted([c for c in sh["cues"] if c["kind"] in ("point", "title", "number")],
                       key=lambda c: c["at"])
        for c in sh["cues"]:
            errs = []
            t = c.get("text", "")
            dat = c.get("data") or {}
            if c["kind"] in ("point", "title"):
                if len(t) > 4:
                    errs.append(f"主词过长({len(t)}字):{t}")
                if len(dat.get("label", "")) > 3:
                    errs.append(f"label过长({len(dat.get('label',''))}字):{dat.get('label','')}")
            if c["kind"] == "highlight" and dat.get("word"):
                cur = [q for q in pages if q["at"] <= c["at"] + 1e-6]
                cur_text = cur[-1].get("text", "") if cur else ""
                if dat["word"] not in cur_text:
                    errs.append(f"highlight词「{dat['word']}」不在当前页主词「{cur_text}」")
            if errs:
                bad += 1
                print(f"  [y5排版告警] {sh['id']}: {'; '.join(errs)}")
    if bad:
        print(f"⚠️ y5 排版告警 {bad} 处（建议修正后重渲）")
    else:
        print("✅ y5 排版自检通过")
    return bad


def build_specs():
    segs = json.load(open(ECON_AUDIO_JSON, encoding="utf-8"))
    assert len(segs) == 13, f"期望 13 段，实际 {len(segs)} 段"

    # 每段精确秒数转整数帧（累计帧与累计时间严丝合缝）
    cum_t = 0.0
    seg_frames = []
    prev_f = 0
    for s in segs:
        cum_t += s["dur"]
        cur_f = round(cum_t * FPS)
        seg_frames.append(cur_f - prev_f)
        prev_f = cur_f

    durs = [f / FPS for f in seg_frames]
    print("13 段帧对齐时长(s):", [round(d, 3) for d in durs], "总计:", round(sum(durs), 3))

    shots = []

    # --- 段0 (小蓝 14.34s)：开场点题「加息」——拆 2 镜 ---
    # ⚠️ y5_kinetic_type 排版铁律（本期踩坑后固化）：
    #   ① 主词（text）≤4 个汉字 —— 字号固定 300px，5 字以上会占满 86% 画宽，左边缘撞左上角 data.label；
    #   ② data.label ≤3 字（标签固定画在 x=140 的左上角，是主词的水平避让位）；
    #   ③ highlight 只刷主词里的词，data.word 必须出现在 text 中，否则整下不生效（引擎会告警）；
    #   ④ 细节信息一律放 sub（副句，可两行），不放主词。
    d0_a = round(seg_frames[0] * 0.50) / FPS
    d0_b = (seg_frames[0] - round(seg_frames[0] * 0.50)) / FPS
    shots.append({
        "id": "shot_01",
        "grammar": "y5_kinetic_type",
        "duration": d0_a,
        "cues": [
            {"at": 0.2, "kind": "point", "text": "加息", "sub": "借钱成本变贵了",
             "data": {"label": "开场", "key": "借钱成本"}},
            {"at": 2.4, "kind": "point", "text": "美联储", "sub": "就业数据强劲，市场押注加息",
             "data": {"label": "央行", "key": "强劲"}},
            {"at": 4.4, "kind": "point", "text": "欧央行", "sub": "通胀逼近 4%",
             "data": {"label": "央行", "key": "通胀"}},
            {"at": 6.2, "kind": "point", "text": "日央行", "sub": "会不会退出负利率",
             "data": {"label": "央行", "key": "负利率"}},
            {"at": 7.6, "kind": "highlight", "data": {"word": "日央行"}},
        ],
    })
    shots.append({
        "id": "shot_02",
        "grammar": "y3_whiteboard",
        "duration": d0_b,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "这跟我们有什么关系"},
            {"at": 1.2, "kind": "draw", "text": "企业贷款：扩张变贵", "data": {"icon": "gear"}},
            {"at": 3.0, "kind": "draw", "text": "居民房贷：月供变高", "data": {"icon": "home"}},
            {"at": 4.8, "kind": "draw", "text": "手头现金：流动性收缩", "data": {"icon": "network"}},
            {"at": 6.4, "kind": "highlight", "data": {"target": "draw", "index": 2}},
        ],
    })

    # --- 段1 (阿信 11.67s)：加息本质 + 流动性收缩，拆 2 镜 ---
    f1_a = round(seg_frames[1] * 0.48)
    f1_b = seg_frames[1] - f1_a
    shots.append({
        "id": "shot_03",
        "grammar": "t1_3b1b",
        "duration": f1_a / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "加息的本质：抬高借钱成本"},
            {"at": 1.2, "kind": "equation", "data": {"tokens": [
                {"s": "利率", "col": "YELLOW"}, {"s": "↑", "gap": 18},
                {"s": "借贷成本", "col": "RED_C"}, {"s": "↑", "gap": 18},
                {"s": "流动性", "col": "BLUE_C"}, {"s": "↓", "gap": 18},
                {"s": "收缩", "col": "GREEN_C"},
            ]}},
            {"at": 3.6, "kind": "point", "text": "利率高了，贷款扩张就变贵"},
            {"at": 5.6, "kind": "highlight", "data": {"target": "equation"}},
        ],
    })
    shots.append({
        "id": "shot_04",
        "grammar": "y3_whiteboard",
        "duration": f1_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "流动性收缩：钱的流转变慢"},
            {"at": 1.2, "kind": "draw", "text": "原本在市场上流动的钱", "data": {"icon": "network"}},
            {"at": 3.0, "kind": "draw", "text": "被高利率吸住、放缓", "data": {"icon": "bulb"}},
            {"at": 4.6, "kind": "point", "text": "不是钱没了，是流速降下来了"},
            {"at": 6.2, "kind": "highlight", "data": {"target": "draw", "index": 1}},
        ],
    })

    # --- 段2 (小蓝 4.89s)：反直觉追问 ---
    shots.append({
        "id": "shot_05",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[2] / FPS,
        "cues": [
            {"at": 0.15, "kind": "point", "text": "反直觉", "sub": "主动让钱变贵",
             "data": {"label": "追问", "key": "主动"}},
            {"at": 2.2, "kind": "highlight", "data": {"word": "反直觉"}},
        ],
    })

    # --- 段3 (阿信 18.57s)：通胀 → 加息降温 → 踩刹车，拆 2 镜 ---
    f3_a = round(seg_frames[3] * 0.52)
    f3_b = seg_frames[3] - f3_a
    shots.append({
        "id": "shot_06",
        "grammar": "t3_finance_chart",
        "duration": f3_a / FPS,
        "data": {
            "title": "通胀：同一笔钱买到的东西变少",
            "unit": "代表性经济体 CPI 同比涨幅（%，近期水平示意）",
            "source": "来源：公开市场宏观数据整理（欧洲物价压力居前）",
            "badge": "宏观机制示意",
            "chart": "bar",
            "decimals": 1,
            "suffix": "%",
            "series": [
                {"label": "欧元区参考", "value": 3.9},
                {"label": "美国参考", "value": 3.1},
                {"label": "日本参考", "value": 2.4},
                {"label": "中国参考", "value": 0.9},
            ],
            "highlight": {"index": 0, "text": "逼近 4%", "sub": "购买力被物价侵蚀"},
        },
        "cues": [
            {"at": 0.2, "kind": "bar", "data": {"index": [0, 1]}},
            {"at": 2.4, "kind": "bar", "data": {"index": 2}},
            {"at": 4.2, "kind": "bar", "data": {"index": 3}},
            {"at": 6.0, "kind": "highlight"},
        ],
    })
    shots.append({
        "id": "shot_07",
        "grammar": "y3_whiteboard",
        "duration": f3_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "加息 = 给经济踩刹车"},
            {"at": 1.2, "kind": "draw", "text": "通胀高 → 加息降温", "data": {"icon": "target"}},
            {"at": 3.0, "kind": "draw", "text": "钱流通慢下来 → 物价降温", "data": {"icon": "network"}},
            {"at": 4.8, "kind": "point", "text": "但刹车要踩对力度"},
            {"at": 6.2, "kind": "highlight", "data": {"target": "draw", "index": 1}},
        ],
    })

    # --- 段4 (小蓝 2.71s)：三大央行同时加息的追问 ---
    shots.append({
        "id": "shot_08",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[4] / FPS,
        "cues": [
            {"at": 0.1, "kind": "point", "text": "共振", "sub": "三大央行同时收紧",
             "data": {"label": "追问", "key": "同时"}},
            {"at": 1.6, "kind": "highlight", "data": {"word": "共振"}},
        ],
    })

    # --- 段5 (阿信 23.72s)：共振 = 水波纹扩散，拆 2 镜 ---
    f5_a = round(seg_frames[5] * 0.45)
    f5_b = seg_frames[5] - f5_a
    shots.append({
        "id": "shot_09",
        "grammar": "y3_whiteboard",
        "duration": f5_a / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "共振：像水波纹一样扩散"},
            {"at": 1.2, "kind": "draw", "text": "美联储 + 欧央行 + 日央行", "data": {"icon": "network"}},
            {"at": 3.0, "kind": "draw", "text": "全球借贷成本一起走高", "data": {"icon": "stack"}},
            {"at": 4.8, "kind": "point", "text": "影响一圈圈荡开"},
            {"at": 6.4, "kind": "highlight", "data": {"target": "draw", "index": 1}},
        ],
    })
    shots.append({
        "id": "shot_10",
        "grammar": "y3_whiteboard",
        "duration": f5_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "被波及的资产"},
            {"at": 1.2, "kind": "draw", "text": "股市：估值被压低", "data": {"icon": "chart"}},
            {"at": 3.0, "kind": "draw", "text": "债券：价格跟着跌", "data": {"icon": "stack"}},
            {"at": 4.8, "kind": "draw", "text": "汇率：承受资本流向压力", "data": {"icon": "gear"}},
            {"at": 6.6, "kind": "highlight", "data": {"target": "draw", "index": 2}},
        ],
    })

    # --- 段6 (小蓝 7.97s)：A股 20% 跌幅追问 ---
    shots.append({
        "id": "shot_11",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[6] / FPS,
        "cues": [
            {"at": 0.2, "kind": "point", "text": "跌两成", "sub": "创业板 · 科创板",
             "data": {"label": "市场", "key": "创业板"}},
            {"at": 3.0, "kind": "point", "text": "有关吗", "sub": "跟这轮加息有关系吗",
             "data": {"label": "追问", "key": "加息"}},
            {"at": 5.4, "kind": "highlight", "data": {"word": "有关吗"}},
        ],
    })

    # --- 段7 (阿信 29.59s)：全球流动性 + 国内政策工具 + 核心矛盾，拆 3 镜 ---
    f7_a = round(seg_frames[7] * 0.30)
    f7_b = round(seg_frames[7] * 0.33)
    f7_c = seg_frames[7] - f7_a - f7_b
    shots.append({
        "id": "shot_12",
        "grammar": "y3_whiteboard",
        "duration": f7_a / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "全球收缩下的资金流向"},
            {"at": 1.2, "kind": "draw", "text": "资金倾向撤出风险资产", "data": {"icon": "cross"}},
            {"at": 3.2, "kind": "draw", "text": "新兴市场承受更大压力", "data": {"icon": "gear"}},
            {"at": 5.4, "kind": "point", "text": "有一部分关联"},
            {"at": 7.0, "kind": "highlight", "data": {"target": "draw", "index": 1}},
        ],
    })
    shots.append({
        "id": "shot_13",
        "grammar": "y3_whiteboard",
        "duration": f7_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "监管出手：给市场开资金通道"},
            {"at": 1.2, "kind": "draw", "text": "互换便利", "data": {"icon": "network"}},
            {"at": 3.0, "kind": "draw", "text": "股票回购增持再贷款", "data": {"icon": "stack"}},
            {"at": 4.8, "kind": "point", "text": "真金白银的流动性注入"},
            {"at": 6.6, "kind": "highlight", "data": {"target": "draw", "index": 0}},
        ],
    })
    shots.append({
        "id": "shot_14",
        "grammar": "t1_3b1b",
        "duration": f7_c / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "核心矛盾：短期输血 ≠ 长期信心"},
            {"at": 1.4, "kind": "equation", "data": {"tokens": [
                {"s": "短期输血", "col": "BLUE_C"}, {"s": "⇒", "gap": 18},
                {"s": "情绪稳住", "col": "YELLOW"},
            ]}},
            {"at": 3.8, "kind": "point", "text": "但未必改变对长期盈利的判断"},
            {"at": 6.0, "kind": "point", "text": "稳信心靠基本面，不只靠政策工具"},
            {"at": 8.2, "kind": "highlight", "data": {"target": "equation"}},
        ],
    })

    # --- 段8 (小蓝 4.72s)：认知追问 ---
    shots.append({
        "id": "shot_15",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[8] / FPS,
        "cues": [
            {"at": 0.15, "kind": "point", "text": "记什么", "sub": "普通人的认知锚点",
             "data": {"label": "认知", "key": "锚点"}},
            {"at": 2.2, "kind": "highlight", "data": {"word": "记什么"}},
        ],
    })

    # --- 段9 (阿信 25.65s)：三点总结，拆 2 镜 ---
    f9_a = round(seg_frames[9] * 0.58)
    f9_b = seg_frames[9] - f9_a
    shots.append({
        "id": "shot_16",
        "grammar": "y3_whiteboard",
        "duration": f9_a / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "记住这三点"},
            {"at": 1.2, "kind": "draw", "text": "一、加息不是孤立事件", "data": {"icon": "network"}},
            {"at": 3.2, "kind": "point", "text": "背后是全球通胀与增长的博弈"},
            {"at": 5.2, "kind": "draw", "text": "二、流动性收缩期资产普遍承压", "data": {"icon": "chart"}},
            {"at": 7.4, "kind": "point", "text": "这是机制规律，不是哪个市场独有"},
        ],
    })
    shots.append({
        "id": "shot_17",
        "grammar": "t1_3b1b",
        "duration": f9_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "第三点最关键"},
            {"at": 1.2, "kind": "equation", "data": {"tokens": [
                {"s": "政策工具", "col": "BLUE_C"}, {"s": "只能", "gap": 18},
                {"s": "延缓震荡", "col": "YELLOW"}, {"s": "≠", "gap": 18},
                {"s": "基本面", "col": "GREEN_C"},
            ]}},
            {"at": 3.8, "kind": "point", "text": "基本面才是最终的锚"},
            {"at": 6.0, "kind": "point", "text": "看懂机制，就不会被波动吓到"},
            {"at": 8.0, "kind": "highlight", "data": {"target": "equation"}},
        ],
    })

    # --- 段10 (小蓝 5.51s)：小蓝点题 ---
    shots.append({
        "id": "shot_18",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[10] / FPS,
        "cues": [
            {"at": 0.2, "kind": "point", "text": "看机制", "sub": "比猜短期涨跌更有价值",
             "data": {"label": "总结", "key": "机制"}},
            {"at": 2.4, "kind": "highlight", "data": {"word": "看机制"}},
        ],
    })

    # --- 段11 (阿信 7.49s)：合规句 ---
    shots.append({
        "id": "shot_19",
        "grammar": "y3_whiteboard",
        "duration": seg_frames[11] / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "理性认知 · 独立判断"},
            {"at": 1.2, "kind": "draw", "text": "纯经济学机制探讨", "data": {"icon": "doc"}},
            {"at": 3.0, "kind": "point", "text": "不构成任何投资建议，市场有风险"},
            {"at": 5.0, "kind": "highlight", "data": {"index": 0}},
        ],
    })

    # --- 段12 (小蓝 12.97s)：评论区互动 + 下期预告，拆 2 镜 ---
    f12_a = round(seg_frames[12] * 0.55)
    f12_b = seg_frames[12] - f12_a
    shots.append({
        "id": "shot_20",
        "grammar": "y5_kinetic_type",
        "duration": f12_a / FPS,
        "cues": [
            {"at": 0.2, "kind": "point", "text": "聊聊", "sub": "哪一块影响你最大",
             "data": {"label": "互动", "key": "影响"}},
            {"at": 2.6, "kind": "point", "text": "三选一", "sub": "房贷 · 理财 · 物价",
             "data": {"label": "互动", "key": "物价"}},
            {"at": 4.8, "kind": "highlight", "data": {"word": "三选一"}},
        ],
    })
    shots.append({
        "id": "shot_21",
        "grammar": "y5_kinetic_type",
        "duration": f12_b / FPS,
        "cues": [
            {"at": 0.2, "kind": "point", "text": "下期聊", "sub": "点个关注 · 一起聊经济",
             "data": {"label": "预告", "key": "关注"}},
            {"at": 3.0, "kind": "highlight", "data": {"word": "下期聊"}},
        ],
    })

    os.makedirs(ECON_SPECS_DIR, exist_ok=True)
    os.makedirs(ECON_CLIPS_DIR, exist_ok=True)

    tot_frames = sum(round(sh["duration"] * FPS) for sh in shots)
    print(f"生成 {len(shots)} 个镜头 spec，总帧数={tot_frames} ({tot_frames/FPS:.3f}s)")
    assert tot_frames == sum(seg_frames), f"帧数不一致: {tot_frames} != {sum(seg_frames)}"

    _lint_y5(shots)

    spec_files = []
    for sh in shots:
        spec = {
            "grammar": sh["grammar"],
            "duration": sh["duration"],
            "fps": FPS,
            "width": 1920,
            "height": 1080,
            "theme": THEME,
            "safe": SAFE,
            "cues": sh["cues"],
        }
        if "data" in sh:
            spec["data"] = sh["data"]
        sp_path = os.path.join(ECON_SPECS_DIR, f"{sh['id']}.json")
        with open(sp_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        spec_files.append((sh["id"], sp_path, sh["duration"]))
    return spec_files


def render_all(spec_files):
    # ⚠️ Windows 陷阱：子进程按 PATH 找可执行文件时读的是**进程级**环境块（SetEnvironmentVariable），
    # 给 subprocess 传 env= 参数无效 —— 必须改 os.environ 本身。
    # （Git Bash 会把 PATH 前缀转成 "G;G:\..." 这种坏条目，所以不能用 shell 前缀方式，只能在 Python 内改。）
    ffmpeg_dir = os.path.abspath(FFMPEG_BIN)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    os.environ.setdefault("HTTPS_PROXY", "http://127.0.0.1:10808")
    os.environ.setdefault("HTTP_PROXY", "http://127.0.0.1:10808")
    env = os.environ.copy()
    render_py = os.path.join(HUASHU_ENGINE, "render.py")

    clip_paths = []
    for idx, (sid, sp_path, dur) in enumerate(spec_files, 1):
        out_mp4 = os.path.join(ECON_CLIPS_DIR, f"{sid}.mp4")
        clip_paths.append(out_mp4)
        if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 5000:
            print(f"  [{idx}/{len(spec_files)}] 复用已存在 {sid}.mp4 ({dur:.2f}s)", flush=True)
            continue
        print(f"  [{idx}/{len(spec_files)}] 渲染 {sid} ({dur:.2f}s) ...", flush=True)
        cmd = [sys.executable, render_py, "--spec", sp_path, "--out", out_mp4]
        subprocess.run(cmd, cwd=HUASHU_ENGINE, env=env, check=True)

    concat_txt = os.path.join(ECON_CLIPS_DIR, "concat_list.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{cp.replace(chr(92), '/')}'\n")

    subprocess.run([
        FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", concat_txt, "-r", str(FPS), "-c:v", "libx264", "-crf", "16",
        "-pix_fmt", "yuv420p", "-an", FINAL_BG_MP4
    ], check=True)
    print(f"\n✅ huashu 动画底片已生成: {FINAL_BG_MP4}", flush=True)


if __name__ == "__main__":
    specs = build_specs()
    if "--specs-only" not in sys.argv:
        render_all(specs)
