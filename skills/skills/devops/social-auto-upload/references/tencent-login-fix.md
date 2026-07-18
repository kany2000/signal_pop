# Tencent/WeChat Channels Login Fix — Patch Set

Applied 2026-07-11 to `uploader/tencent_uploader/main.py`.
3 independent crashes found when video channel frontend updated.

## Crash 1: page.wait_for_url() timeout on redirect

**Symptoms:** `Timeout 15000ms exceeded` / `"load" event fired` during `cookie_auth()`.

**Root cause:** `await page.wait_for_url(TENCENT_UPLOAD_URL, timeout=5000)` — page navigates from `/platform/post/create` to `/platform/post/list` or `/platform` after auth, so exact URL match fails.

**Fix:**
```python
# OLD — fails on redirect
await page.goto(TENCENT_UPLOAD_URL)
await page.wait_for_url(TENCENT_UPLOAD_URL, timeout=5000)

# NEW — tolerate redirect
await page.goto(TENCENT_UPLOAD_URL, wait_until="domcontentloaded")
await page.wait_for_load_state("networkidle", timeout=15000)
```

## Crash 2: QR code extraction aborts entire login

**Symptoms:** `RuntimeError("未获取到视频号登录二维码地址")` → `tencent_cookie_gen()` exception → login never enters wait loop.

**Root cause:** `_extract_tencent_qrcode_src()` uses element selectors that don't match the current frontend (iframe src, img.qrcode classes changed). The exception propagates up and kills the login before the user can scan.

**Fix:** Wrap `_save_tencent_qrcode()` in try/except. On failure: skip QR-saving (no local file), but still enter wait loop — browser shows QR visually for headed mode.

```python
try:
    qrcode_info = await _save_tencent_qrcode(
        page, account_file, qrcode_callback=qrcode_callback
    )
    qrcode_path = Path(qrcode_info["image_path"])
    tencent_logger.info("请扫码...")
except Exception as qr_e:
    qrcode_path = None
    qrcode_info = {}
    tencent_logger.warning(f"二维码提取失败（{qr_e}），请在浏览器中直接扫码")
```

## Crash 3: KeyError: 'image_path' on empty qrcode_info

**Symptoms:** `KeyError: 'image_path'` after QR extraction skip.

**Root cause:** `_wait_for_tencent_login()` unconditionally accesses `qrcode_info["image_path"]` at line 314. After crash 2's fix, `qrcode_info={}` causes KeyError.

**Fix in `_wait_for_tencent_login()`:**
```python
qrcode_path = Path(qrcode_info["image_path"]) if qrcode_info.get("image_path") else None
```
Also guard `_is_tencent_qrcode_expired` handler:
```python
if await _is_tencent_qrcode_expired(page) and qrcode_path:
    # ... refresh logic only when we have a path to track
```

And guard `finally` cleanup:
```python
if qrcode_path and qrcode_utils["remove_qrcode_file"](qrcode_path):
    ...
```

## Cookie format conversion (manual export)

When using EditThisCookie extension to export cookies, the JSON format differs from Playwright's `storage_state()`. Conversion script:

```python
import json

def convert_editthis_to_playwright(cookies_json_array):
    """Convert EditThisCookie JSON array → Playwright storage_state."""
    pw_cookies = []
    for c in cookies_json_array:
        ss = c.get("sameSite", "Lax").lower()
        if ss in ("unspecified", "no_restriction"):
            ss = "None" if c.get("secure") else "Lax"
        else:
            ss = ss.capitalize()
        pw_cookies.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "expires": c.get("expirationDate", c.get("expires", -1)),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
            "sameSite": ss,
        })
    return {"cookies": pw_cookies, "origins": []}
```

## Verdict

All three fixes make QR extraction non-fatal — the login proceeds even when the script can't snapshot the QR code. The user scans the QR code shown in the browser window, cookie auto-saves on success. No functional loss; the QR is only used for expiry-refresh tracking and local file cleanup, not for the scan itself.