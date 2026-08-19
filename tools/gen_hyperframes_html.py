#!/usr/bin/env python3
"""Generate HyperFrames index.html for daily Signal Pop video — multi-style (v3).

支持多种「布局风格」输出，原经典布局保留为 Style 0（默认、行为不变）。
多个风格按日期 hash 自动轮换，避免每期视频千篇一律；也可手动指定。

Usage:
  python3 gen_hyperframes_html.py YYYYMMDD
  python3 gen_hyperframes_html.py YYYYMMDD --style 2
  python3 gen_hyperframes_html.py YYYYMMDD --out /path/to/index.html
  SIGNAL_POP_HF_STYLE=3 python3 gen_hyperframes_html.py YYYYMMDD

Options:
  --style N   固定使用第 N 种风格（0=经典左栏，1=底部字幕，2=右侧栏，3=居中卡片，4=分屏）
  --out PATH  输出 HTML 路径（默认 /home/kan/signal_pop/hyperframes/index.html）
  --srt PATH  覆盖 SRT 字幕路径
  --script PATH 覆盖新闻脚本路径

风格轮换：未指定 --style 时，按 DATE 的 md5 取模选定风格（与 config.py 的配色轮换同源思路），
保证同一天可复现、不同天自动变化。Style 0 输出与旧版完全一致。
"""
import os
import re
import sys
import hashlib
from datetime import datetime

# ── 默认路径（Linux 部署环境；可用 --srt/--script/--out 覆盖）──
DATE = sys.argv[1] if len(sys.argv) > 1 else "20260629"
SRT_PATH = f"/home/kan/signal_pop/daily/output/signal_pop_daily_{DATE}.srt"
SCRIPT_PATH = f"/home/kan/signal_pop/daily/data/script_{DATE}.txt"
OUT_HTML = "/home/kan/signal_pop/hyperframes/index.html"


# ─────────────────────────────────────────────────────────────────────────────
# 风格注册表
# ─────────────────────────────────────────────────────────────────────────────
# 颜色主题（自包含，与 config.STYLE_THEMES 同源，用于非经典风格的强调色/面板色）
LOCAL_THEMES = [
    {"bar": (30, 85, 130), "accent": (255, 215, 0)},   # 蓝白（accent 金）
    {"bar": (180, 70, 30), "accent": (255, 160, 40)},  # 橙黑
    {"bar": (20, 100, 70), "accent": (0, 210, 150)},   # 墨绿
    {"bar": (80, 40, 120), "accent": (200, 160, 255)}, # 紫金
]
GOLD = "#ffd700"


def rgb_hex(rgb):
    return "#%02x%02x%02x" % rgb


# 每种布局：name + 内容定位 class（overlay 由 CSS 决定）
STYLES = [
    {"id": 0, "name": "classic_left", "pos": "left"},    # 原版：左侧文字遮罩
    {"id": 1, "name": "bottom_banner", "pos": "bottom"}, # 底部字幕条
    {"id": 2, "name": "right_panel", "pos": "right"},    # 右栏
    {"id": 3, "name": "center_card", "pos": "center"},   # 居中卡片
    {"id": 4, "name": "split_screen", "pos": "split"},   # 分屏（左色块+右图）
]


def style_index_for(date_str, explicit):
    """确定本次使用的风格序号。优先级：--style > 环境变量 > 日期 hash 轮换。"""
    n = len(STYLES)
    if explicit is not None:
        try:
            return int(explicit) % n
        except (TypeError, ValueError):
            pass
    env = os.getenv("SIGNAL_POP_HF_STYLE")
    if env and env.strip().lower() not in ("", "auto"):
        try:
            return int(env) % n
        except ValueError:
            pass
    seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
    return seed % n


