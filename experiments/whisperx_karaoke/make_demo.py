#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · whisperX 逐字高亮字幕测试：生成可交互预览页

读取 align_test.py 产出的 word-level 时间戳 JSON，生成单文件 HTML：
  - 播放真实 TTS 样本音频，字幕随语音逐字点亮（已读 / 当前 / 未读三态）
  - 可切换「整句对照」模式，直观对比现行 PagedDialogue 效果
  - 显示当前字时间戳、对齐分数、覆盖率等测试指标

同时产出 ASS 卡拉OK字幕（给 ffmpeg 烧录 MP4 demo 用）。
"""
import argparse
import base64
import json
import os
import re

PUNCT = "，。！？；：、,.!?;:"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>Signal Pop · whisperX 逐字高亮字幕 测试</title>
<style>
  :root{
    --bg:#080d18; --panel:#111a2c; --line:#243352; --txt:#e8eefc;
    --muted:#8494b4; --gold:#E8B44A; --blue:#5EC8F2; --dim:#5a6784;
  }
  *{box-sizing:border-box}
  body{margin:0;background:radial-gradient(1200px 700px at 50% -10%,#16233d,#080d18 70%);
       color:var(--txt);font-family:"Microsoft YaHei","Noto Sans SC",sans-serif;min-height:100vh}
  .wrap{max-width:1280px;margin:0 auto;padding:28px 24px 40px}
  header{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:18px}
  h1{font-size:22px;margin:0;letter-spacing:1px}
  .tag{font-size:12px;color:var(--gold);border:1px solid #6b5a2a;background:#2a2413;
       padding:3px 10px;border-radius:20px}
  .sub{color:var(--muted);font-size:13px}
  .grid{display:grid;grid-template-columns:1fr 250px;gap:18px}
  @media(max-width:900px){.grid{grid-template-columns:1fr}}
  .stage{background:linear-gradient(160deg,#0d1830,#0a1120 60%,#101c33);
         border:1px solid var(--line);border-radius:16px;position:relative;
         aspect-ratio:16/9;overflow:hidden;box-shadow:0 18px 60px rgba(0,0,0,.5)}
  .stage::before{content:"";position:absolute;inset:0;
    background:radial-gradient(420px 260px at 18% 28%,rgba(94,200,242,.13),transparent 70%),
               radial-gradient(420px 260px at 82% 28%,rgba(232,180,74,.13),transparent 70%)}
  .ghost{position:absolute;top:46%;left:50%;transform:translate(-50%,-50%);
         font-size:min(5vw,64px);font-weight:800;color:rgba(255,255,255,.035);letter-spacing:14px;white-space:nowrap}
  .who{position:absolute;top:24px;left:28px;font-size:14px;color:var(--muted);letter-spacing:2px}
  .who b{color:var(--gold);font-size:17px}
  .clock{position:absolute;top:24px;right:28px;font:14px Consolas,monospace;color:var(--muted)}
  .cap{position:absolute;left:6%;right:6%;bottom:11%;text-align:center;
       background:rgba(10,16,30,.82);border:1px solid rgba(255,255,255,.14);
       border-radius:16px;padding:18px 22px;backdrop-filter:blur(10px)}
  .cap .speaker{font-size:13px;letter-spacing:3px;color:var(--muted);margin-bottom:10px}
  .cap .line{font-size:clamp(22px,3.1vw,44px);font-weight:800;line-height:1.45;letter-spacing:2px;
             text-shadow:0 2px 3px #000;word-break:break-all}
  .cap .next{font-size:15px;color:#6c7c9c;margin-top:10px;min-height:20px}
  .w{display:inline-block;transition:color .09s linear,transform .09s ease-out,text-shadow .09s linear;
     color:var(--dim)}
  .w.done{color:var(--gold)}
  .w.active{color:#fff;transform:scale(1.22);text-shadow:0 0 14px rgba(232,180,74,.95),0 0 34px rgba(232,180,74,.6)}
  .w.punct{color:#7d8aa6}
  .mode-plain .w{color:var(--txt)!important;transform:none!important;text-shadow:0 2px 3px #000!important}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}
  .panel h2{font-size:13px;color:var(--muted);letter-spacing:2px;margin:0 0 12px;font-weight:600}
  .kv{display:flex;justify-content:space-between;gap:8px;font-size:13px;padding:6px 0;border-bottom:1px dashed #22304b}
  .kv:last-child{border-bottom:0}
  .kv span:first-child{color:var(--muted)}
  .kv span:last-child{font-family:Consolas,monospace;color:var(--txt)}
  .controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:16px}
  button{background:#1b2942;color:var(--txt);border:1px solid #33476b;border-radius:9px;
         padding:9px 16px;font-size:13px;cursor:pointer;font-family:inherit}
  button:hover{background:#26395b}
  button.on{background:#7a5c1c;border-color:var(--gold);color:#fff}
  input[type=range]{flex:1;min-width:220px;accent-color:var(--gold)}
  .t{font:13px Consolas,monospace;color:var(--muted);min-width:100px}
  .hint{color:var(--muted);font-size:12px;line-height:1.8;margin-top:14px}
  .legend{display:flex;gap:16px;font-size:12px;color:var(--muted);margin-top:10px}
  .legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>逐字高亮字幕 · 实验室</h1>
    <span class="tag">whisperX word-level alignment</span>
    <span class="sub" id="meta"></span>
  </header>
  <div class="grid">
    <div>
      <div class="stage" id="stage">
        <div class="ghost">SIGNAL POP</div>
        <div class="who">当前播报：<b id="who">—</b></div>
        <div class="clock" id="clock">00:00.000</div>
        <div class="cap">
          <div class="speaker" id="capSpeaker">—</div>
          <div class="line" id="capLine">点击播放开始</div>
          <div class="next" id="capNext"></div>
        </div>
      </div>
      <div class="controls">
        <button id="play">▶ 播放</button>
        <button id="plain">整句对照</button>
        <button id="back">-2s</button>
        <button id="fwd">+2s</button>
        <button class="on" id="speed">1.0×</button>
        <input type="range" id="seek" min="0" max="100" step="0.01" value="0" />
        <span class="t" id="tlab">0.00 / 0.00 s</span>
      </div>
      <div class="legend">
        <span><i style="background:#5a6784"></i>未读</span>
        <span><i style="background:#E8B44A"></i>已读</span>
        <span><i style="background:#fff;box-shadow:0 0 10px #E8B44A"></i>当前字（放大 + 发光）</span>
      </div>
      <div class="hint" id="hint"></div>
    </div>
    <div>
      <div class="panel">
        <h2>当前字</h2>
        <div class="kv"><span>字</span><span id="curW">—</span></div>
        <div class="kv"><span>start</span><span id="curS">—</span></div>
        <div class="kv"><span>end</span><span id="curE">—</span></div>
        <div class="kv"><span>score</span><span id="curScore">—</span></div>
      </div>
      <div class="panel" style="margin-top:14px">
        <h2>测试指标</h2>
        <div id="stats"></div>
      </div>
    </div>
  </div>
</div>
<audio id="audio" src="__AUDIO__" preload="auto"></audio>
<script>
const DATA = __DATA__;
const audio = document.getElementById('audio');
const segs = DATA.segments;
const LINES = [];
const MAXCHARS = 15;
for (const s of segs) {
  let buf = [];
  for (const w of s.words) {
    buf.push(w);
    const last = String(w.w || '');
    if (PUNCT_RE(last) || buf.length >= MAXCHARS) { LINES.push({speaker:s.speaker, words:buf}); buf = []; }
  }
  if (buf.length) LINES.push({speaker:s.speaker, words:buf});
}
function PUNCT_RE(c){ return /[，。！？；：、,.!?;:]/.test(c); }
for (const l of LINES) { l.start = l.words[0].start; l.end = l.words[l.words.length-1].end; }

const $ = id => document.getElementById(id);
const fmt = t => { const m=Math.floor(t/60), s=t-m*60; return String(m).padStart(2,'0')+':'+s.toFixed(3).padStart(6,'0'); };
$('meta').textContent = DATA.meta.date + ' 期 · 样本 ' + DATA.meta.start.toFixed(2) + '–' + DATA.meta.end.toFixed(2) + 's · ' + DATA.meta.model;
$('hint').textContent = '音频来源：output/weekly/' + DATA.meta.date + '/audio/tts.wav（真实主片音轨）。字幕文本为已知 TTS 文稿，whisperX 仅做强制对齐，不经 ASR 猜字。';
const statsHtml = Object.entries(DATA.stats).map(([k,v]) => '<div class="kv"><span>'+k+'</span><span>'+v+'</span></div>').join('');
$('stats').innerHTML = statsHtml;

function lineAt(t){
  let idx = -1;
  for (let i=0;i<LINES.length;i++) if (LINES[i].start <= t + 0.001) idx = i; else break;
  if (idx < 0) return {cur:null,next:LINES[0]||null};
  if (LINES[idx].end + 0.45 < t && LINES[idx+1]) idx++;
  return {cur:LINES[idx], next:LINES[idx+1]||null};
}
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
let lastSpeaker = '', lineIdx = -1;
function paint(t){
  $('clock').textContent = fmt(t);
  $('seek').value = (t / (DATA.meta.end - DATA.meta.start)) * 100;
  $('tlab').textContent = t.toFixed(2) + ' / ' + (DATA.meta.end-DATA.meta.start).toFixed(2) + ' s';
  const {cur,next} = lineAt(t);
  if (!cur) { $('capLine').textContent=''; return; }
  if (cur.speaker !== lastSpeaker) { $('who').textContent = cur.speaker; $('capSpeaker').textContent = cur.speaker + ' · 逐字同步'; lastSpeaker = cur.speaker; }
  const idx = LINES.indexOf(cur);
  if (idx !== lineIdx) {
    $('capLine').innerHTML = cur.words.map(w => '<span class="w">'+esc(w.w)+'</span>').join('');
    lineIdx = idx;
  }
  let active = null;
  const spans = $('capLine').children;
  cur.words.forEach((w,i) => {
    const punct = PUNCT_RE(String(w.w||''));
    let cls = 'w';
    if (t >= w.end) cls += ' done';
    else if (t >= w.start && !punct) { cls += ' active'; active = w; }
    if (punct) cls += ' punct';
    if (spans[i]) spans[i].className = cls;
  });
  $('capNext').textContent = next ? '下句：' + next.words.map(w=>w.w).join('').slice(0,20) + '…' : '';
  $('curW').textContent = active ? active.w : '—';
  $('curS').textContent = active ? active.start.toFixed(3)+'s' : '—';
  $('curE').textContent = active ? active.end.toFixed(3)+'s' : '—';
  $('curScore').textContent = active && active.score!=null ? Number(active.score).toFixed(2) : '—';
}
function loop(){ if(!audio.paused) paint(audio.currentTime); requestAnimationFrame(loop); }
requestAnimationFrame(loop);
audio.addEventListener('timeupdate', () => paint(audio.currentTime));
audio.addEventListener('ended', () => $('play').textContent='▶ 播放');
$('play').onclick = () => { if(audio.paused){ audio.play(); $('play').textContent='❚❚ 暂停'; } else { audio.pause(); $('play').textContent='▶ 播放'; } };
$('plain').onclick = () => { const on = $('stage').classList.toggle('mode-plain'); $('plain').classList.toggle('on',on); $('plain').textContent = on?'逐字高亮':'整句对照'; paint(audio.currentTime); };
$('back').onclick = () => { audio.currentTime = Math.max(0,audio.currentTime-2); paint(audio.currentTime); };
$('fwd').onclick = () => { audio.currentTime = Math.min(audio.duration||999,audio.currentTime+2); paint(audio.currentTime); };
$('speed').onclick = () => { const rates=[1,0.75,1.25]; let i=rates.indexOf(audio.playbackRate); audio.playbackRate=rates[(i+1)%3]; $('speed').textContent=audio.playbackRate.toFixed(2).replace(/0$/,'')+'×'; };
$('seek').oninput = e => { audio.currentTime = (e.target.value/100)*(DATA.meta.end-DATA.meta.start); paint(audio.currentTime); };
paint(0);
</script>
</body>
</html>
"""


