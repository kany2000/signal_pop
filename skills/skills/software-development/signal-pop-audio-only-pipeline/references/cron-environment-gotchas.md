# Cron Environment & Delivery Gotchas (Signal Pop)

## feedparser Missing in Cron Context

**Symptom**: `ModuleNotFoundError: No module named 'feedparser'` in cron logs, but `pip list` shows feedparser installed.

**Root Cause**: The hermes-agent venv Python (`/home/kan/.hermes/hermes-agent/venv/bin/python3`) has feedparser, but system Python (`/usr/bin/python3` = Python 3.12) does not. When cron runs scripts via subprocess, it may resolve `python3` differently than in an interactive shell.

**Fix**: In `generate_audio_only.sh`, use the full venv python path:
```bash
PYTHON="/home/kan/.hermes/hermes-agent/venv/bin/python3"
```
instead of `python3`.

## Telegram 401 Unauthorized

**Symptom**: `requests.post` to `api.telegram.org/bot<TOKEN>/sendAudio` returns 401.

**Root Cause**: The bot token has expired or been revoked. Or the bot has not been started by the target user / added to the target group.

**Fix**:
1. Verify token is still valid: `curl https://api.telegram.org/bot<TOKEN>/getMe`
2. Start the bot by sending `/start` in the target chat
3. If using a group/channel, add the bot as administrator first
4. Use the home channel chat ID `1921948418` for direct delivery

## Output Path Confusion

The pipeline writes to two different directories depending on how it's invoked:

| Invocation | Output dir | Latest file |
|---|---|---|
| `generate_audio_only.sh daily` | `/home/kan/signal_pop/output/daily/` | `signal_pop_daily_latest.mp3` |
| `generate_audio_only.sh weekly` | `/home/kan/signal_pop/output/weekly/` | `signal_pop_weekly_latest.mp3` |

When delivering via Telegram, always use the `_latest` file, not the timestamped one.

## Male Voice Bug (Fixed 2026-05-16)

**Symptom**: Male voice (yunyang) used on Monday/Wednesday/Friday instead of female (xiaoxiao).

**Root Cause**: `generate_audio_only.sh` line 37 used `WEEKDAY == "6"` as fallback, which triggered whenever `$MODE` wasn't explicitly set to `daily`.

**Fix**: Changed to:
```bash
if [ "$MODE" == "weekly" ]; then
    VOICE_ID="yunyang"
else
    VOICE_ID="xiaoxiao"
fi
```

## China Network Issues

**Symptom**: `urlopen error: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING]` when fetching RSS feeds.

**Root Cause**: Some Chinese news sites (e.g., aitechtalk.com) have broken SSL or block non-browser requests.

**Fix**: The pipeline already falls back gracefully. Check `data/raw_feed.json` to confirm which feeds returned data.

## News Content Must Be Confirmed Facts (2026-07-03)

**User correction**: News headlines should be **confirmed facts**, not ongoing events or open questions. Sports match scores that are still in progress (e.g., "C罗点球破门，葡萄牙1-1克罗地亚" during an ongoing game) should NOT be used as headlines. Wait for the final result before using as news.

**Action**: When manually selecting news (filtered_news.json), verify each item is a **confirmed outcome** — published result, official statement, or completed event. If in doubt, replace with a confirmed alternative.

## Pitfalls

### ffmpeg path

Use venv bundled binary — `/home/kan/.hermes/hermes-agent/venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2`. Do NOT assume `ffmpeg` is in PATH.

### feedparser + timeout

`feedparser.parse()` does not accept a `timeout` kwarg. Use `requests.get()` first, pass `BytesIO(r.content)` to `feedparser.parse()`.

### Reuters RSS URL

The correct Reuters CN feed is `https://feeds.reuters.com/reuters/CNTopStories` — the space-prefixed variant in many docs is broken.

### MiMo role rule

Target text MUST be in `role: assistant`. `role: user` is only for style instructions. Confirmed via live API call 2026-05-12.

### MiMo API key

`sk-c6i...5odm` — stored hardcoded in `src/tts_mimo.py`. Do NOT truncate or mask it when editing the file. If you see a truncated version in the file, the key was accidentally corrupted — restore from memory.

### Nightly failure before 8:30

Logs at `logs/pipeline_daily_*.log` may show a 00:14 failure — that is the previous day's failed run (before the cron was updated). The actual successful run is at ~08:17. Check both timestamps when debugging.

### execute_code + Telegram Bot API — SSL Consideration

**Symptom (sporadic):** `requests.post("https://api.telegram.org/bot{token}/sendAudio")` may raise `ssl.SSLError: [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]`. When this occurs, Python `requests` in the execute_code sandbox uses TLS 1.3 which fails SSL handshake to api.telegram.org.

**✅ Primary approach (verified 2026-06-05):** Use `requests` with proxy — works fine:
```python
proxies = {'http': proxy, 'https': proxy} if proxy else None
resp = requests.post(url, files={'audio': audio}, proxies=proxies, timeout=60)
```

**✅ Fallback:** `subprocess.run(["curl", ..., "--tlsv1.2"])` from `execute_code` when SSL still fails:
```python
cmd = ["curl", "-s", "--tlsv1.2", "-X", "POST",
       f"https://api.telegram.org/bot{token}/sendAudio",
       "-F", f"audio=@{mp3_path}", "-F", "chat_id=1921948418"]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
```
`terminal()` has no SSL issue — `requests` works fine there. See `references/telegram-delivery.md` for both full patterns.

### tts_mimo.py Tuple Unpacking Bug (2026-06-26)

**Symptom**: `AttributeError: 'tuple' object has no attribute 'replace'` when running TTS.

**Root Cause**: `synthesize_long_text()` returns a tuple `(wav_path, segments)` but `__main__` entry point treated it as a single string path.

**Fix** in `src/tts_mimo.py:324-325`:
```python
# Before
wav_path = synthesize_long_text(text, voice_gender=gender, output_path=output)

# After
wav_path, _ = synthesize_long_text(text, voice_gender=gender, output_path=output)
```

### Pipeline Timeout Optimization (2026-06-26)

**Problem**: Original pipeline generated video every run (ffmpeg `libx264 preset=medium`), taking >30 minutes — exceeding cron 180s timeout.

**Solution**:
1. **Daily mode skips video**: `generate_audio_only.sh` now only generates audio + SRT for daily; weekly still produces full video
2. **ffmpeg preset=ultrafast**: Changed from `medium` to `ultrafast` in `generate_video.py`, encoding ~10x faster
3. **Result**: Daily pipeline completes in **1m47s** (including 11-segment TTS), well within cron timeout

**Updated script behavior**:
- `bash scripts/generate_audio_only.sh daily` → audio + SRT only (1m47s)
- `bash scripts/generate_audio_only.sh weekly` → audio + SRT + video (longer, but Saturday run has no timeout pressure)