# ─────────────────────────────────────────────────────────────────────────────
# 数据解析（与旧版保持一致）
# ─────────────────────────────────────────────────────────────────────────────
def parse_srt(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        blocks = re.split(r'\n\n+', f.read().strip())
    for b in blocks:
        lines = b.strip().split('\n')
        if len(lines) < 3:
            continue
        m = re.match(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', lines[1])
        if not m:
            continue
        start = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000
        end = int(m[5]) * 3600 + int(m[6]) * 60 + int(m[7]) + int(m[8]) / 1000
        text = ' '.join(lines[2:]).strip()
        entries.append((start, end, text))
    return entries


def parse_news_items(script_path):
    news_items = []
    cur_num, cur_text = None, []
    auto_idx = 0
    with open(script_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re.match(r'^第(\d+)条[,，\s]+(.*)', line) \
                or re.match(r'^\[([^\]]+)\]\s+(.*)', line) \
                or re.match(r'^(\d+)[\uFE0F\u20E3]*\s+(.*)', line) \
                or re.match(r'^(\d+)[.、]\s*(.*)', line) \
                or (line.startswith('🔟') and (10, line[1:].strip()))
            if m:
                if cur_num is not None:
                    news_items.append((cur_num, ' '.join(cur_text)))
                if isinstance(m, tuple) and len(m) == 2:
                    cur_num, cur_text = m[0], [m[1]]
                else:
                    num = m.group(1)
                    if not num.isdigit():
                        auto_idx += 1
                        cur_num, cur_text = auto_idx, [m.group(2)]
                    else:
                        cur_num, cur_text = int(num), [m.group(2)]
            elif cur_num is not None:
                cur_text.append(line)
    if cur_num is not None:
        news_items.append((cur_num, ' '.join(cur_text)))
    return news_items


def find_news_time_ranges(srt_entries, news_items, total_dur):
    intro_end = None
    outro_start = None
    for i, (st, en, txt) in enumerate(srt_entries):
        if '这里是隔天信号弹' in txt and intro_end is None:
            intro_end = en
        if intro_end is not None and ('今天有10条新闻' in txt or '我是主播' in txt):
            intro_end = max(intro_end, en)
        if '下期见' in txt:
            outro_start = st

    if intro_end is None:
        intro_end = 0.0

    markers = {}
    for st, en, txt in srt_entries:
        m = re.match(r'^第(\d+)条', txt.strip())
        if m:
            markers[int(m.group(1))] = st

    if len(markers) < max(len(news_items) * 7 // 10, 1):
        alloc = (total_dur - intro_end) / max(len(news_items), 1)
        timings = []
        for i in range(len(news_items)):
            n = i + 1
            timings.append((n, intro_end + i * alloc, intro_end + (i + 1) * alloc))
        return timings, intro_end, outro_start

    prev_end = intro_end
    timings = []
    for n in range(1, len(news_items) + 1):
        if n in markers:
            start = markers[n]
        else:
            start = prev_end
        end = total_dur
        for next_n in range(n + 1, len(news_items) + 2):
            if next_n in markers:
                end = markers[next_n]
                break
        # 最后一条新闻不要侵入 outro 区间
        if outro_start is not None and end > outro_start:
            end = outro_start
        if end - start <= 0:
            if end < total_dur:
                end = min(total_dur, end + 1.0)
            elif start > 0:
                start = max(0, start - 1.0)
        timings.append((n, start, end))
        prev_end = end
    return timings, intro_end, outro_start


def esc(s):
    """Escape special chars for JS/HTML text content."""
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ')


# ─────────────────────────────────────────────────────────────────────────────
# 内联内容渲染（每个 clip 的内部 HTML，不含外层 .clip 包裹）
# ─────────────────────────────────────────────────────────────────────────────
def render_intro(style_idx, date_display, total, accent_hex, bar_hex):
    if style_idx == 0:
        grad = "linear-gradient(135deg, #0f0f23, #1a1a3e)"
        a = GOLD
    else:
        grad = f"linear-gradient(135deg, {bar_hex}, #0b0b18)"
        a = accent_hex
    return f'''
<div class="slide center" style="background:{grad};">
<img class="bg-img" src="assets/images/anchor_bg.jpg" alt="">
<div class="overlay-full"></div>
<div class="center-content">
<div class="hero-icon">📡</div>
<h1 class="hero-title">隔天信号弹</h1>
<p class="hero-sub" style="color:{a};">每周定期新闻播报</p>
<p class="hero-date">{date_display} · {total}条新闻</p>
</div>
</div>'''


def render_outro(style_idx, date_display, accent_hex, bar_hex):
    if style_idx == 0:
        grad = "linear-gradient(135deg, #0f0f23, #1a1a3e)"
        a = GOLD
    else:
        grad = f"linear-gradient(135deg, {bar_hex}, #0b0b18)"
        a = accent_hex
    return f'''
<div class="slide center" style="background:{grad};">
<img class="bg-img" src="assets/images/anchor_bg.jpg" alt="">
<div class="overlay-full"></div>
<div class="center-content">
<div class="hero-icon" style="font-size:60px;">📡</div>
<h2 class="outro-title">隔天信号弹</h2>
<p class="outro-sub">每周定期新闻播报 · {date_display}</p>
<p class="outro-end" style="color:{a};">下期再见！</p>
</div>
</div>'''


def _news_common(n, cat, icon, title_main, detail, fs, color, total, date_display):
    """生成 tag-row + title + detail 片段，detail 可为空。"""
    detail_html = f'<p class="news-detail">{esc(detail)}</p>\n' if detail else ""
    tag = (f'<div class="tag-row"><span class="tag-icon">{icon}</span>'
           f'<span class="tag-label" style="color:{color};">{cat}</span>'
           f'<span class="tag-num">#{n:02d}</span></div>')
    title = f'<h2 class="news-title" style="font-size:{fs}px;">{esc(title_main)}</h2>'
    return tag, title, detail_html


def render_news(style_idx, n, cat, icon, title_main, detail, fs, color, total, date_display, accent_hex, bar_hex):
    pos = STYLES[style_idx]["pos"]
    tag, title, detail_html = _news_common(n, cat, icon, title_main, detail, fs, color, total, date_display)

    if pos == "left":
        # 原版：左栏遮罩
        return f'''
<div class="slide">
<img class="bg-img" src="assets/images/{n:02d}.jpg" alt="">
<div class="overlay-left"></div>
<div class="content">
{tag}
{title}
{detail_html}</div>
<div class="footer">
<span class="footer-brand">隔天信号弹 · {date_display}</span>
<span class="tag-num" style="text-align:right;width:auto;">{n}/{total}</span>
</div></div>'''

    if pos == "bottom":
        # 底部字幕条：文字贴底
        return f'''
<div class="slide">
<img class="bg-img" src="assets/images/{n:02d}.jpg" alt="">
<div class="overlay-bottom"></div>
<div class="content pos-bottom">
{tag}
{title}
{detail_html}</div>
<div class="footer">
<span class="footer-brand">隔天信号弹 · {date_display}</span>
<span class="tag-num" style="text-align:right;width:auto;">{n}/{total}</span>
</div></div>'''

    if pos == "right":
        # 右栏：镜像布局，文字右对齐
        return f'''
<div class="slide">
<img class="bg-img" src="assets/images/{n:02d}.jpg" alt="">
<div class="overlay-right"></div>
<div class="content pos-right">
{tag}
{title}
{detail_html}</div>
<div class="footer">
<span class="footer-brand">隔天信号弹 · {date_display}</span>
<span class="tag-num" style="text-align:right;width:auto;">{n}/{total}</span>
</div></div>'''

    if pos == "center":
        # 居中卡片：暗化 + 半透明卡片（直接构造正确 style，避免重复属性）
        detail_html_c = (f'<p class="news-detail" style="text-align:center;max-width:1100px;'
                         f'margin:0 auto;">{esc(detail)}</p>\n') if detail else ""
        tag_c = (f'<div class="tag-row" style="justify-content:center;">'
                 f'<span class="tag-icon">{icon}</span>'
                 f'<span class="tag-label" style="color:{color};">{cat}</span>'
                 f'<span class="tag-num">#{n:02d}</span></div>')
        title_c = (f'<h2 class="news-title" style="font-size:{fs}px;text-align:center;'
                   f'max-width:1100px;margin:0 auto 16px;">{esc(title_main)}</h2>')
        return f'''
<div class="slide center">
<img class="bg-img" src="assets/images/{n:02d}.jpg" alt="">
<div class="overlay-card"></div>
<div class="center-content">
<div class="card">
{tag_c}
{title_c}
{detail_html_c}<div class="footer" style="justify-content:center; margin-left:0; margin-top:24px;">
<span class="footer-brand">{date_display}</span>
<span class="tag-num" style="text-align:center;width:auto;">{n}/{total}</span>
</div>
</div>
</div></div>'''

    if pos == "split":
        # 分屏：左侧色块（巨号+类别），右侧图+文字
        return f'''
<div class="slide">
<img class="bg-img" src="assets/images/{n:02d}.jpg" alt="">
<div class="split-panel" style="background:linear-gradient(160deg, {bar_hex}, #0b0b18);">
<div class="split-num" style="color:{accent_hex};">{n}</div>
<div class="split-rule" style="background:{accent_hex};"></div>
<div class="split-cat">{cat}</div>
<div class="split-foot">隔天信号弹 · {date_display}</div>
</div>
<div class="overlay-right"></div>
<div class="content pos-split">
{tag}
{title}
{detail_html}</div>
<div class="footer">
<span class="footer-brand">隔天信号弹 · {date_display}</span>
<span class="tag-num" style="text-align:right;width:auto;">{n}/{total}</span>
</div></div>'''

    # 兜底
    return render_news(0, n, cat, icon, title_main, detail, fs, color, total, date_display, accent_hex, bar_hex)


def clip(start, dur, track, inner):
    return (f'<div class="clip" data-start="{start:.3f}" data-duration="{dur:.3f}" '
            f'data-track-index="{track}">{inner}</div>')


# ─────────────────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────────────────
def build_timeline_js(style_idx):
    """生成与风格匹配的 GSAP 时间轴脚本。
    Style 0 保持原始行为（clip 整体淡入淡出）；其余风格各自采用不同的入场/退场动效，
    让不同风格在「动起来」的观感上真有区别，而不只是布局/配色不同。
    返回普通 JS 字符串（单花括号），直接拼接进 HTML。
    """
    if style_idx == 0:
        # 原始：clip 整体淡入淡出，行为不变
        return (
            "window.__timelines = window.__timelines || {};\n"
            "const tl = gsap.timeline({ paused: true });\n"
            "document.querySelectorAll('.clip').forEach((el) => {\n"
            "  const st = parseFloat(el.dataset.start);\n"
            "  const dur = parseFloat(el.dataset.duration);\n"
            "  tl.to(el, { opacity: 1, duration: 0.4, ease: 'power2.out' }, st)\n"
            "    .to(el, { opacity: 0, duration: 0.4, ease: 'power2.in' }, st + dur - 0.4);\n"
            "});\n"
            "window.__timelines['signal-pop-daily'] = tl;\n"
            "window.dispatchEvent(new Event('__hf_ready'));\n"
        )
    if style_idx == 1:
        # 底部字幕条：内容从下方滑入/滑出
        body = (
            "  tl.set(el, { opacity: 1 }, st);\n"
            "  const c = el.querySelector('.content');\n"
            "  if (c) {\n"
            "    tl.fromTo(c, { y: 70, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: 'power3.out' }, st);\n"
            "    tl.to(c, { y: -30, opacity: 0, duration: 0.4, ease: 'power2.in' }, st + dur - 0.4);\n"
            "  } else {\n"
            "    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.4 }, st);\n"
            "    tl.to(el, { opacity: 0, duration: 0.4 }, st + dur - 0.4);\n"
            "  }\n"
        )
    elif style_idx == 2:
        # 右栏：内容从右侧滑入/滑出
        body = (
            "  tl.set(el, { opacity: 1 }, st);\n"
            "  const c = el.querySelector('.content');\n"
            "  if (c) {\n"
            "    tl.fromTo(c, { x: 70, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5, ease: 'power3.out' }, st);\n"
            "    tl.to(c, { x: 40, opacity: 0, duration: 0.4, ease: 'power2.in' }, st + dur - 0.4);\n"
            "  } else {\n"
            "    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.4 }, st);\n"
            "    tl.to(el, { opacity: 0, duration: 0.4 }, st + dur - 0.4);\n"
            "  }\n"
        )
    elif style_idx == 3:
        # 居中卡片：卡片缩放+去模糊入场，缩放回退+模糊出场
        body = (
            "  tl.set(el, { opacity: 1 }, st);\n"
            "  const card = el.querySelector('.card');\n"
            "  if (card) {\n"
            "    tl.fromTo(card, { scale: 0.92, opacity: 0, filter: 'blur(8px)' }, { scale: 1, opacity: 1, filter: 'blur(0px)', duration: 0.6, ease: 'power3.out' }, st);\n"
            "    tl.to(card, { scale: 0.96, opacity: 0, filter: 'blur(4px)', duration: 0.4, ease: 'power2.in' }, st + dur - 0.4);\n"
            "  } else {\n"
            "    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.4 }, st);\n"
            "    tl.to(el, { opacity: 0, duration: 0.4 }, st + dur - 0.4);\n"
            "  }\n"
        )
    elif style_idx == 4:
        # 分屏：左侧色块滑入 + 巨号计数 + 右侧内容滑入 + 背景缓慢推近
        body = (
            "  tl.set(el, { opacity: 1 }, st);\n"
            "  const panel = el.querySelector('.split-panel');\n"
            "  const numEl = el.querySelector('.split-num');\n"
            "  const c = el.querySelector('.content');\n"
            "  const bg = el.querySelector('.bg-img');\n"
            "  if (panel) {\n"
            "    tl.fromTo(panel, { x: -70, opacity: 0 }, { x: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }, st);\n"
            "    if (numEl) {\n"
            "      const tgt = parseInt(numEl.textContent, 10) || 0;\n"
            "      const o = { v: 0 };\n"
            "      numEl.textContent = '0';\n"
            "      tl.to(o, { v: tgt, duration: 0.6, ease: 'power2.out', onUpdate: function () { numEl.textContent = Math.round(o.v); } }, st + 0.1);\n"
            "    }\n"
            "    if (c) { tl.fromTo(c, { x: 40, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5, ease: 'power3.out' }, st + 0.1); }\n"
            "    if (bg) { tl.fromTo(bg, { scale: 1.12 }, { scale: 1, duration: dur, ease: 'none' }, st); }\n"
            "    tl.to(panel, { opacity: 0, duration: 0.3 }, st + dur - 0.3);\n"
            "    if (c) { tl.to(c, { opacity: 0, x: 30, duration: 0.3 }, st + dur - 0.3); }\n"
            "  } else {\n"
            "    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.4 }, st);\n"
            "    tl.to(el, { opacity: 0, duration: 0.4 }, st + dur - 0.4);\n"
            "  }\n"
        )
    else:
        body = (
            "  tl.to(el, { opacity: 1, duration: 0.4, ease: 'power2.out' }, st)\n"
            "    .to(el, { opacity: 0, duration: 0.4, ease: 'power2.in' }, st + dur - 0.4);\n"
        )
    header = (
        "window.__timelines = window.__timelines || {};\n"
        "const tl = gsap.timeline({ paused: true });\n"
        "document.querySelectorAll('.clip').forEach((el) => {\n"
        "  const st = parseFloat(el.dataset.start);\n"
        "  const dur = parseFloat(el.dataset.duration);\n"
    )
    footer = (
        "  tl.set(el, { opacity: 0 }, st + dur);\n"
        "});\n"
        "window.__timelines['signal-pop-daily'] = tl;\n"
        "window.dispatchEvent(new Event('__hf_ready'));\n"
    )
    return header + body + footer


def main():
    # 解析参数
    args = sys.argv[1:]
    explicit_style = None
    out_html = OUT_HTML
    srt_path = SRT_PATH
    script_path = SCRIPT_PATH
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--style" and i + 1 < len(args):
            explicit_style = args[i + 1]
            i += 2
            continue
        if a == "--out" and i + 1 < len(args):
            out_html = args[i + 1]
            i += 2
            continue
        if a == "--srt" and i + 1 < len(args):
            srt_path = args[i + 1]
            i += 2
            continue
        if a == "--script" and i + 1 < len(args):
            script_path = args[i + 1]
            i += 2
            continue
        if a in ("-h", "--help"):
            print(__doc__)
            return
        if not a.startswith("--"):
            global DATE
            DATE = a
        i += 1

    # 确定风格
    style_idx = style_index_for(DATE, explicit_style)
    style = STYLES[style_idx]
    if style_idx == 0:
        accent_hex, bar_hex = GOLD, "#1a1a3e"
    else:
        theme = LOCAL_THEMES[style_idx % len(LOCAL_THEMES)]
        accent_hex, bar_hex = rgb_hex(theme["accent"]), rgb_hex(theme["bar"])

    print(f"[Style] #{style_idx} — {style['name']}  (accent={accent_hex}, bar={bar_hex})")

    # 解析数据
    srt_entries = parse_srt(srt_path)
    total_dur = srt_entries[-1][1] if srt_entries else 0
    news_items = parse_news_items(script_path)
    news_timings, intro_end, outro_start = find_news_time_ranges(srt_entries, news_items, total_dur)

    intro_duration = intro_end if intro_end else 0.0
    if outro_start is None:
        outro_start = total_dur - 5
    outro_dur = total_dur - outro_start if outro_start else 5

    date_display = f"{DATE[:4]}.{DATE[4:6]}.{DATE[6:]}"
    category_map = {
        1: ("科技财经", "📡"), 2: ("科技财经", "📡"), 3: ("社会", "📋"),
        4: ("国际", "🌍"), 5: ("科技", "💻"), 6: ("游戏", "🎮"),
        7: ("社会", "📋"), 8: ("体育", "⚽"), 9: ("体育", "⚽"), 10: ("财经", "📊"),
    }
    colors = {1: "#3b82f6", 2: "#3b82f6", 3: "#f59e0b", 4: "#10b981", 5: "#8b5cf6",
              6: "#ef4444", 7: "#f59e0b", 8: "#2ecc71", 9: "#2ecc71", 10: "#3b82f6"}

    # ── 组装 HTML ──
    parts = []
    parts.append('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1920, height=1080">
<script src="assets/gsap.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { width:1920px; height:1080px; overflow:hidden; background:#000; font-family:system-ui,sans-serif; }
.clip { position:absolute; top:0; left:0; width:1920px; height:1080px; opacity:0; will-change:opacity; }
.slide { width:100%; height:100%; padding:60px 80px; display:flex; flex-direction:column; position:relative; }
.slide.center { align-items:center; justify-content:center; text-align:center; }
.bg-img { position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; z-index:0; }
.overlay-full { position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.55); z-index:1; }
.overlay-left { position:absolute; top:0; left:0; width:100%; height:100%;
  background:linear-gradient(to right, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.55) 40%, rgba(0,0,0,0.15) 70%, transparent 100%);
  z-index:1; }
.overlay-bottom { position:absolute; top:0; left:0; width:100%; height:100%;
  background:linear-gradient(to top, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.7) 30%, rgba(0,0,0,0.25) 60%, transparent 100%);
  z-index:1; }
.overlay-right { position:absolute; top:0; left:0; width:100%; height:100%;
  background:linear-gradient(to left, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.55) 40%, rgba(0,0,0,0.15) 70%, transparent 100%);
  z-index:1; }
.overlay-card { position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.45); z-index:1; }
.center-content { position:relative; z-index:2; display:flex; flex-direction:column; align-items:center; }
.content { flex:1; display:flex; flex-direction:column; justify-content:center; margin-left:40px; z-index:2; position:relative; }
.content.pos-bottom { justify-content:flex-end; margin-left:0; margin-right:40px; padding-bottom:90px; }
.content.pos-right { align-items:flex-end; text-align:right; margin-left:0; margin-right:50px; }
.content.pos-right .tag-row { flex-direction:row-reverse; }
.content.pos-right .footer { flex-direction:row-reverse; }
.content.pos-split { width:58%; margin-left:auto; align-items:flex-start; padding-right:30px; }
.card { background:rgba(10,12,24,0.72); border:2px solid rgba(255,255,255,0.15); border-radius:24px;
  padding:50px 64px; max-width:1400px; box-shadow:0 20px 60px rgba(0,0,0,0.5); }
