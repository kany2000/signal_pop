---
name: social-auto-upload
description: Manage video distribution to Chinese social media platforms (Douyin, Bilibili, Kuaishou, WeChat Channels, Xiaohongshu, Baijiahao) via the sau CLI. Covers login troubleshooting, cookie management, platform-specific quirks, and browser automation fixes for the social-auto-upload project.
---

# social-auto-upload (sau) — Distribution Toolkit

## Quick reference

| Platform | CLI prefix | Login method | Upload cmd |
|---|---|---|---|
| Douyin | `sau douyin` | Patchright browser QR | `upload` |
| Bilibili | `sau bilibili` | `biliup` CLI QR (standalone binary) | `upload-video` |
| Kuaishou | `sau kuaishou` | Patchright browser QR | `upload-video` |
| WeChat Channels | `sau tencent` | Patchright browser QR | `upload-video` |
| Xiaohongshu | `sau xiaohongshu` | Patchright browser QR | `upload-video` |
| Baijiahao | `sau baijiahao` | Patchright browser QR | `upload-video` |

## Login troubleshooting

### Common crash pattern: QR code extraction fails

**Problem:** Page structure changed, element selectors in `_extract_tencent_qrcode_src()` don't match → `RuntimeError("未获取到...二维码地址")` → login aborts.

**Fix:** Make QR extraction non-fatal. Wrap in try/except, fall through to wait loop. Browser still shows QR code visually — user can scan it even if script can't snapshot it.

**Patching checklist (see references/tencent-login-fix.md for full diff):**
1. `page.wait_for_url(..., timeout=5000)` → `page.goto(wait_until="domcontentloaded")` + `page.wait_for_load_state("networkidle", timeout=15000)` — page redirects to different URL after load
2. Wrap `_save_tencent_qrcode()` in try/except → set `qrcode_path=None; qrcode_info={}`
3. `_wait_for_tencent_login()`: access `qrcode_info["image_path"]` only when key exists — guard with `.get("image_path")`
4. `finally` block: guard `remove_qrcode_file()` with `if qrcode_path and ...`

### Browser: Executable doesn't exist

`patchright` (not `playwright`) is the browser automation library used. Its browsers live under a different version path than standard playwright.

**Fix:**
```bash
patchright install chromium
```

### Cookie management

#### Playwright storage_state format (sau native)
```json
{
  "cookies": [
    {
      "name": "...", "value": "...",
      "domain": "...", "path": "/",
      "expires": <unix_ts>,
      "httpOnly": false, "secure": true,
      "sameSite": "Lax"  // or "None" for session cookies
    }
  ],
  "origins": []
}
```

#### Manual cookie export (when QR login fails repeatedly)

1. Open Chrome → F12 → Application → Cookies → Export via **EditThisCookie** extension
2. File is JSON array — needs conversion to Playwright `storage_state` format
3. Key transforms:
   - `expirationDate` → `expires` (field rename)
   - `sameSite`: `"unspecified"`/`"no_restriction"` → `"Lax"` or `"None"` (Playwright strict enum)
   - Wrap in `{"cookies": [...], "origins": []}`
4. Save to: `cookies/<platform>_uploader/<account_name>` (no file extension)

#### Platform cookie locations

| Platform | Directory | Account file |
|---|---|---|
| Tencent/WeChat | `cookies/tencent_uploader/` | `signalpop` |
| Kuaishou | `cookies/ks_uploader/` | `her2home` |
| Bilibili | `~/.social-auto-upload/tools/biliup/...` (biliup native) | N/A — biliup manages its own |

### Bilibili (biliup) specific

Bilibili uses a standalone `biliup` binary (auto-downloaded from GitHub releases). Cookie format is biliup-specific:
```json
{
  "cookie_info": {
    "cookies": [
      {"name": "SESSDATA", "value": "...", "expires": ..., "http_only": 1, "secure": 0},
      {"name": "bili_jct", "value": "...", ...},
      {"name": "DedeUserID", "value": "...", ...}
    ],
    "domains": [".bilibili.com", ...]
  },
  "token_info": {
    "access_token": "...",
    "refresh_token": "..."
  }
}
```
Login via `sau bilibili login --account <name>` — prints QR code to terminal, scan with Bilibili app.

## Platform quirks

### WeChat Channels (tencent)
- Login URL: `https://channels.weixin.qq.com`
- Upload URL: `https://channels.weixin.qq.com/platform/post/create`
- Must be logged in with a WeChat account that has **already registered a video channel**
- QR code refreshes every ~60s — script auto-detects and refreshes
- Supports: `--short-title`, `--thumbnail` (3:4 portrait), `--thumbnail-landscape` (4:3), `--thumbnail-portrait` (3:4), `--category`, `--draft`

#### Cookie path mismatch (critical)

`sau` CLI saves cookies to `cookies/tencent_{account}.json`, but `tencent_setup` (in `uploader/tencent_uploader/main.py`) reads from `cookies/tencent_uploader/{account}` via `_resolve_account_file()`. After `sau tencent login` succeeds, the cookie is only in the sau path — upload will fail with "cookie missing or expired" because the uploader checks the wrong path.

**Fix:** Copy the cookie after login:
```bash
cp cookies/tencent_{account}.json cookies/tencent_uploader/{account}
```

#### Headless auth timeout

`cookie_auth()` uses `page.wait_for_load_state("networkidle", timeout=15000)`. On headless servers, the page may never reach `networkidle` within 15s (slow network, heavy JS). Replacing with `page.wait_for_timeout(8000)` works:

```python
# In uploader/tencent_uploader/main.py, cookie_auth():
await page.goto(TENCENT_UPLOAD_URL, wait_until="domcontentloaded")
await page.wait_for_timeout(8000)  # was: wait_for_load_state("networkidle", timeout=15000)
```

This is safe for headless operation — the markers (`get_by_text("扫码登录")`, `get_by_text("发表视频")`) are in the DOM after `domcontentloaded`, they don't need `networkidle`.

### Kuaishou
- Uses patchright chromium-1208 (locked version — don't `playwright install`, use `patchright install chromium`)

## CLI reference

```bash
# Login
sau <platform> login --account <name> [--headed]

# Check cookie
sau <platform> check --account <name>

# Upload
sau <platform> upload-video \
  --account <name> \
  --file <video.mp4> \
  --title <title> \
  --desc <description> \
  --tags tag1,tag2 \
  --schedule "YYYY-MM-DD HH:MM" \
  [--draft] \
  [--headed]

# Runtime flags (for login/upload with browser)
# --headed : show browser window (vs headless default)
# --headless : force headless
# --debug : verbose logging
```

## Pitfalls

1. **QR extraction fragility**: Platform frontend updates break element selectors often. Always wrap in try/except rather than letting them crash the login.
2. **patchright ≠ playwright**: Browsers downloaded by `playwright install` are wrong version for `patchright`. Always use `patchright install chromium`.
3. **Cookie sameSite enum**: Playwright strictly validates sameSite — `"unspecified"` / `"no_restriction"` from some export tools causes silent failures. Convert to `"Lax"` or `"None"`.
4. **Tencent auth page redirects**: After load, URL may redirect from `/post/create` to `/post/list` or `/platform`. `wait_for_url(..., exact_match)` fails — use `wait_for_load_state("networkidle")` instead.
5. **B站 token refresh**: `bili_jct` + `SESSDATA` have expiry — token_info's `refresh_token` can renew via `passport.bilibili.com/api/v2/sso`.