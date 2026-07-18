#!/usr/bin/env python3
"""Generate HyperFrames index.html for daily Signal Pop video - v2"""
import os, re, sys
from datetime import datetime

DATE = sys.argv[1] if len(sys.argv) > 1 else "20260629"
SRT_PATH = f"/home/kan/signal_pop/daily/output/signal_pop_daily_{DATE}.srt"
SCRIPT_PATH = f"/home/kan/signal_pop/daily/data/script_{DATE}.txt"
OUT_HTML = "/home/kan/signal_pop/hyperframes/index.html"

def parse_srt(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        blocks = re.split(r'\n\n+', f.read().strip())
    for b in blocks:
        lines = b.strip().split('\n')
        if len(lines) < 3: continue
        m = re.match(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', lines[1])
        if not m: continue
        start = int(m[1])*3600 + int(m[2])*60 + int(m[3]) + int(m[4])/1000
        end = int(m[5])*3600 + int(m[6])*60 + int(m[7]) + int(m[8])/1000
        text = ' '.join(lines[2:]).strip()
        entries.append((start, end, text))
    return entries

srt_entries = parse_srt(SRT_PATH)
total_dur = srt_entries[-1][1] if srt_entries else 0

# Parse news items from script file
news_items = []
cur_num, cur_text = None, []
auto_idx = 0
with open(SCRIPT_PATH, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        # Match: 第X条, [类别] text, emoji patterns, or digit+dot
        m = re.match(r'^第(\d+)条[,，\s]+(.*)', line) \
            or re.match(r'^\[([^\]]+)\]\s+(.*)', line) \
            or re.match(r'^(\d+)[\uFE0F\u20E3]*\s+(.*)', line) \
            or re.match(r'^(\d+)[.、]\s*(.*)', line) \
            or (line.startswith('🔟') and (10, line[1:].strip()))
        if m:
            if cur_num is not None: news_items.append((cur_num, ' '.join(cur_text)))
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
if cur_num is not None: news_items.append((cur_num, ' '.join(cur_text)))

def find_news_time_ranges(srt_entries):
    timings = []
    intro_end = None
    outro_start = None
    for i, (st, en, txt) in enumerate(srt_entries):
        if '这里是隔天信号弹' in txt and intro_end is None:
            intro_end = en
        if intro_end is not None and ('今天有10条新闻' in txt or '我是主播' in txt):
            intro_end = max(intro_end, en)
        if '今天的信号弹' in txt and '下期再见' in txt:
            outro_start = st

    if intro_end is None:
        intro_end = 0.0

    # 找所有 "第N条" 标记在 SRT 中的起始时间
    markers = {}
    for st, en, txt in srt_entries:
        m = re.match(r'^第(\d+)条', txt.strip())
        if m:
            markers[int(m.group(1))] = st

    # 如果标记太少（少于新闻数的70%），等长分配
    # edge-tts 经常吞掉奇数条标记，导致SRT只有偶数条（如10条只有5个标记）
    if len(markers) < max(len(news_items) * 7 // 10, 1):
        alloc = (total_dur - intro_end) / max(len(news_items), 1)
        for i in range(len(news_items)):
            n = i + 1
            timings.append((n, intro_end + i * alloc, intro_end + (i+1) * alloc))
        return timings, intro_end, outro_start

    # 按顺序分配：缺失标记的用上一条结束时间作为开始
    prev_end = intro_end
    for n in range(1, len(news_items) + 1):
        if n in markers:
            start = markers[n]
        else:
            start = prev_end
        # 找下一条标记作为结束
        end = total_dur
        for next_n in range(n + 1, len(news_items) + 2):
            if next_n in markers:
                end = markers[next_n]
                break
        # 确保有正时长：至少1s
        if end - start <= 0:
            if end < total_dur:
                end = min(total_dur, end + 1.0)
            elif start > 0:
                start = max(0, start - 1.0)
        timings.append((n, start, end))
        prev_end = end
    return timings, intro_end, outro_start

news_timings, intro_end, outro_start = find_news_time_ranges(srt_entries)
# intro_duration: only if there's actual intro content detected
intro_duration = intro_end if intro_end else 0.0
if outro_start is None:
    outro_start = total_dur - 5  # last 5 seconds
outro_dur = total_dur - outro_start if outro_start else 5

category_map = {
    1: ("科技财经", "📡"), 2: ("科技财经", "📡"), 3: ("社会", "📋"),
    4: ("国际", "🌍"), 5: ("科技", "💻"), 6: ("游戏", "🎮"),
    7: ("社会", "📋"), 8: ("体育", "⚽"), 9: ("体育", "⚽"), 10: ("财经", "📊"),
}

date_display = f"{DATE[:4]}.{DATE[4:6]}.{DATE[6:]}"

# ── JS 辅助函数 ──
def esc(s):
    """Escape special chars for JS"""
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ')

# ── Build HTML ──
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
.center-content { position:relative; z-index:2; display:flex; flex-direction:column; align-items:center; }
.content { flex:1; display:flex; flex-direction:column; justify-content:center; margin-left:40px; z-index:2; position:relative; }
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
.hero-sub { font-size:32px; color:#ffd700; margin:12px 0; text-shadow:0 2px 20px rgba(0,0,0,0.5); }
.hero-date { font-size:26px; color:rgba(255,255,255,0.6); }
.outro-title { font-size:44px; color:#fff; text-shadow:0 2px 20px rgba(0,0,0,0.5); }
.outro-sub { font-size:28px; color:rgba(255,255,255,0.6); margin:12px 0; }
.outro-end { font-size:48px; color:#ffd700; margin:25px 0; text-shadow:0 2px 20px rgba(0,0,0,0.5); font-weight:bold; }
</style>
</head>
<body>
<div data-composition-id="signal-pop-daily" data-start="0" data-width="1920" data-height="1080" data-duration="''' + f"{total_dur:.3f}" + '''">

<!-- INTRO -->
<div class="clip" data-start="0" data-duration="''' + f"{intro_duration:.2f}" + '''" data-track-index="0">
<div class="slide center" style="background:linear-gradient(135deg, #0f0f23, #1a1a3e);">
<img class="bg-img" src="assets/images/anchor_bg.jpg" alt="">
<div class="overlay-full"></div>
<div class="center-content">
<div class="hero-icon">📡</div>
<h1 class="hero-title">隔天信号弹</h1>
<p class="hero-sub">每日新闻播报</p>
<p class="hero-date">''' + date_display + ''' · 10条新闻</p>
</div>
</div></div>
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
    # 拆分标题：第一个句号/问号前做主标题
    m = re.search(r'[。？?!]', text)
    if m and m.end() < len(text) - 10:
        title_main = text[:m.end()]
        detail = text[m.end():]
    else:
        # 尝试丨前
        m2 = re.search(r'[丨｜]', text)
        if m2:
            title_main = text[:m2.end()]
            detail = text[m2.end():]
        else:
            title_main = text[:60]
            detail = text[60:] if len(text) > 60 else ""

    # 如果标题过长，缩小字号
    fs = "38" if len(title_main) > 55 else "42"

    colors = {1:"#3b82f6",2:"#3b82f6",3:"#f59e0b",4:"#10b981",5:"#8b5cf6",
              6:"#ef4444",7:"#f59e0b",8:"#2ecc71",9:"#2ecc71",10:"#3b82f6"}
    color = colors.get(n, "#3b82f6")

    parts.append(f'''
<!-- NEWS #{n} -->
<div class="clip" data-start="{start_t:.3f}" data-duration="{dur:.3f}" data-track-index="{track}">
<div class="slide">
<img class="bg-img" src="assets/images/{n:02d}.jpg" alt="">
<div class="overlay-left"></div>
<div class="content">
<div class="tag-row">
<span class="tag-icon">{icon}</span>
<span class="tag-label" style="color:{color};">{cat}</span>
<span class="tag-num">#{n:02d}</span>
</div>
<h2 class="news-title" style="font-size:{fs}px;">{esc(title_main)}</h2>
''')
    if detail:
        parts.append(f'<p class="news-detail">{esc(detail)}</p>\n')
    parts.append(f'''</div>
<div class="footer">
<span class="footer-brand">隔天信号弹 · {date_display}</span>
<span class="tag-num" style="text-align:right;width:auto;">{n}/{len(news_timings)}</span>
</div></div></div>
''')
    track += 1

parts.append(f'''
<!-- OUTRO -->
<div class="clip" data-start="{outro_start:.3f}" data-duration="{outro_dur:.3f}" data-track-index="{track}">
<div class="slide center" style="background:linear-gradient(135deg, #0f0f23, #1a1a3e);">
<img class="bg-img" src="assets/images/anchor_bg.jpg" alt="">
<div class="overlay-full"></div>
<div class="center-content">
<div class="hero-icon" style="font-size:60px;">📡</div>
<h2 class="outro-title">隔天信号弹</h2>
<p class="outro-sub">每日新闻播报 · {date_display}</p>
<p class="outro-end">下期再见！</p>
</div>
</div></div>

<!-- NARRATION AUDIO (full TTS track) -->
<audio id="narration-audio" data-start="0" data-duration="{total_dur:.3f}" data-track-index="99"
       src="./assets/audio/narration.mp3"></audio>

</div>

<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
document.querySelectorAll('.clip').forEach((el, i) => {{
  const st = parseFloat(el.dataset.start);
  const dur = parseFloat(el.dataset.duration);
  tl.to(el, {{ opacity: 1, duration: 0.4, ease: 'power2.out' }}, st)
    .to(el, {{ opacity: 0, duration: 0.4, ease: 'power2.in' }}, st + dur - 0.4);
}});
window.__timelines['signal-pop-daily'] = tl;
window.dispatchEvent(new Event('__hf_ready'));
</script>
</body>
</html>
''')

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(''.join(parts))
print(f"Written: {OUT_HTML}")
print(f"Total duration: {total_dur:.1f}s")
print(f"Intro: 0-{intro_duration:.1f}s")
for n, st, et in news_timings:
    d = et - st
    text_len = 0
    for tn, tt in news_items:
        if tn == n: text_len = len(tt); break
    print(f"  #{n}: {st:.1f}-{et:.1f}s ({d:.1f}s, {text_len} chars)")
print(f"Outro: {outro_start:.1f}-{total_dur:.1f}s" if outro_start else f"Outro: ~{total_dur-3:.1f}s")