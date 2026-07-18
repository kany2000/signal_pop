---
name: github-oss-promotion
description: "Promote an open-source project: grow GitHub stars, submit to stores, post to platforms, content marketing."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Stars, Marketing, Chrome-Web-Store, Product-Hunt, Open-Source]
    related_skills: [github-repo-management, github-pr-workflow]
---

# Open-Source Project Promotion

Grow GitHub stars, get listed on extension stores, and build a user community for open-source projects.

## Quick Start Checklist

```
Day 1    Optimize repo: topics, .github/ files, CONTRIBUTING.md, GIF demo
Day 1    Landing page: fix install link to specific store URL, SEO meta, analytics
Day 1    Create assets: banners, feature cards, demo GIF (free tools: Pillow/Python)
Day 1    Add sponsorship/support page: payment methods, multi-language, cover image
Day 2-3  Chrome Web Store submission (3-7 day review, prepare assets during wait)
Day 3-4  Content blast: 掘金 + 知乎 + 即刻 (Chinese users first for CN-focused projects)
Day 5-7  Reddit + Indie Hackers + seed user outreach
Day 8+   Weekly: content posts, awesome list PRs, issue responses, store reviews
```

**Critical first step**: Before any promotion, ensure the install link on your website/GitHub README points to the **specific extension page** (not `chrome.google.com/webstore` generic), and the install guide shows **1-click store install** (not `git clone` + developer mode).

> 📋 See `references/chrome-store-listing.md` for the full store submission checklist.
> 📋 See `references/launch-templates.md` for ready-to-use post copy for all platforms.

---

## 1. Repo Professionalization

Before any promotion, make the repo look credible.

### GitHub Topics

In Settings → Topics, add 3-5 relevant tags. **Rule**: each topic ≤ 35 chars, lowercase, hyphens only, no spaces.

```bash
# Via API
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  https://api.github.com/repos/OWNER/REPO/topics \
  -d '{"names": ["chrome-extension", "translation", "productivity"]}'
```

### `.github/` Infrastructure

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md       # Labels: bug
│   └── feature_request.md  # Labels: enhancement
├── pull_request_template.md
└── FUNDING.yml            # Optional sponsors link
```

Create locally and push with git, or use `github-repo-management` skill Section 11.

### CONTRIBUTING.md

Place in repo root. Sections: how to report bugs, suggest features, PR workflow, code style, local testing, licensing note.

See `github-repo-management` skill references: `contributing-template.md`

### README First Impression

- **First 300 lines matter most** — front-load value proposition
- **Chrome Web Store badge at very top** — primary CTA should be store install, not git clone
- **Demo GIF/video in the first scroll** — 15-30s animated GIF showing core feature in action (convert button clicks into visual proof)
- **Star call-to-action at the top** — `如果好用，请点 ⭐ Star` above the fold, not just at the bottom
- Use badges: version, license, build status, Chrome Web Store
- **Install button links to specific extension page**, not generic store
- Natural keyword integration (don't keyword-stuff)
- For detailed documentation, use `<details>` tags to collapse long sections — keep first scroll focused on demo + install + star

**Optimal README structure (top-to-bottom):**

```
1. [Title + Badges row] → Project name, store badge, stars badge, version
2. [Star CTA banner] → "如果好用请点 Star ⭐"  — centered, right after badges
3. [Demo image/GIF] → 700px wide screenshot showing the core feature in action
4. [Tagline + Install buttons] → 2 big buttons: "Install from Chrome Store" + "Visit Website"
5. [Features table] → Compact table: feature | interaction | use case  (3 columns, <10 rows)
6. [Quick install section] → 1-click store install first, developer mode collapsed
7. [Detailed demos] → Section-by-section feature walkthrough with images
8. [Performance metrics] → Key metrics in a clean table
9. [Detailed documentation] → Collapsed under <details>
10. [Contributing + License + Footer star CTA]
```

**Why this order:**
- Stars + store button come before user scrolls → higher conversion
- Demo image loads instantly and shows value before user reads a single word
- Features table is skimmable; long prose comes after
- Detailed docs collapsed → keeps first-viewport length manageable
- Footer star CTA repeats the ask after user has seen the value

**Rule of thumb**: A user should be able to install the extension within 5 seconds of landing on the page, without scrolling. Achieve this by putting the store install button and a demonstration image in the first viewport.

---

## 2. Chrome Web Store Submission

The highest-leverage channel for browser extensions.

### Registration

1. [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole) — $5 one-time fee
2. Complete developer profile

### Listing Fields

| Field | Tips |
|-------|------|
| Name | Lead with keyword: `QuickTranslate - 网页划词翻译 + 截图翻译` |
| Short description | ≤ 132 chars. Feature + benefit + numbers: `选中网页文字即翻译，0.5秒出结果，支持10+语言和截图OCR。` |
| Detailed description | Markdown-style: ✅ feature list, use cases, privacy statement, changelog link |
| Category | Productivity > Accessibility or Language |
| Language | At least: zh-CN, zh-TW, en-US, ja |
| Screenshots | 1280×800 or 640×400, 5-8 screenshots, first = core feature, uniform style |

### Screenshots Checklist

- [ ] 5-8 screenshots showing the key flows
- [ ] Uniform style (same border, font colors)
- [ ] Chinese UI labeled in Chinese, English labeled in English
- [ ] No phone/tablet screenshots — desktop only
- [ ] First screenshot = the most valuable "wow" moment

### Store Assets Directory

```
repo/
├── store-assets/
│   ├── icons/  (16, 48, 128 px)
│   ├── screenshots/
│   │   ├── 01-main-feature.png
│   │   ├── 02-secondary-feature.png
│   │   └── ...
│   └── promo-video.mp4  (≤ 60s, silent, auto-play)
```

### Privacy Policy
### Privacy Policy
Required for extensions requesting permissions. Simple static page hosted on GitHub Pages: `https://username.github.io/project-name/privacy`