def ass_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def build_ass(words_path, ass_path, offset=0.0, max_chars=16):
    r"""ASS 卡拉OK：每个字一个 \k 标签；offset 用于对齐成片 9s 片头。

    长段按字数/标点分页成多条 Dialogue，避免 170 字挤在一行溢出画面。
    """
    with open(words_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Microsoft YaHei,58,&H00FFFFFF,&H00FFD24A,&H00101010,&H80000000,"
        "-1,0,0,0,100,100,0,0,1,3,0,2,80,80,150,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    n_dialogues = 0
    for seg in data["segments"]:
        words = seg["words"]
        if not words:
            continue
        # 分页：优先在标点处断行，最多 max_chars 字
        pages, buf = [], []
        for w in words:
            buf.append(w)
            if str(w["w"]) in PUNCT or len(buf) >= max_chars:
                pages.append(buf)
                buf = []
        if buf:
            pages.append(buf)
        for pi, page in enumerate(pages):
            chunks, prev_end = [], page[0]["start"] + offset
            for w in page:
                gap = max(0.0, w["start"] + offset - prev_end)
                if gap > 0.02:
                    chunks.append(f"{{\\k{int(round(gap * 100))}}}")
                dur = max(1, int(round(max(0.02, w["end"] - w["start"]) * 100)))
                chunks.append(f"{{\\kf{dur}}}{w['w']}")
                prev_end = w["end"] + offset
            text = "".join(chunks)
            next_start = (pages[pi + 1][0]["start"] + offset) if pi + 1 < len(pages) else None
            end = min(page[-1]["end"] + offset + 0.25, seg["end"] + offset + 0.35)
            if next_start is not None:
                end = min(end, next_start - 0.02)
            end = max(end, page[-1]["end"] + offset + 0.01)
            lines.append(
                f"Dialogue: 0,{ass_time(page[0]['start'] + offset)},{ass_time(end)},"
                f"Default,,0,0,0,,{text}"
            )
            n_dialogues += 1
    print(f"[ass ] {n_dialogues} 行卡拉OK字幕 -> {ass_path}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return ass_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", default=None)
    ap.add_argument("--ass-offset", type=float, default=9.0,
                    help="ASS 时间轴偏移（成片 9s 片头），仅烧录用")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    words_path = args.words or os.path.join(here, "words.json")
    with open(words_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    # 音频内嵌，保证 HTML 单文件在任何预览环境都能出声
    wav_path = os.path.join(here, "sample_16k.wav")
    with open(wav_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    html = html.replace("__AUDIO__", "data:audio/wav;base64," + b64)
    out_html = os.path.join(here, "karaoke_demo.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[demo] {out_html}")

    out_ass = os.path.join(here, "karaoke.ass")
    build_ass(words_path, out_ass, offset=args.ass_offset)
    print(f"[ass ] {out_ass} (offset {args.ass_offset}s)")

    raw_ass = os.path.join(here, "karaoke_raw.ass")
    build_ass(words_path, raw_ass, offset=0.0)
    print(f"[ass ] {raw_ass} (样本时间轴，供独立片段烧录)")


if __name__ == "__main__":
    main()
