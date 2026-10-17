#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据 20261016 期「大家一起聊经济」11 段真实 TTS 时长，生成 huashu-art-motion 分镜 spec 并批量渲染拼接。
特点：
1. 全片统一色板 theme="ink"（#121417 深墨底 + #F2B33D 金黄强调 + #5FB3A1 青绿第二强调，零蓝紫渐变）
2. 全片统一安全框 safe={"top": 76, "bottom": 128, "left": 148, "right": 148}，让开左右 96x96 小头像与底部 72px 字幕条
3. 长段落自动拆成 6~9 秒的多镜（y3_whiteboard / t1_3b1b / t3_finance_chart / y5_kinetic_type 交替），杜绝一页 PPT 到底
4. 每镜时长按 30fps 整数帧对齐，总帧数严格匹配 TTS 总时长（144.31s）
"""
import os
import sys
import json
import subprocess

PROJECT_ROOT = "E:/projects/signal_pop"
HUASHU_ENGINE = "E:/projects/_dl/huashu/huashu-art-motion-main/scripts/engine"
FFMPEG_BIN = "E:/projects/signal_pop/bin/ffmpeg-9.0.1-essentials_build/bin"
FFMPEG = os.path.join(FFMPEG_BIN, "ffmpeg.exe")

PREP_DATE = sys.argv[1] if len(sys.argv) > 1 else "20261016"
OUT_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", PREP_DATE)
ECON_AUDIO_JSON = os.path.join(OUT_DIR, "econ_audio", "tts_segments.json")
ECON_SPECS_DIR = os.path.join(OUT_DIR, "econ_huashu", "specs")
ECON_CLIPS_DIR = os.path.join(OUT_DIR, "econ_huashu", "clips")
FINAL_BG_MP4 = os.path.join(OUT_DIR, "econ_huashu", "econ_huashu_bg.mp4")

FPS = 30
SAFE = {"top": 76, "bottom": 128, "left": 148, "right": 148}
THEME = "ink"


def build_specs():
    segs = json.load(open(ECON_AUDIO_JSON, encoding="utf-8"))
    assert len(segs) == 11, f"期望 11 段，实际 {len(segs)} 段"

    # 将每段精确秒数转为整数帧（保证累计帧数与累计时间严丝合缝）
    cum_t = 0.0
    seg_frames = []
    prev_f = 0
    for s in segs:
        cum_t += s["dur"]
        cur_f = round(cum_t * FPS)
        seg_frames.append(cur_f - prev_f)
        prev_f = cur_f

    durs = [f / FPS for f in seg_frames]
    print("11 段帧对齐时长(s):", [round(d, 3) for d in durs], "总计:", round(sum(durs), 3))

    shots = []

    # --- 段0 (小蓝 14.20s)：开场点题，拆为 2 镜 ---
    d0_a = round(seg_frames[0] * 0.52) / FPS
    d0_b = (seg_frames[0] - round(seg_frames[0] * 0.52)) / FPS
    shots.append({
        "id": "shot_01",
        "grammar": "y5_kinetic_type",
        "duration": d0_a,
        "cues": [
            {"at": 0.2, "kind": "point", "text": "聊经济", "sub": "宏观指标串成一条线", "data": {"label": "大家一起聊经济", "key": "一条线"}},
            {"at": 2.2, "kind": "point", "text": "CPI · PPI", "sub": "物价与产业链传导", "data": {"label": "实体经济端", "key": "物价"}},
            {"at": 4.2, "kind": "point", "text": "收益率 · 汇率", "sub": "无风险基准与资金流向", "data": {"label": "金融资产端", "key": "基准"}},
            {"at": 5.8, "kind": "highlight", "data": {"word": "一条线"}}
        ]
    })
    shots.append({
        "id": "shot_02",
        "grammar": "y3_whiteboard",
        "duration": d0_b,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "七大指标一张网"},
            {"at": 1.1, "kind": "draw", "text": "实体端：PPI / CPI", "data": {"icon": "gear"}},
            {"at": 2.6, "kind": "draw", "text": "央行：利率与流动性", "data": {"icon": "network"}},
            {"at": 4.1, "kind": "draw", "text": "资产端：债市 / 楼市 / 股市", "data": {"icon": "chart"}},
            {"at": 5.5, "kind": "highlight", "data": {"target": "draw", "index": 1}}
        ]
    })

    # --- 段1 (阿信 28.57s)：实体端传导 + 央行调控 + 流动性陷阱，拆为 3 镜 ---
    f1_a = round(seg_frames[1] * 0.34)
    f1_b = round(seg_frames[1] * 0.34)
    f1_c = seg_frames[1] - f1_a - f1_b
    shots.append({
        "id": "shot_03",
        "grammar": "y3_whiteboard",
        "duration": f1_a / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "主线：实体端 ↔ 央行 ↔ 金融端"},
            {"at": 1.4, "kind": "point", "text": "实体经济端：生产与消费交易"},
            {"at": 3.4, "kind": "draw", "text": "央行利率连接两端", "data": {"icon": "network"}},
            {"at": 5.5, "kind": "point", "text": "金融资产端：股、债、房定价"},
            {"at": 7.6, "kind": "highlight", "data": {"index": 0}}
        ]
    })
    shots.append({
        "id": "shot_04",
        "grammar": "t1_3b1b",
        "duration": f1_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "价格传导：从工厂到终端"},
            {"at": 1.2, "kind": "equation", "data": {"tokens": [
                {"s": "PPI", "col": "BLUE_C"}, {"s": "→", "gap": 18},
                {"s": "CPI", "col": "YELLOW", "gap": 18}, {"s": "⇒", "gap": 18},
                {"s": "通胀", "col": "RED_C"}
            ]}},
            {"at": 3.4, "kind": "point", "text": "PPI：工业出厂价（上游成本）"},
            {"at": 5.4, "kind": "point", "text": "CPI：居民消费价（终端物价）"},
            {"at": 7.5, "kind": "highlight", "data": {"target": "equation"}}
        ]
    })
    shots.append({
        "id": "shot_05",
        "grammar": "y3_whiteboard",
        "duration": f1_c / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "央行调控与流动性陷阱"},
            {"at": 1.2, "kind": "draw", "text": "通胀高 → 加息降温", "data": {"icon": "target"}},
            {"at": 3.0, "kind": "draw", "text": "通缩压 → 降息放水", "data": {"icon": "bulb"}},
            {"at": 5.0, "kind": "point", "text": "企业家庭不愿借钱 → 资金空转"},
            {"at": 7.2, "kind": "highlight", "data": {"index": 0}}
        ]
    })

    # --- 段2 (小蓝 2.67s)：原来放水也不是万能的 ---
    shots.append({
        "id": "shot_06",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[2] / FPS,
        "cues": [
            {"at": 0.15, "kind": "point", "text": "资金空转", "sub": "放水 ≠ 借贷扩张", "data": {"label": "流动性陷阱", "key": "空转"}},
            {"at": 1.4, "kind": "highlight", "data": {"word": "空转"}}
        ]
    })

    # --- 段3 (阿信 19.03s)：国债收益率 = 无风险基准 + 债价反向 + 利差驱动汇率，拆为 2 镜 ---
    f3_a = round(seg_frames[3] * 0.52)
    f3_b = seg_frames[3] - f3_a
    shots.append({
        "id": "shot_07",
        "grammar": "t1_3b1b",
        "duration": f3_a / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "金融端锚点：国债收益率"},
            {"at": 1.3, "kind": "line", "text": "债券价格 ↓", "data": {"values": [8.5, 7.6, 6.5, 5.2, 4.1, 3.2, 2.5], "color": "BLUE_C"}},
            {"at": 3.6, "kind": "point", "text": "全社会无风险利率基准"},
            {"at": 5.6, "kind": "line", "text": "国债收益率 ↑（反向变动）", "data": {"values": [2.2, 3.0, 3.9, 5.0, 6.2, 7.4, 8.4], "color": "YELLOW"}},
            {"at": 8.0, "kind": "highlight", "data": {"index": 0}}
        ]
    })
    shots.append({
        "id": "shot_08",
        "grammar": "y3_whiteboard",
        "duration": f3_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "收益率抬升的连锁反应"},
            {"at": 1.2, "kind": "point", "text": "全社会资产贴现率同步抬升"},
            {"at": 3.2, "kind": "draw", "text": "两国利差 → 驱动汇率", "data": {"icon": "chart"}},
            {"at": 5.4, "kind": "point", "text": "美债高息 → 资本倾向美元资产"},
            {"at": 7.4, "kind": "highlight", "data": {"target": "draw", "index": 0}}
        ]
    })

    # --- 段4 (小蓝 1.73s)：那楼市和股市呢？ ---
    shots.append({
        "id": "shot_09",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[4] / FPS,
        "cues": [
            {"at": 0.1, "kind": "point", "text": "楼市 · 股市", "sub": "钱往哪里搬？", "data": {"label": "资产价格端", "key": "楼市"}}
        ]
    })

    # --- 段5 (阿信 18.93s)：楼市资金搬进债市 + 股市减法题公式，拆为 2 镜 ---
    f5_a = round(seg_frames[5] * 0.46)
    f5_b = seg_frames[5] - f5_a
    shots.append({
        "id": "shot_10",
        "grammar": "t3_finance_chart",
        "duration": f5_a / FPS,
        "data": {
            "title": "楼市资金沉淀转向国债避险",
            "unit": "10 年期国债收益率对比（%，近期代表水平）",
            "source": "来源：公开市场数据整理（美债高位虹吸 vs 中国国债低位运行）",
            "badge": "宏观机制示意",
            "chart": "bar",
            "decimals": 2,
            "suffix": "%",
            "series": [
                {"label": "美国10Y国债", "value": 4.85},
                {"label": "欧元区基准", "value": 2.65},
                {"label": "中国10Y国债", "value": 1.68}
            ],
            "highlight": {"index": 2, "text": "1.68% 低位", "sub": "楼市退出资金涌入债市"}
        },
        "cues": [
            {"at": 0.2, "kind": "bar", "data": {"index": [0, 1]}},
            {"at": 2.0, "kind": "bar", "data": {"index": 2}},
            {"at": 4.2, "kind": "highlight"}
        ]
    })
    shots.append({
        "id": "shot_11",
        "grammar": "t1_3b1b",
        "duration": f5_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "股票定价是一道「减法题」"},
            {"at": 1.2, "kind": "equation", "data": {"tokens": [
                {"s": "股价", "col": "YELLOW"}, {"s": "∝", "gap": 18},
                {"s": "企业盈利(+)", "col": "GREEN_C", "gap": 14},
                {"s": "÷", "gap": 14},
                {"s": "国债贴现率(−)", "col": "RED_C"}
            ]}},
            {"at": 3.8, "kind": "point", "text": "分子：企业盈利与现金流（加分项）"},
            {"at": 6.0, "kind": "point", "text": "分母：国债收益率/贴现率（减分项）"},
            {"at": 8.2, "kind": "highlight", "data": {"target": "equation"}}
        ]
    })

    # --- 段6 (小蓝 3.07s)：那收益率一涨，股市就一定跌？ ---
    shots.append({
        "id": "shot_12",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[6] / FPS,
        "cues": [
            {"at": 0.15, "kind": "point", "text": "一定跌？", "sub": "收益率 ↑ ⇒ 股市 ↓ ？", "data": {"label": "关键追问", "key": "一定跌"}},
            {"at": 1.6, "kind": "highlight", "data": {"word": "一定跌"}}
        ]
    })

    # --- 段7 (阿信 36.30s)：两种推高力量 + 真衰假衰 + 2005-2007反例，拆为 4 镜 ---
    f7_a = round(seg_frames[7] * 0.28)
    f7_b = round(seg_frames[7] * 0.24)
    f7_c = round(seg_frames[7] * 0.23)
    f7_d = seg_frames[7] - f7_a - f7_b - f7_c
    shots.append({
        "id": "shot_13",
        "grammar": "t1_3b1b",
        "duration": f7_a / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "动力一：经济与盈利真扩张"},
            {"at": 1.2, "kind": "line", "text": "盈利增速 >> 利率升幅", "data": {"values": [2.0, 2.8, 3.9, 5.4, 7.2, 9.5], "color": "YELLOW"}},
            {"at": 3.5, "kind": "point", "text": "经济强 + 利润扩张 → 消化高利率"},
            {"at": 6.0, "kind": "point", "text": "分子跑赢分母，股市照涨"},
            {"at": 8.2, "kind": "highlight", "data": {"index": 1}}
        ]
    })
    shots.append({
        "id": "shot_14",
        "grammar": "y3_whiteboard",
        "duration": f7_b / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "动力二：赤字与发债纯挤压"},
            {"at": 1.2, "kind": "draw", "text": "财政赤字 + 发债过多", "data": {"icon": "stack"}},
            {"at": 3.2, "kind": "point", "text": "未创造新利润，仅抬高用钱门槛"},
            {"at": 5.4, "kind": "draw", "text": "纯成本挤压风险资产", "data": {"icon": "cross"}},
            {"at": 7.0, "kind": "highlight", "data": {"target": "draw", "index": 1}}
        ]
    })
    shots.append({
        "id": "shot_15",
        "grammar": "y3_whiteboard",
        "duration": f7_c / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "下跌也要分清两种性质"},
            {"at": 1.2, "kind": "draw", "text": "业绩不及预期 → 趋势延续", "data": {"icon": "cross"}},
            {"at": 3.4, "kind": "draw", "text": "业绩稳健被错杀 → 多数收复", "data": {"icon": "check"}},
            {"at": 5.8, "kind": "point", "text": "基本面决定长期方向"},
            {"at": 7.0, "kind": "highlight", "data": {"target": "draw", "index": 1}}
        ]
    })
    shots.append({
        "id": "shot_16",
        "grammar": "t3_finance_chart",
        "duration": f7_d / FPS,
        "data": {
            "title": "2005–2007：美债高利率下 A 股走出大牛市",
            "unit": "上证指数年度收盘点位（点，2005–2007）",
            "source": "来源：历史行情数据（流动性 + 真实利润 + 制度改革共振）",
            "badge": "历史实证",
            "chart": "bar",
            "decimals": 0,
            "suffix": "点",
            "series": [
                {"label": "2005年末", "value": 1161},
                {"label": "2006年末", "value": 2675},
                {"label": "2007年末", "value": 5262}
            ],
            "highlight": {"index": 2, "text": "5262 点", "sub": "流动性 × 利润 × 制度共振"}
        },
        "cues": [
            {"at": 0.2, "kind": "bar", "data": {"index": 0}},
            {"at": 1.6, "kind": "bar", "data": {"index": 1}},
            {"at": 3.2, "kind": "bar", "data": {"index": 2}},
            {"at": 5.2, "kind": "highlight"}
        ]
    })

    # --- 段8 (小蓝 4.43s)：懂了，看指标不能只看一个数，得看背后的原因 ---
    shots.append({
        "id": "shot_17",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[8] / FPS,
        "cues": [
            {"at": 0.2, "kind": "point", "text": "看背后原因", "sub": "不止看一个数字", "data": {"label": "核心认知", "key": "原因"}},
            {"at": 2.4, "kind": "highlight", "data": {"word": "原因"}}
        ]
    })

    # --- 段9 (阿信 6.67s)：照例提醒合规句 ---
    shots.append({
        "id": "shot_18",
        "grammar": "y3_whiteboard",
        "duration": seg_frames[9] / FPS,
        "cues": [
            {"at": 0.1, "kind": "title", "text": "理性认知 · 独立判断"},
            {"at": 1.2, "kind": "draw", "text": "纯经济学机制探讨", "data": {"icon": "doc"}},
            {"at": 3.0, "kind": "point", "text": "不构成任何投资建议，市场有风险"},
            {"at": 5.0, "kind": "highlight", "data": {"index": 0}}
        ]
    })

    # --- 段10 (小蓝 8.70s)：评论区互动 + 下周接着拆 ---
    shots.append({
        "id": "shot_19",
        "grammar": "y5_kinetic_type",
        "duration": seg_frames[10] / FPS,
        "cues": [
            {"at": 0.2, "kind": "point", "text": "评论区聊聊", "sub": "哪个指标听得最多却没弄明白？", "data": {"label": "互动话题", "key": "聊聊"}},
            {"at": 3.8, "kind": "point", "text": "下周接着拆", "sub": "点个关注 · 大家一起聊经济", "data": {"label": "周末特别版", "key": "关注"}},
            {"at": 6.4, "kind": "highlight", "data": {"word": "关注"}}
        ]
    })

    os.makedirs(ECON_SPECS_DIR, exist_ok=True)
    os.makedirs(ECON_CLIPS_DIR, exist_ok=True)

    tot_frames = sum(round(sh["duration"] * FPS) for sh in shots)
    print(f"生成 {len(shots)} 个镜头 spec，总帧数={tot_frames} ({tot_frames/FPS:.3f}s)")
    assert tot_frames == sum(seg_frames), f"帧数不一致: {tot_frames} != {sum(seg_frames)}"

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
            "cues": sh["cues"]
        }
        if "data" in sh:
            spec["data"] = sh["data"]
        sp_path = os.path.join(ECON_SPECS_DIR, f"{sh['id']}.json")
        with open(sp_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        spec_files.append((sh["id"], sp_path, sh["duration"]))
    return spec_files


def render_all(spec_files):
    env = os.environ.copy()
    env["PATH"] = FFMPEG_BIN + os.pathsep + env.get("PATH", "")
    env["HTTPS_PROXY"] = "http://127.0.0.1:10808"
    env["HTTP_PROXY"] = "http://127.0.0.1:10808"
    render_py = os.path.join(HUASHU_ENGINE, "render.py")

    clip_paths = []
    for idx, (sid, sp_path, dur) in enumerate(spec_files, 1):
        out_mp4 = os.path.join(ECON_CLIPS_DIR, f"{sid}.mp4")
        clip_paths.append(out_mp4)
        if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 5000:
            print(f"  [{idx}/{len(spec_files)}] 复用已存在 {sid}.mp4 ({dur:.2f}s)", flush=True)
            continue
        print(f"  [{idx}/{len(spec_files)}] 渲染 {sid} ({dur:.2f}s) ...", flush=True)
        cmd = ["uv", "run", "--offline", "--with", "playwright", "python", render_py, "--spec", sp_path, "--out", out_mp4]
        subprocess.run(cmd, cwd=HUASHU_ENGINE, env=env, check=True)

    # 拼接全部镜头为一条完整动画底片
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