### Chrome Extension ZIP Packaging
**Critical**: Only include files needed at runtime. The `manifest.json` error on Chrome Web Store means a file is missing.

```powershell
# Windows PowerShell — list what files actually exist first
dir E:\\projects\\QuickTranslate\\

# Then zip only the existing files (no HTML files for panel-style extensions)
Compress-Archive -Path manifest.json, background.js, content.js, content.css, popup.html, popup.js, popup.css, float-panel.js, float-panel.css, quick-panel.js, quick-panel.css, i18n.js, icons, images, src -DestinationPath extension.zip -Force
```

**Common mistake**: Including files that don't exist (`float-panel.html`, `quick-panel.html`, `locales/`). Always `dir` or `ls` the project first to see real file names, then only zip files that exist.

### Submission

1. Zip the extension (manifest.json + all files, no `node_modules/`, no `.git/`)
2. Upload in dashboard, fill listing
3. Submit → 3-7 day review
4. Approval → extension goes live

---

## 2b. Dedicated Landing Page / Website

If your project has a dedicated website (e.g. `project-name.xyz`), it's often the first touchpoint for users. Optimize it aggressively.

### Critical Fixes (P0 — conversion killers)

| Issue | Fix | Impact |
|-------|-----|--------|
| Install button → generic store URL | Point to `chromewebstore.google.com/detail/EXTENSION_ID` | Directly increases install rate |
| Install guide shows `git clone` | Change to "Click button → Add to Chrome" 3-step flow | Non-developer users can now install |
| Inflated user numbers | Use real store data, or "Newly launched · Open source" | Avoids trust destruction |

### SEO & Metadata

```html
<!-- Must-have tags in <head> -->
<meta name="description" content="Project description with keywords.">
<meta property="og:title" content="Project Name">
<meta property="og:description" content="One-line value prop.">
<meta property="og:image" content="https://domain/og-image.png">
<meta property="og:url" content="https://domain/">
<meta name="twitter:card" content="summary_large_image">
```

### Trust Signals

