# Gate Detection Cheatsheet

## CAPTCHA Providers

| Provider | DOM Signature | Token Field | Solve Cost |
|----------|---------------|-------------|------------|
| **Cloudflare Turnstile** | `<div id="cf-turnstile">` or `data-sitekey` | `cf-turnstile-response` | $1-3/1k (2Capsolver, CapMonster) |
| **hCaptcha** | `<div class="h-captcha">` | `h-captcha-response` | $2-4/1k |
| **reCAPTCHA v2** | `<div class="g-recaptcha">` | `g-recaptcha-response` | $1-2/1k |
| **reCAPTCHA v3** | Invisible, `grecaptcha.execute()` | `g-recaptcha-response` | Harder (score-based) |

## Rewarded Ad Gates

| Provider | JS Global | Trigger | Signal |
|----------|-----------|---------|--------|
| **BuySellAds** | `window.bsa`, `bsaPro` | `showRewardedAd()` | `rewardedSlotReady` event |
| **Google AdMob** | `googletag`, `googletag.cmd` | `googletag.pubads().refresh()` | `slotReady` + `rewarded` |
| **Unity Ads** | `UnityAds` | `UnityAds.show()` | `onUnityAdsComplete` |

## Request Payload Indicators

```json
// Turnstile/hCaptcha proof
{"question": "...", "interactionProof": "0.xxx...", "model": "..."}

// Rewarded ad proof
{"prompt": "...", "adViewProof": "eyJhbGciOi...", "model": "..."}

// Session cookie required
Cookie: session_id=abc123; cf_clearance=xyz...
```

## Response Signatures

| Response | Meaning |
|----------|---------|
| `{"error":"Unauthorized"}` | No auth header/cookie |
| `{"error":"Unauthorized request"}` | Invalid/missing browser fingerprint |
| `{"error":"CAPTCHA required"}` | Must solve challenge first |
| `{"error":"Ad view required"}` | Must complete rewarded ad |
| `{"error":"Rate limited"}` | Too many requests |
| `{"error":"Model unavailable"}` | Backend queue full |

## Cloudflare Managed Challenge (Full-Page)

Not all CF protections are created equal. Two distinct tiers:

| Type | DOM Signal | Bypass | Headless Playwright | puppeteer-stealth |
|------|-----------|--------|--------------------|-------------------|
| **Turnstile** (widget) | `<div id="cf-turnstile">`, `data-sitekey` | Capsolver (~$2/1k) | ✅ Works with solver | ✅ Works with solver |
| **Managed Challenge** (full page) | Title "Just a moment...", no navigation | **No known reliable method** | ❌ Blocked | ❌ Blocked (still blocked 2026-07) |

**Managed Challenge** is enterprise-grade. Page never navigates — stays stuck on the verification screen. The browser literally cannot reach the target content.

### How to detect early (before waiting 60s)
```bash
curl -sL "$URL" -H "User-Agent: Mozilla/5.0" | grep -c "Just a moment"
# 1 = managed challenge. 0 = pass or CF Turnstile
```

### Escalation ladder

| Step | Tool | Success Sign | Fail Sign |
|------|------|-------------|-----------|
| 1 | `curl -sL "$URL"` | HTML content | "Just a moment..." |
| 2 | `curl` + API endpoints directly | JSON response | 403 / empty |
| 3 | Playwright headless (bundled Chromium) | Title changes from "Just a moment..." | Stays on verification |
| 4 | Playwright channel='chrome' (system Chrome) | Same | Same |
| 5 | puppeteer-extra + stealth plugin | Same | Same |
| 6 | **Verdict**: If all 5 fail → **unreachable programmatically** | — | — |

### What Managed Challenge blocks
- ✅ curl / wget (always)
- ✅ Headless Playwright / Puppeteer
- ✅ puppeteer-extra with stealth
- ✅ System Chrome via `channel='chrome'` in headless
- ✅ Undetected-chromedriver
- ❌ Residential proxies + full headed browser (possible but requires X server)

### Practical takeaway
When managed challenge detected, **stop trying**. No headless tool + datacenter IP can pass. Options:
1. User opens in their own browser (has ambient trust)
2. Find mirror / API / cached copy (webcache, r.jina.ai — jina also blocks bad ASN)
3. Build local equivalent of service's core function
4. Residential proxy service (BrightData etc.) — not free, may still fail

## Quick curl Tests

```bash
# 1. Baseline - no headers
curl -X POST "$URL/api/endpoint" -d '{}'

# 2. With JSON content-type
curl -X POST "$URL/api/endpoint" -H "Content-Type: application/json" -d '{"test":true}'

# 3. With browser-like headers
curl -X POST "$URL/api/endpoint" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)..." \
  -H "Origin: $BASE" \
  -H "Referer: $BASE/tools/..." \
  -d '{}'

# 4. With session cookie (if you have one)
curl -X POST "$URL/api/endpoint" \
  -H "Cookie: session=...; cf_clearance=..." \
  -d '{}'
```

## Decision Matrix

| Signals | Verdict | Action |
|---------|---------|--------|
| All endpoints work with curl | **Programmatic** | Use directly |
| Chat works, image gen needs CAPTCHA | **Partial** | Chat API only |
| All need Turnstile + ad gate | **Browser-only** | Playwright + solver |
| 404 on claimed endpoints | **Fake/Deprecated** | Abandon |
| Generic errors, no model info | **Proxy/Reseller** | Find upstream |