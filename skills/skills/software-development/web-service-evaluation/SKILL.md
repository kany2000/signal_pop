---
name: web-service-evaluation
category: software-development
description: Evaluate actual capabilities of web services/APIs vs marketing claims. Probe endpoints, detect gates (CAPTCHA, ad walls, session auth), document real vs advertised features.
---

# Web Service Evaluation

## Purpose
Systematically test whether a web service's actual API capabilities match its marketing claims. Identify gating mechanisms (CAPTCHA, ad walls, session requirements, rate limits) that prevent programmatic use.

## When to Use
- User asks "can I use X service programmatically?"
- Evaluating a new AI/API provider before integration
- Verifying "free tier" claims vs reality
- Due diligence on third-party services

## Core Workflow

### 1. Reconnaissance (Passive)
- Fetch landing page + key tool pages via `curl`
- Extract: API endpoints from JS bundles, schema.org structured data, meta tags
- Identify tech stack (Astro, Next.js, etc.), analytics, ad providers
- Check for: Cloudflare Turnstile, hCaptcha, reCAPTCHA, rewarded ad gates

### 2. Endpoint Discovery
- Search JS bundles for: `fetch`, `axios`, `api/`, `/api/`, `endpoint`, `graphql`
- Note: Astro islands (`astro-island` components) often hydrate client-side only
- API routes typically under `/api/` or proxied via edge functions

### 3. Active Probing (Sequential)
```bash
# Chat/completion endpoint
curl -X POST "$BASE/api/generate-ai-answer" \
  -H "Content-Type: application/json" \
  -d '{"question":"test","conversationHistory":[]}'

# Image generation
curl -X POST "$BASE/api/generate-image" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","model_type":"fast"}'

# Ancillary endpoints (search, TTS, etc.)
curl -X POST "$BASE/api/jina-fetch" -d '{"type":"search","target":"test"}'
```

### 4. Gate Detection
| Signal | Meaning |
|--------|---------|
| `{"error":"Unauthorized"}` / `401` | Requires auth/session |
| `{"error":"Unauthorized request"}` | Requires browser context (cookies, fingerprint) |
| Cloudflare Turnstile `<div id="cf-turnstile">` | Human verification required |
| Rewarded ad modal (`bsa-zone_*` + `showRewardedAd`) | Must watch ad before each generation |
| `interactionProof` in request payload | Anti-bot token from client-side challenge |
| LocalStorage `mobile_chat_message_count` / `mobile_chat_cooldown_end` | Client-side rate limiting |

### 5. Browser Verification (If APIs Gated)
- Use Playwright/puppeteer to load page, complete CAPTCHA, trigger generation
- Observe: network requests, response format, actual model used
- Check: model dropdown vs actual model (marketing often lies)

### 6. Document Findings
```markdown
## Service: <name>
**URL:** <base>
**Claimed:** <models, limits, pricing>
**Actual:** <working endpoints, gates, real limits>
**Verdict:** <programmatic/usable/browser-only/unusable>
**Evidence:** <curl outputs, screenshots, network logs>
```

## Common Patterns

### Affiliate/SEO Aggregators
- Astro/Next.js static sites with heavy ad stacks (BuySellAds, AdSense, Monetag)
- Proxy Replicate/Fal/RunPod endpoints behind CAPTCHA + ad gate
- Marketing names: "GPT-5.2", "Claude-4.5" — usually fake
- Real models: `openai/gpt-image-2`, `google/nano-banana`, `flux-schnell` (visible in model dropdown)

### Legitimate Free Tiers
- Direct API key auth (no browser session)
- Clear rate limits in headers (`X-RateLimit-*`)
- OpenAPI/Swagger docs
- No CAPTCHA on API endpoints

## Tools
- `curl` — fast endpoint probing
- `browser_navigate` + `browser_console` — dynamic content, network inspection
- Playwright — full browser automation for gated flows
- `grep` JS bundles for endpoint discovery

## Pitfalls
- **Don't trust marketing copy** — verify via actual API calls
- **Don't assume "no signup" = programmatic access** — often means "no account but browser fingerprint required"
- **Test multiple endpoints** — chat may work but image gen gated differently
- **Check model dropdown** — actual model IDs often exposed in `<select>` options
- **Session storage/cookies** — some gates only enforce after N requests

## References
- `references/affiliate-site-patterns.md` — Common SEO/affiliate site patterns and tells
- `references/gate-detection-cheatsheet.md` — Quick reference for CAPTCHA/ad gate signatures, including Cloudflare Managed Challenge escalation ladder (step-by-step bypass attempt protocol)
- `references/closed-platform-evaluation.md` — How to conclusively determine a service has no programmatic access (403 on all /api/*, no OpenAPI, CF Managed Challenge, no GitHub repos). Step-by-step investigation sequence and verdict thresholds.