- **Real demo media** — embed demo GIF/screenshots in the hero area, not a static placeholder
- **User count** — only use accurate store numbers (users check — inflated counts = immediate distrust)
- **No fake social proof** — "暂无评价，成为第一个用户" is better than fake testimonials
- **Open-source badge** + GitHub link visible in header/footer

### Multi-Language Website: Update ALL Language Versions

If your site has multiple language versions (e.g. `en/index.html`, `zh/index.html`, `ja/index.html`), **every fix must be applied to each version**. Common misses:

| Fix needed | Languages likely to still have the old version | Impact of missing |
|------------|-----------------------------------------------|-------------------|
| Install URL → specific store URL | CN/JP versions | EN users get fixed, CN/JP users land on generic store |
| Install guide (dev mode → 1-click) | JP version | Non-EN users see wrong instructions |
| Inflated user-count claims | CN version | CN users distrust the project |
| OG image / meta tags | All non-EN versions | Social previews broken for those languages |
| Analytics snippet | Non-EN pages | Under-counted traffic from CN/JP users |
| Star CTA banner text | Translated versions | Star button not visible to non-EN readers |

**Pattern**: Walk the directory tree systematically:

```python
for lang in ['en', 'zh', 'ja']:
    path = f'{lang}/index.html'
    if os.path.exists(path):
        # apply all fixes to this file
```

> 📋 See `references/multi-language-website.md` for the full fix checklist and Pillow → ImageMagick GIF fallback.

