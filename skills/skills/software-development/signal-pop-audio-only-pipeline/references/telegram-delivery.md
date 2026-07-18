# Telegram Delivery for Signal Pop

## Bot Configuration

| Setting | Value |
|---------|-------|
| Bot Token | `8708781676:AAFc-Jaap...` (stored in `~/.hermes/.env` as `TELEGRAM_BOT_TOKEN`) |
| Bot Username | `xiaotu2026_bot` |
| Home Channel | `1921948418` (direct message) |
| Group | `-1003790311439` (虾之屋 group, thread 285) |

## Pre-requisites for Bot to Send Messages

1. User must send `/start` to the bot first (authorizes the bot to send messages)
2. For groups: bot must be added to the group AND the group must allow bot messaging
3. User ID must be in `TELEGRAM_ALLOWED_USERS` in `.env`

## Testing Bot Connectivity

```bash
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | cut -d= -f2-)
curl -s --tlsv1.2 "https://api.telegram.org/bot${BOT_TOKEN}/getMe"
```

## sendAudio + sendMessage — Verified Patterns

### Method A: Python `requests` from `execute_code` (simpler, verified 2026-06-05)

When the proxy is configured, `requests` in `execute_code` works fine with the Telegram Bot API — no SSL error:

```python
import os, requests

# Read .env
with open("/home/kan/.hermes/.env") as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

bot_token = os.environ['TELEGRAM_BOT_TOKEN']
chat_id = os.environ.get('TELEGRAM_HOME_CHANNEL', '1921948418')
proxy = os.environ.get('TELEGRAM_PROXY', 'http://10.10.10.150:7890')
proxies = {'http': proxy, 'https': proxy} if proxy else None

mp3_path = '/home/kan/signal_pop/output/daily/signal_pop_daily_latest.mp3'
script_path = '/home/kan/signal_pop/output/daily/signal_pop_daily_latest.txt'

# === sendAudio ===
url = f'https://api.telegram.org/bot{bot_token}/sendAudio'
with open(mp3_path, 'rb') as audio:
    resp = requests.post(url, data={'chat_id': chat_id, 'caption': '🎙️ 今日信号弹'},
                         files={'audio': audio}, proxies=proxies, timeout=60)
assert resp.status_code == 200 and resp.json().get('ok'), f"Audio failed: {resp.text}"

# === sendMessage (script text) ===
with open(script_path) as f:
    script_text = f.read()
msg_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
msg_resp = requests.post(msg_url, data={'chat_id': chat_id, 'text': script_text},
                         proxies=proxies, timeout=30)
assert msg_resp.status_code == 200
```

**Result (2026-06-05):** Audio msg_id=1076, script msg_id=1077 delivered to 1921948418.

**Note on SSL**: Previous sessions (2026-05-29) saw `ssl.SSLError: [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]` when `requests` in `execute_code` tried TLS 1.3 against api.telegram.org. This appears to be **intermittent or proxy-dependent** — with the proxy `http://10.10.10.150:7890`, `requests` works fine. If SSL fails, fall back to Method B.

### Method B: `curl --tlsv1.2` via `subprocess` (fallback, verified 2026-05-29)

Use when Method A's SSL handshake fails:

```python
import subprocess, json

cmd = ["curl", "-s", "--tlsv1.2", "-X", "POST",
       f"https://api.telegram.org/bot{token}/sendAudio",
       "-F", f"audio=@{mp3_path}",
       "-F", "chat_id=1921948418",
       "-F", "caption=🎙️ 今日信号弹"]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
resp = json.loads(result.stdout)
assert resp.get('ok'), f"Audio failed: {resp}"
```

**⚠️ Always use `-X POST` with `-F`** — bare `-F` alone returns 404 for `sendAudio`.

**Why curl --tlsv1.2**: Python `requests` in the sandbox uses TLS 1.3 by default, which api.telegram.org sometimes misnegotiates. `curl --tlsv1.2` forces TLS 1.2. In `terminal()`, `requests` always works fine — the SSL issue is sandbox-specific.

## Cron Delivery Gap

The shell script `generate_audio_only.sh` does NOT include Telegram delivery. The Hermes cron job's `deliver: origin` only delivers text, not files. **File delivery must be done by the cron agent calling Telegram bot API directly after TTS completes**, using the pattern above.

## File Size Limits

| Method | Limit |
|--------|-------|
| Telegram Bot API (sendAudio) | 50 MB |
| Recommended max for reliability | ~10 MB |

Signal Pop daily MP3 is ~11 MB (6 audio segments). Within limits but needs `timeout=120`.