.split-panel { position:absolute; top:0; left:0; width:40%; height:100%; z-index:1;
  display:flex; flex-direction:column; justify-content:center; align-items:flex-start; padding:70px; }
.split-num { font-size:200px; font-weight:800; line-height:1; text-shadow:0 6px 30px rgba(0,0,0,0.6); }
.split-rule { width:120px; height:6px; border-radius:3px; margin:24px 0; }
.split-cat { font-size:34px; color:#fff; letter-spacing:4px; }
.split-foot { font-size:20px; color:rgba(255,255,255,0.6); margin-top:auto; }
.tag-row { display:flex; align-items:center; margin-bottom:16px; gap:12px; }
.tag-icon { font-size:40px; }
.tag-label { font-size:22px; background:rgba(255,255,255,0.08); padding:4px 16px; border-radius:16px; }
.tag-num { font-size:18px; color:rgba(255,255,255,0.35); }
.news-title { font-size:42px; color:#f0f6fc; font-weight:700; line-height:1.4; margin-bottom:16px; max-width:1500px; text-shadow:0 2px 15px rgba(0,0,0,0.8); }
.news-detail { font-size:26px; color:rgba(255,255,255,0.85); line-height:1.6; max-width:1500px; text-shadow:0 1px 8px rgba(0,0,0,0.7); }
.footer { display:flex; justify-content:space-between; align-items:center; margin-top:10px; margin-left:40px; z-index:2; position:relative; }
.footer-brand { font-size:16px; color:rgba(255,255,255,0.25); }
.hero-icon { font-size:80px; margin-bottom:15px; text-shadow:0 0 40px rgba(255,215,0,0.3); }
.hero-title { font-size:72px; color:#fff; text-shadow:0 4px 30px rgba(0,0,0,0.7); font-weight:bold; letter-spacing:6px; }
.hero-sub { font-size:32px; margin:12px 0; text-shadow:0 2px 20px rgba(0,0,0,0.5); }
.hero-date { font-size:26px; color:rgba(255,255,255,0.6); }
.outro-title { font-size:44px; color:#fff; text-shadow:0 2px 20px rgba(0,0,0,0.5); }
.outro-sub { font-size:28px; color:rgba(255,255,255,0.6); margin:12px 0; }
.outro-end { font-size:48px; margin:25px 0; text-shadow:0 2px 20px rgba(0,0,0,0.5); font-weight:bold; }
</style>
</head>
<body>
<div data-composition-id="signal-pop-daily" data-start="0" data-width="1920" data-height="1080" data-duration="''' + f"{total_dur:.3f}" + '''">

<!-- INTRO -->
''' + clip(0, intro_duration, 0, render_intro(style_idx, date_display, len(news_timings), accent_hex, bar_hex)) + '''

<!-- NEWS -->
''')

    track = 1
    for n, start_t, end_t in news_timings:
        dur = end_t - start_t
        if dur <= 0:
            print(f"  W News #{n}: duration {dur:.1f}s <= 0, skip")
            continue
        cat, icon = category_map.get(n, ("新闻", "📰"))
        item_text = None
        for tn, tt in news_items:
            if tn == n:
                item_text = tt
                break
        text = item_text or f"新闻 #{n}"
        m = re.search(r'[。？?!]', text)
        if m and m.end() < len(text) - 10:
            title_main = text[:m.end()]
            detail = text[m.end():]
        else:
            m2 = re.search(r'[丨｜]', text)
            if m2:
                title_main = text[:m2.end()]
                detail = text[m2.end():]
            else:
                title_main = text[:60]
                detail = text[60:] if len(text) > 60 else ""
        fs = "38" if len(title_main) > 55 else "42"
        color = colors.get(n, "#3b82f6")
        parts.append(clip(start_t, dur, track,
                          render_news(style_idx, n, cat, icon, title_main, detail, fs, color,
                                      len(news_timings), date_display, accent_hex, bar_hex)))
        track += 1

    parts.append('''

<!-- OUTRO -->
''' + clip(outro_start, outro_dur, track,
          render_outro(style_idx, date_display, accent_hex, bar_hex)) + '''

<!-- NARRATION AUDIO (full TTS track) -->
<audio id="narration-audio" data-start="0" data-duration="''' + f"{total_dur:.3f}" + '''" data-track-index="99"
       src="./assets/audio/narration.mp3"></audio>

</div>

<script>
''' + build_timeline_js(style_idx) + '''
</script>
</body>
</html>
''')

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(''.join(parts))
    print(f"Written: {out_html}  (style={style['name']})")
    print(f"Total duration: {total_dur:.1f}s")
    print(f"Intro: 0-{intro_duration:.1f}s")
    for n, st, et in news_timings:
        d = et - st
        text_len = 0
        for tn, tt in news_items:
            if tn == n:
                text_len = len(tt)
                break
        print(f"  #{n}: {st:.1f}-{et:.1f}s ({d:.1f}s, {text_len} chars)")
    print(f"Outro: {outro_start:.1f}-{total_dur:.1f}s" if outro_start else f"Outro: ~{total_dur-3:.1f}s")


if __name__ == "__main__":
    main()
