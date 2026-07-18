# Diagnostic: "没有开场白 / No Opening" Complaints

## User's real meaning differs from literal words

| User says | Likely actual problem |
|-----------|----------------------|
| "开场白没有出现" | Audio-visual mismatch — opening card duration ≠ TTS intro duration |
| "没有开场白" | May mean missing text OR missing audio OR timing mismatch |
| "直接就进入新闻播报了" | Card switched before intro finished, OR audio starts with 第1条 |

## Triage order

### 1. Verify `_segments.json` count vs expected
```bash
python3 -c "
import json
with open('output/daily/signal_pop_daily_YYYYMMDD_segments.json') as f:
    segs = json.load(f)
print(f'Actual: {len(segs)}, Expected: {1 + NUM_NEWS} (intro + items)')
print(f'Intro duration: {segs[0]:.1f}s')
"
```
- If `< expected`: TTS silently dropped segments → audio is short
- If `segs[0] < 10`: intro was never generated

### 2. Check actual concat timing
```bash
cat /tmp/concat_v4.txt | head -5
```
First frame duration should ≈ `segs[0]`. If it's 8.0, timing fallback is wrong.

### 3. Check opening card text size
Inspect the opening.png for small text. 26px is invisible on 1920×1080 — minimum 36px.

### 4. Verify WAV actually contains speech
```python
python3 -c "
import wave
with wave.open('output/daily/signal_pop_daily_YYYYMMDD.wav') as w:
    w.setpos(0)
    chunk = w.readframes(w.getframerate())  # first 1s
    non_zero = sum(1 for b in chunk if b != 0)
    print(f'{non_zero}/{len(chunk)} bytes ({non_zero*100/len(chunk):.1f}%)')
"
```
< 10% non-zero = silence, segment failed.