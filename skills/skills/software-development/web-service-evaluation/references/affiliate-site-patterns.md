# Affiliate/SEO Site Patterns

## Telltale Signs

### Tech Stack
- **Astro v5+** — static islands, heavy client-side hydration
- **17+ languages** — i18n routing for SEO (`/zh/`, `/es/`, etc.)
- **Schema.org** — `WebApplication`, `WebPage`, `BreadcrumbList` everywhere
- **Uniconsent CMP** — consent banner (GDPR compliance theater)

### Ad Stack (Always Present)
| Provider | Signature |
|----------|-----------|
| BuySellAds | `bsa-zone_*` slots, `rewardedSlotReady`, `makeRewardedVisible()` |
| Google AdSense | `data-ad-client="G-XXXXXXXX"` in `<script>` |
| Monetag | `window.Monetag` + push notification prompts |
| OptAd360 | `optAd360` global, `optAd360Manager` |

### Model Marketing Names (Fake)
- "GPT-5.2", "GPT-5"
- "Claude-Sonnet-4.5", "Claude-Opus-4.5"
- "Gemini-3-Pro", "Gemini-3-Flash"
- "DeepSeek-R2", "DeepSeek-V4"
- **Real models in dropdown**: `openai/gpt-image-2`, `google/nano-banana`, `flux-schnell`, `runway/gen-4`, `bytedance/seedream-4`

### URL Patterns
- `/tools/ai-chat`, `/tools/text-to-speech-free`, `/image-generators`
- `/api/generate-ai-answer`, `/api/generate-image`, `/api/jina-fetch`
- `robots.txt` allows all, aggressive `sitemap.xml`

## Behavioral Patterns

1. **No real API keys** — everything gated behind browser session
2. **Turnstile CAPTCHA** — required before first generation
3. **Rewarded ad gate** — must watch 30s ad per generation
4. **Client-side rate limit** — `localStorage` counters, 30s cooldown
5. **Fake streaming** — SSE but actually polls or returns all at once
6. **Error messages generic** — "Sorry, I don't know the answer to that question"

## Why They Exist
- **Arbitrage**: Free traffic → ad impressions → revenue
- **SEO**: "Free GPT-5", "Free AI Image Generator" keywords
- **Affiliate**: Drive signups to real providers (Replicate, Fal, etc.)
- **Email capture**: Waitlists, "notify me" forms