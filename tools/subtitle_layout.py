#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · 字幕智能排版（auto line-break）

算法移植自 short-video-factory (YILS-LIN) 的
src/effect-engine/shared/line-break.ts（2026-09-12 评估后外科手术式借鉴，
评估与跳过项见 .workbuddy/memory/2026-09-12.md）。

核心算法 auto_line_break：
    字号从 font_size 逐级递减到 min_font_size，每级贪心填行；
    行数 <= max_lines 即采用；全部超限则用 min_font_size 强制分配到
    max_lines 行（优先塞进放得下的行，兜底塞最后一行）。

分词 split_tokens：
    优先 jieba（若环境已安装）；否则使用与原 JS fallback 一致的
    「CJK/标点逐字兜底」——英文按空格成词、CJK 逐字、标点吸附前词。
    零第三方硬依赖。

量宽 measure：
    默认 Pillow ImageFont.getlength 真实度量（自动探测系统字体）；
    无 Pillow / 无字体时退化为按字符类估宽（CJK≈1.0em，其他≈0.55em）。

用法（库）：
    from subtitle_layout import wrap_text, SRT_WRAP_STYLE
    lines, font_size = wrap_text(text, video_width=1920, style=SRT_WRAP_STYLE)

自检：python tools/subtitle_layout.py --demo
"""
import os
import re
import sys

# CJK：汉字 + 假名 + 谚文（含扩展A/兼容区/注音字母，覆盖常用面）
CJK_RE = re.compile(
    "[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff"
    "\u3040-\u309f\u30a0-\u30ff"
    "\u3130-\u318f\uac00-\ud7af]"
)
# 行首禁则标点：不允许出现在行首（吸附到前一 token）
PUNCT_RE = re.compile("^[,.;!?%:，。！？；：、）】》〉」』]$")
# 粘连符：独立成 token 时吸附前词，且与后词之间不加空格
# （如 under-display、9/19、don't——jieba 会把撇号拆成独立 token）
GLUE = "-/·'"

# 默认样式（对齐 short-video-factory default-style.ts 的 schema）
DEFAULT_SUBTITLE_STYLE = {
    "position": "bottom",
    "offset_x": 0,
    "offset_y": -210,
    "safe_area_bottom_ratio": 0.12,
    "max_width_ratio": 0.86,
    "max_lines": 2,
    "font_family": '"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif',
    "font_size": 56,
    "min_font_size": 34,
    "font_weight": "700",
    "line_height": 1.24,
    "color": "#FFFFFF",
    "stroke_color": "#101010",
    "stroke_width": 4,
}

# 英文外挂 SRT 专用换行样式（1920 宽 ≈ 每行 ~59 字符）
# SRT 由播放器自渲染字号：虚拟字号只用于定宽，max_lines=None 表示
# 不缩字、不限行数——固定宽度纯贪心换行（正常 cue 自然 ≤2 行，
# 超长 cue 每行 ≤ 限宽，绝不再出现整段单行）。
SRT_WRAP_STYLE = {
    "font_size": 48,
    "min_font_size": 48,
    "max_lines": None,
    "max_width_ratio": 0.78,
}

# 字体探测候选（Windows → macOS → Linux）
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def _merge_glue(tokens):
    """把独立标点/粘连符 token 吸附到前词（行首禁则 + under-display 不拆散）。"""
    merged = []
    for tok in tokens:
        first = tok[0] if tok else ""
        if merged and (PUNCT_RE.match(first) or (first in GLUE and len(tok) <= 2)):
            merged[-1] += tok
        else:
            merged.append(tok)
    # 时间 "1:00" 被 jieba 拆成 ["1:","00"]：数字冒号后紧跟数字时回并
    out = []
    i = 0
    while i < len(merged):
        tok = merged[i]
        if re.fullmatch(r"\d{1,2}:", tok) and i + 1 < len(merged) and merged[i + 1].isdigit():
            out.append(tok + merged[i + 1])
            i += 2
        else:
            out.append(tok)
            i += 1
    return out


def split_tokens(text):
    """中英混排分词：优先 jieba，失败/未安装则逐字兜底（与原 JS 一致）。"""
    try:  # 可选增强：环境里有 jieba 就用真分词
        import jieba  # noqa: F401

        toks = [t.strip() for t in jieba.lcut(text) if t.strip()]
        if toks:
            return _merge_glue(toks)
    except Exception:
        pass

    tokens = []
    word = ""
    for ch in text:
        if ch.isspace():
            if word:
                tokens.append(word)
                word = ""
        elif CJK_RE.match(ch) or PUNCT_RE.match(ch):
            if word:
                tokens.append(word)
                word = ""
            if PUNCT_RE.match(ch) and tokens:
                tokens[-1] += ch  # 标点吸附前词
            else:
                tokens.append(ch)
        else:
            word += ch
    if word:
        tokens.append(word)
    return tokens


def join_tokens(tokens):
    """token 回拼成行：标点/CJK 相邻不加空格，其余加空格。"""
    text = ""
    for i, tok in enumerate(tokens):
        if i == 0:
            text = tok
            continue
        prev = text[-1] if text else ""
        first = tok[0]
        if PUNCT_RE.match(first):
            text += tok  # 标点吸附前词
        elif PUNCT_RE.match(prev):
            # 前一字符是标点：后续是 CJK 不加空格（「，库克」），拉丁仍加空格
            text += tok if CJK_RE.match(first) else " " + tok
        elif prev in GLUE or (CJK_RE.match(prev) and CJK_RE.match(first)):
            text += tok  # 粘连符后 / CJK 相邻：不加空格
        else:
            text += " " + tok
    return text


def pillow_measure(font_path=None):
    """用 Pillow 真实字体度量字宽（带字号缓存）。需系统安装 Pillow。"""
    from PIL import ImageFont

    path = font_path
    if not path:
        for cand in _FONT_CANDIDATES:
            if os.path.exists(cand):
                path = cand
                break
    cache = {}

    def measure(text, font_size):
        key = (path, font_size)
        font = cache.get(key)
        if font is None:
            font = (
                ImageFont.truetype(path, font_size)
                if path
                else ImageFont.load_default()
            )
            cache[key] = font
        return font.getlength(text)

    return measure


def estimate_measure():
    """无 Pillow / 无字体时的兜底量宽：按字符类估算。"""
    def measure(text, font_size):
        width = 0.0
        for ch in text:
            if CJK_RE.match(ch):
                width += font_size
            elif ch.isspace():
                width += font_size * 0.3
            else:
                width += font_size * 0.55
        return width

    return measure


def default_measure():
    try:
        return pillow_measure()
    except Exception:
        return estimate_measure()


def _finalize(lines):
    return [t for t in (join_tokens(ln) for ln in lines) if t]


def auto_line_break(text, video_width, style=None, measure=None):
    """智能换行：字号递减 + 贪心填行 + 安全区约束。

    返回 (lines: list[str], font_size: int)。
    """
    style = {**DEFAULT_SUBTITLE_STYLE, **(style or {})}
    tokens = split_tokens(text)
    if not tokens:
        return [], style["font_size"]

    max_width = max(1, int(video_width * style["max_width_ratio"]))
    measure = measure or default_measure()
    min_size = style["min_font_size"]
    max_lines = style["max_lines"]

    # max_lines=None：SRT 等播放器自渲染场景——固定虚拟宽度纯贪心换行，
    # 不缩字不限行数（短文本自然 ≤2 行，超长 cue 每行都 ≤ 限宽）。
    if max_lines is None:
        lines = [[]]
        for tok in tokens:
            candidate = join_tokens(lines[-1] + [tok])
            if not lines[-1] or measure(candidate, style["font_size"]) <= max_width:
                lines[-1].append(tok)
            else:
                lines.append([tok])
        return _finalize(lines), style["font_size"]

    size = style["font_size"]
    while size >= min_size:
        lines = [[]]
        for tok in tokens:
            candidate = join_tokens(lines[-1] + [tok])
            if not lines[-1] or measure(candidate, size) <= max_width:
                lines[-1].append(tok)
            else:
                lines.append([tok])
        if len(lines) <= max_lines:
            return _finalize(lines), size
        size -= 1

    # 最小字号仍超行数：按顺序强制分配到 max_lines 行（最后一行兜底硬塞）。
    # 注：原 JS 用「first line that fits」回填，窄 token 会插回前面的行、
    # 打乱文本顺序（字幕不可接受），此处改为顺序保持式填充。
    lines = [[]]
    for tok in tokens:
        fits = measure(join_tokens(lines[-1] + [tok]), min_size) <= max_width
        if fits or not lines[-1]:
            lines[-1].append(tok)
        elif len(lines) < max_lines:
            lines.append([tok])
        else:
            lines[-1].append(tok)
    return _finalize(lines), min_size


def wrap_text(text, video_width, style=None, measure=None):
    """auto_line_break 的便捷别名。返回 (lines, font_size)。"""
    return auto_line_break(text, video_width, style=style, measure=measure)


def wrap_srt_text(en, max_chars=3000):
    """SRT 字幕文本智能换行（固定虚拟宽度贪心换行、行首禁则）。

    - 输入含换行（如断点复用的多行译文）也安全：\\n 按空白处理，天然 unwrap，幂等。
    - 超长文本（> max_chars）保险起见原样返回——正常 cue 远小于该值，
      仅防「整文件误当一条 cue」之类的极端输入触发 O(n²) 慢路径。
    - 任何异常都退回原文，绝不因排版阻断字幕生成。
    """
    try:
        if not en or len(en) > max_chars:
            return en
        lines, _ = wrap_text(en, video_width=1920, style=SRT_WRAP_STYLE)
        return "\n".join(lines) if lines else en
    except Exception:
        return en


def _demo():
    samples = [
        (
            "英文长句",
            "Apple unveiled the foldable iPhone Duo with an under-display "
            "camera and global eSIM support at its autumn event, signaling "
            "a new era for foldable phones.",
        ),
        (
            "中文长句",
            "本周最值得关注的是苹果秋季发布会，折叠屏iPhone正式登场，"
            "库克称这是iPhone史上最大的一次设计飞跃，售价一万七千九百九十九元起。",
        ),
        (
            "中英混排",
            "据9to5mac报道，iPhone Duo 起售价 1799 美元，将于 9月19日 正式开售。",
        ),
    ]
    for name, text in samples:
        lines, size = wrap_text(text, video_width=1920, style=SRT_WRAP_STYLE)
        print(f"\n[{name}] font_size={size} lines={len(lines)}")
        for ln in lines:
            print(f"  | {ln}")
        # 校验：换行不丢 token（回拼 token 流与原文一致）
        orig = split_tokens(text)
        rewrapped = split_tokens(" ".join(lines))
        if orig == rewrapped:
            print("  token 校验: OK")
        else:
            print("  token 校验: WARN: token 流不一致")
            for j, (a, b) in enumerate(zip(orig, rewrapped)):
                if a != b:
                    print(f"    首个差异 @ {j}: {a!r} vs {b!r}")
                    break
            print(f"    len: {len(orig)} vs {len(rewrapped)}")


if __name__ == "__main__":
    _demo()