### Analytics (Free)

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXX');
</script>
```

Also submit to **Google Search Console** for free SEO insights.

---

## 2c. Sponsorship / Support Page

A dedicated sponsorship page is essential for open-source project sustainability. Add it as a sub-page of your project website (e.g. `domain/support/` or `domain/sponsor/`).

### Supported Payment Methods (Free)

| Method | Setup Time | Audience | China Payout? | Notes |
|--------|-----------|----------|--------------|-------|
| **Buy Me a Coffee** | 2 min | Global | ❌ Stripe doesn't support Chinese bank accounts | `buymeacoffee.com/username`. Cover image required (1600×400px). Can receive donations but money cannot be withdrawn via Chinese bank. |
| **GitHub Sponsors** | 5 min | Developers | ❌ Region not supported for mainland China | Enable in repo Settings → Sponsorship. Creates `github.com/sponsors/username`. |
| **PayPal.me** | 3 min | Global | ❌ Chinese bank cards cannot receive payouts | `paypal.me/username`. Do NOT add link until user confirms registration. |
| **支付宝收款码** | 1 min | China | ✅ Works natively | User screenshots their Alipay receive QR. Placeholder: 140×140px dashed box. Replace with `<img src="alipay-qr.png" class="qr-image">`. No platform fee. |
| **微信赞赏码** | 1 min | China | ✅ Works natively | WeChat → I → Payments → Collect → Save QR. Same replacement workflow as Alipay. |
| **爱发电 (afdian.net)** | 3 min | China | ✅ | May be inaccessible in some regions. Have Alipay/WeChat QR as fallback. |

**Recommended stack for CN + Global projects**: 支付宝收款码 (China primary) + Buy Me a Coffee (keep link with payout-disclaimer note) + GitHub Sponsors (dev, but note China region restriction).

**Critical reality for Chinese OSS developers**: Chinese bank cards (UnionPay) generally cannot be used to RECEIVE payouts from Stripe (BMC), PayPal, or GitHub Sponsors. The only reliable receiving methods are domestic: Alipay QR, WeChat QR, or 爱发电. Buy Me a Coffee and PayPal links should be kept with disclaimers like "pending payout setup" or "withdrawal limited" rather than presented as fully functional options.

### Page Structure

```
Hero            → Title, tagline, direct CTA buttons (BMC / PayPal)
Why Support     → Explain costs (servers, API, domain, dev time)
Tiers/Cards     → One card per method (icon, description, perks, CTA)
Other Ways      → Free support (Star, review, share, translate, report bugs)
FAQ             → What sponsors get, refunds, where money goes, corporate options
Footer          → Back to home, GitHub, Chrome Web Store
```

### Design Integration

Match the existing website's design:
- Same CSS variables (colors, fonts, spacing, radii)
- Same theme toggle (dark/light mode)
- Same particles / decorative elements
- Same scroll-reveal animations
- Same language switcher (only show existing support page variants)

### Payment Card Pattern

Each method gets a `.tier-card`:
```
.tier-icon         → Emoji (☕ 💳 📱 💖)
h3                 → Method name
.tier-price        → Price label
.tier-desc         → Short description
ul.tier-perks      → Benefits (sponsor wall, priority feedback, beta access)
.sponsor-btn       → CTA button linking to payment URL
```

For QR code methods (Alipay/WeChat), replace CTA with `.qr-placeholder` (140×140px dashed box). User provides actual QR image later.

### Cover Image for Buy Me a Coffee (1600×400)

Generate programmatically with Pillow:
- Dark gradient background matching website
- Rounded-rect logo with brand monogram
- Brand name + tagline + "开源免费" badge
- Decorative particles, gradient accent bars, dot patterns
- See `references/sponsorship-page-cover.md` for full script

### Workflow

```
1. Confirm payment methods (which are registered vs placeholder)
2. Create support page matching website design
3. Use temporary "coming soon" links for unregistered methods
4. Generate BMC cover image
5. Add "Support" link to ALL landing page footers
6. When user provides links → replace placeholders
7. When user provides QR → replace QR placeholder
```

### Pitfalls

- ❌ **Language switcher linking to non-existent pages** — only show support page variants that exist. Strip JA/KO/ZH-TW links from support-page language dropdown unless those pages exist.
- ❌ **Dead PayPal links** — don't link `paypal.me/username` until user confirms registration. Use placeholder text with note.
- ❌ **爱发电 inaccessible** — afdian.net unreachable in some regions. Always offer Alipay/WeChat QR as China fallback.
- ❌ **QR placeholder too prominent** — keep 140×140px, clearly marked "preparing".
- ❌ **Inconsistent footers** — adding "Support" to one language version means adding to ALL of them.
- ❌ **Hero placeholder notice stale** — once a payment link is live, remove "coming soon" banner.
- ❌ **Over-translating** — for uncommon languages, pointing to EN/CN support page is better than a broken translation.
- ❌ **Pre-adding unconfirmed payment links** — do NOT add PayPal.me/BMC/GitHub Sponsors links to the page until user confirms they registered the account. Show `<span class="placeholder-text">Coming soon</span>` or similar placeholder. Adding a dead link before confirmation forces a follow-up edit the user didn't ask for.
- ❌ **Chinese bank card payout assumption** — never assume Chinese bank cards (UnionPay) can receive payouts from Stripe (BMC), PayPal, or GitHub Sponsors. All three require international bank accounts for payout. Default to Alipay QR + WeChat QR as the primary receiving methods for China-based developers. Global methods should carry disclaimers like "payout setup pending" rather than presented as functional.
- ❌ **GitHub Sponsors region assumption** — GitHub Sponsors does not support mainland China for either sending or receiving. Do not list it as a valid option for Chinese developers without noting the restriction.
- ❌ **微信经营收款码 assumption** — do NOT suggest 微信经营收款码 unless user confirms they have a business license. Personal 赞赏码 (Tips QR) or 个人收款码 works for individual open-source projects and requires no business registration.
- ❌ **QR image source path unknown until user provides** — when creating QR placeholders, the actual image will come from a user-provided screenshot, not from any predictable path. Structure the HTML so the replacement is a single `<img src="..." alt="QR">` swap — don't embed QR in CSS backgrounds or complex layouts. Agree on filename convention (e.g. `alipay-qr.png`, `wechat-qr.png`) so replacement is simple.

### Reference Files

- `references/sponsorship-page-cover.md` — Full Pillow script for BMC cover image (1600×400)
- `references/sponsorship-page-html-template.md` — Complete HTML template pattern for support page (CN + EN)

---

## 3. Launch Day Posting

Post to multiple platforms simultaneously for maximum Day 1 visibility.

### Platform Comparison

| Platform | Audience | Language | Cost | Effort | Expected Reach |
|----------|----------|----------|------|--------|---------------|
| Product Hunt | Global makers | English | Free | 45 min | 50-200 visits |
| V2EX | Chinese devs | Chinese | Free (invite code req.) | 20 min | 100-500 visits |
| 掘金 | Chinese devs | Chinese | Free | 1 hr | 50-200 visits |
| Reddit r/ChromeExtensions | Global extension users | English | Free (account age + karma req.) | 30 min | 50-200 visits |
| Indie Hackers | Builders/entrepreneurs | English | Free | 25 min | 30-100 visits |

### Product Hunt Template

```
Title: [Project Name] — [One-liner benefit]

Tagline: [14 chars max]

Description:
- Bullet points of core features
- Why better than alternatives

Links: GitHub, Website, Chrome Web Store

Media: GIF/demo + 3-5 screenshots
```

### Product Hunt Shoutouts

Add 3-4 shoutouts (founder reviews) crediting products that helped build yours. Shoutouts increase featured probability and earn a link back from the recipient's product page.

**⚠️ Critical**: PH shoutouts are NOT free-text — you pick from PH's product database. Each shoutout also asks for "alternatives considered" (you check from a list of competitors) and "what made you choose" (your founder review text). Common options available in PH's database:

| PH Product | When to Use |
|------------|-------------|
| **Chrome Developer Tool** | Your extension runs on Chrome (NOT "Chrome Web Store" — that's not in PH's DB) |
| **GitHub** | Open-source project hosting |
| **VS Code** | If developed in VS Code |

Don't guess what's in PH's database — ask the user to search or screenshot the available options. The founder review format:

```
*"2-3 sentence explanation: what problem this product solved, why you picked it over alternatives, how it helped ship your project."*
```

What PH shows on the edit page:
1. Product name (search and select from DB)
2. "Other alternatives considered?" — check boxes from a provided list
3. "What made you choose [Product] over the alternatives?" — free-text founder review

Example real flow (from a Chrome extension launch):
- **Product**: Chrome Developer Tool
  - Alternatives considered: Plasmo, ExtensionKit, SuperDev Pro, Hoverify (check what's shown)
  - Review: "Chrome Developer Tool is the official debugging and development environment for Chrome extensions. It provides native Manifest V3 support, real-time service worker inspection, and direct access to extension-specific APIs — capabilities that third-party tools can't fully replicate. No extra dependencies, no abstraction layers to debug through."
- **Product**: GitHub
  - Alternatives considered: GitLab, GitKraken, CodeFactor (check what's shown)
  - Review: "GitHub's ecosystem — especially Actions for CI/CD, the largest developer community, and seamless PR workflows — made it the clear choice for maximizing project visibility and contributor reach."

### YouTube Video Description

Videos (demo, promo, tutorial) are cross-posted from YouTube to social media.

**Key constraint**: YouTube descriptions **cannot contain `<` or `>` characters** — they're parsed as HTML tags and silently stripped or cause rendering errors. Replace `X < Y` with "X under Y" or "X in less than Y". Replace `<500ms` with "0.5 seconds" or "under 500ms".

**Template**:

```
[Project Name] — [Descriptor] | [3-4 keywords separated by slash]

[2-3 sentence project description covering value prop + tech stack]

✨ Key Features
00:00 - Feature 1
00:05 - Feature 2
00:10 - Feature 3
00:15 - More features
00:20 - Get it now

🔗 Links
- Chrome Web Store → [store URL]
- GitHub → https://github.com/OWNER/REPO
- Website → [site URL]

Why [Project Name]?
- ✅ Bullet point 1
- ✅ Bullet point 2
- ✅ Bullet point 3

[Call to action]

#[Keyword1] #[Keyword2] #[Keyword3]
```

Note: Timestamps in description only work if video is at least 25s long (YouTube restriction). For shorter videos, omit timestamps or use floor names instead.

### Chinese Platform Template

```
🚀 我做了个「[核心功能]」的 [项目类型]

大家好，我是 [名字]，做了 [项目名](GitHub链接)。

✨ 核心功能：
• 功能点1
• 功能点2
• 功能点3

🔗 安装方式：
1. [Platform 1]
2. [Platform 2]

🙏 求支持：
欢迎 ⭐ + 提建议！
```

### V2EX Posting

- Node: `分享创造` or relevant tech node
- Title format: `「ProjectName」一句话描述`
- Include GIF in post body (hosted on Imgur/GitHub)
- Engage with replies quickly (first 2 hours matter)

---

## 4. Ongoing Growth

### Weekly Tasks

1. **Reply to every GitHub Issue** — fast responses = trust
2. **One content post** — 知乎/小红书/Dev.to (tutorial, use case, comparison)
3. **Update Release Notes** — post updates to community threads

### Submit to Awesome Lists

```
1. awesome-chrome-extensions
2. awesome-selfhosted (if applicable)
3. awesome-readme (if README is excellent)
4. 开源中国推荐项目
5. 少数派「利器」栏目
```

PR template:
```markdown
## [Project Name] - One-line description

- 🔗 Link: https://github.com/user/project
- ⭐ Stars: XX
- 🏷️ Tags: tag1, tag2
- Description...
```

### GitHub Insights Tracking

- Check **Traffic** tab weekly: clone/views/referrers
- Use [star-history.com](https://www.star-history.com/) to track growth
- Target: 10+ new stars/week after launch

### Review Prompt (In-App)

Add a gentle review prompt after user uses the product 5 times:

```javascript
// In popup.js or background.js
let count = localStorage.getItem('usage_count') || 0;
count++;
localStorage.setItem('usage_count', count);

if (count === 5 && !localStorage.getItem('review_asked')) {
  // Show "Rate us" button linking to Chrome Web Store
  localStorage.setItem('review_asked', 'true');
}
```

---

## 5. 30-Day Growth Calendar

```
Week 1  [Setup] Topics, .github/, README (store badge + GIF + star CTA at top)
Week 1  [Website] SEO meta tags, analytics, fix install link to specific store URL, replace dev-mode guide with 1-click install
Week 1  [Assets] Create banners, feature cards, demo GIF, social images (free: Pillow/Python)
Week 1  [Launch] 掘金 + 知乎 (Chinese first), then Reddit + Twitter (English)
Week 2  [Seed] Invite 5-10 users, ask for real store reviews
Week 3  [Content] 1 知乎 answer + 1 Dev.to article + comparison chart
Week 4  [Lists] Submit to 2-3 awesome lists, 小众软件
Ongoing [Ops] Weekly: respond to issues, post updates, monitor analytics, iterate
```

---

## 6. Pitfalls
### Pitfalls
- ❌ **Too many topics** — 3-5 focused topics beat 20 random ones
- ❌ **Topic too long** — GitHub error "consist of 50 characters or less" is misleading; the real per-topic limit is **35 characters**. Shorten any topic over 35 chars before saving.
- ❌ **Topic contains uppercase** — all topics must be lowercase. GitHub gives a misleading error about "starting with lowercase" which actually means the entire topic must be lowercase.
- ❌ **Keyword stuffing in store** — causes rejection + ranking penalty
- ❌ **Posting once and disappearing** — engagement after posting matters more than the post itself
- ❌ **Asking for stars without providing value** — seed users should be real testers first
- ❌ **Excessive permissions** — strip unnecessary permissions before store submission to avoid rejection
- ❌ **Non-trader account for commercial extensions** — selecting "non-trader" by mistake can cause issues; "trader" is correct for any developer promoting their own project (even if free/open-source). Non-trader applies only to hobbyists with no business intent.
- ❌ **Fake ID verification info** — Google requires real name/ID for Chrome Web Store developer verification. Fake names cause account suspension. This is mandatory, not optional.
- ❌ **Install link → generic store URL** — always link to the specific extension detail page, not `chrome.google.com/webstore`
- ❌ **Install guide shows developer mode** — put 1-click store install first; `git clone` developer mode should be a secondary "advanced" option
- ❌ **Inflated user numbers** — users check. A "100,000+ users" claim on a brand-new extension with 3 store users instantly destroys trust. Use real counts from the store dashboard, or qualifiers like "Newly launched · Open source". A single suspicious number can poison the entire project's credibility. Better to say "New" than to inflate.
- ❌ **No analytics on landing page** — you cannot improve what you don't measure. Add Google Analytics (free) from day one.
- ❌ **Static demo placeholder** — a non-functional "demo" widget is worse than screenshots or a GIF. Replace with real media.
- ❌ **Only fixing one language version** — if your site has `en/`, `zh/`, `ja/` directories, fixing only EN leaves CN/JP users with broken install links, old user counts, and wrong instructions. Walk all language directories systematically.
- ❌ **Pillow GIF turns out tiny** — Pillow's `append_images` can silently resize frames. Verify with `identify demo.gif`. Fallback: save frames as PNGs → `convert -delay 100 -loop 0 frame-*.png demo.gif` (ImageMagick).

---

## 7. Zero-Budget Promotional Asset Creation

When budget is $0, create all promotional media programmatically using Python + Pillow.

### Required Tools

```bash
pip install pillow  # Image generation (banners, cards, feature panels)
pip install moviepy # GIF/video creation (if ffmpeg is available)
```

No Canva, no Photoshop, no paid tools needed.

### Asset Types & Dimensions

| Asset | Size (W×H) | Usage |
|-------|-----------|-------|
| Hero banner | 1280×800 | README top, website hero |
| Social card | 1200×630 | OG:image, Twitter card |
| Feature card | 600×700 | Feature showcase, README gallery |
| Twitter card | 800×418 | Tweet attachments |
| Zhihu/Juejin cover | 1280×720 | Article cover image (desktop) |
| Zhihu/Juejin cover (thumb) | 192×128 | Article cover thumbnail — juejin/zhihu auto-generate from the 1280×720 original, no need to create separately unless the auto-crop looks bad |
| Comparison chart | 700×500 | Social proof, "vs competitors" |
| Comparison chart | 700×500 | Social proof, "vs competitors" |
| Install guide | 600×400 | WeChat/Telegram share |
| Demo GIF | 800×520 | README demo, social media |

### Pillow Pattern (Banner)

```python
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 800
img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# Gradient background
for y in range(H):
    r = int(102 + 16 * y / H)  # Interpolate between colors
    g = int(126 + 0 * y / H)
    b = int(234 - 72 * y / H)
    draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

# Text
def get_font(size):
    # Try CJK-first font paths
    paths = ["/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

draw.text((80, 120), "Project Name", fill=(255, 255, 255), font=get_font(72))
draw.text((80, 210), "Tagline", fill=(255, 255, 255, 200), font=get_font(36))

# CTA button
draw.rounded_rectangle([80, 600, 400, 660], radius=30, fill=(255, 255, 255, 230))
draw.text((100, 615), "Install from Store", fill=(102, 126, 234), font=get_font(24))

img.save("promo-banner.png")
```

**Key Pillow tips:**
- Use `draw.rounded_rectangle()` with a single int radius (list-style radius may fail on older Pillow)
- RGBA mode for transparency support
- Always handle CJK fonts via try/except font path fallbacks
- Use 4-tuple RGBA colors for alpha effects: `(r, g, b, alpha)`

**CJK font sizing on Linux — critical for small images:**
- Known-good CJK fonts on Ubuntu: `/usr/share/fonts/truetype/arphic/ukai.ttc` (UKai, decorative) and `/usr/share/fonts/truetype/arphic/uming.ttc` (UMing, serif). Also `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc` (need `index=0` for SC on some Pillow versions).
- **Small-image pitfall**: At 192×128px (article thumbnail), CJK text at 18px is invisible. Use ≥24px and only 2-4 characters. The bottom bar text at 9-10px won't render legibly — skip it or use English-only.
- If your image is 1280×720, 18px CJK text renders fine (the thumbnail is auto-generated by the platform). Only optimize for the actual pixel size you're targeting.

### Demo GIF Creation (Pillow + ImageMagick fallback)

**Pillow approach** (start here — works for simple animations):

```python
frames = [draw_frame(s) for s in ["browse", "select", "translate", "result", "done"]]
frames[0].save("demo.gif",
    save_all=True,
    append_images=frames[1:],
    duration=1000,
    loop=0)
```

⚠️ **Known pitfall**: Pillow's `save()` with `append_images` may silently produce a very small GIF (e.g. 128×83 instead of your intended 800×520). This happens when frames are `Image.new()` RGBA images — the save method resamples them. **Fix**: Save individual frames as PNGs, then assemble with ImageMagick `convert`:

```bash
# Step 1: Export frames as PNGs (ensure correct dimensions)
# Each frame should be written to frame-01.png, frame-02.png, etc.

# Step 2: Assemble with ImageMagick
convert -delay 100 -loop 0 frame-*.png demo.gif

# Step 3: Verify dimensions
identify demo.gif  # Should show your intended W×H for every frame
```

**`-delay` values**: divide by 10 for seconds. `-delay 100` = 1s per frame, `-delay 50` = 0.5s.

**Install ImageMagick if missing**:
```bash
sudo apt-get install imagemagick  # Linux
brew install imagemagick          # macOS
```

Each frame should simulate a browser window with: URL bar, page content, progressive UI states (text selection highlight → floating translate button → translation popup → completion).

### Feature Cards Pattern

Create individual 600×700 cards per feature with:
- Accent color matching your brand
- Title + subtitle
- Bullet-point feature description  
- "Scenario" callout box at bottom
- Consistent layout across all cards for a cohesive set

See `references/asset-creation-pillow.md` for a complete working script.

### Promo Video (Programmatic, 640×360)

Create silent MP4 promo videos entirely in Python with MoviePy + PIL — no video editor needed:

```python
from moviepy import ImageSequenceClip
import numpy as np
# Build scenes as lists of numpy frames, then:
clip = ImageSequenceClip(all_frames, fps=24)
clip.write_videofile("promo.mp4", codec='libx264', fps=24, preset='fast')
```

Each scene animates independently (fade-in, slide-up, staggered grid, cursor movement). Multiple scenes concatenated into one video. See `references/promo-video-moviepy.md` for full scene templates, font sizing, and animation techniques.

> 📋 Full working script at `references/promo-video-moviepy.md`

### YouTube Watermark (Channel Logo, 150×150)

Create 150×150 RGBA transparent watermarks for YouTube video branding:

- **Dark tech style**: rounded bg, dot grid, hex circuit lines, glow effects
- **Single monogram** (2-3 chars) in DejaVu Sans Bold 52pt
- **GaussianBlur glow** for neon effect
- **16px rounded corners** — blends better on dark video backgrounds
- For CJK channel names, use `/usr/share/fonts/truetype/arphic/ukai.ttc`

> 📋 See `references/youtube-watermark.md` for full pattern and color palette

### Free Alternatives

---

## 8. Platform-Specific Promotion Copies

See `references/launch-templates.md` for ready-to-use copies.

### Platform Targeting by Language

| Project Type | Primary Platforms | Secondary |
|-------------|-------------------|-----------|
| CN-focused, Chinese UI | 掘金, 知乎, 即刻 | 小众软件, 微信 |
| Global, English UI | Product Hunt, Reddit, Twitter/X | Indie Hackers, Dev.to |
| Both languages | Launch in Chinese first, then translate to English | Stagger by 1 week |

### Copy Structure (Universal)

```
1. Hook: Pain point + solution in 1 sentence
2. Demo: GIF/screenshot showing the "before vs after"
3. Features: 3-5 bullet points of core capabilities
4. Install: Specific store URL (not generic)
5. CTA: "Star on GitHub" / "Leave a review"
6. Context: Open source, free, tech stack (for dev audiences)
```

### Important: Engagement Strategy

- Posting = 20% of the work; replying = 80%
- Reply to every comment within 2 hours (first-day critical)
- Don't argue with criticism — thank and ask for specifics
- If V2EX requires invite code (common), ask a friend to post or skip to 掘金
- Cross-post the same content with platform-specific formatting

---