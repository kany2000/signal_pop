---
name: website-monetization
description: Monetize product websites and Chrome extensions — AdSense application, sponsor/donation pages, content strategy for small sites. Covers the full pipeline from site audit to AdSense approval.
---

# Website Monetization Guide

## When to Use
- User asks to add AdSense / monetization to a website
- User wants sponsor/donation pages (Alipay, WeChat, BMC)
- User wants to prepare a small product site for AdSense review
- User asks "how to apply for Google AdSense"

## Phase 1: Site Audit

1. **List all pages**: landing pages, language versions, support pages
2. **Check domain**: `.xyz` / `.us.kg` / free domains → stricter AdSense review; compensate with more content
3. **Check HTTPS**: required for AdSense
4. **Check site age**: new sites (<1 month) get rejected → wait 2-4 weeks after content is ready
5. **Check content quality**: original, substantial (not thin product pages)

## Phase 2: Pre-AdSense Content Checklist

### Required Pages
- [ ] **Privacy Policy** — must include: data collected, how collected (GA4, cookies), sharing with third parties (Google as ad partner), user rights, contact info, last updated date
- [ ] **Contact / About** — email or form
- [ ] **10+ pages** of original content minimum

### Recommended Content Types for Product Sites
- Blog posts: use cases, tutorials, comparisons ("Tool X vs Y")
- How-to guides
- Industry-relevant analysis
- Changelog / release notes (stretch goal)

### Content Quality Rules
- No "under construction" pages
- No machine-translated gibberish
- Each page 500+ words of original text

## Phase 3: AdSense Application

1. Go to https://adsense.google.com
2. Sign in with Google account
3. Enter site URL (https://...)
4. Select: display ads
5. Submit → wait 1-2 weeks for review

## Phase 4: After Approval

- Place ad code in `<head>` (similar to GA4 gtag placement)
- Auto-display ads on content pages
- **DO NOT** click your own ads (permanent ban)
- **DO NOT** use auto-click / paid traffic

## Sponsor / Donation Pages

### For Chinese Audience
- Alipay QR code (use收款码)
- WeChat Pay QR code
- Place both on the same page, side by side

### For International Audience
- Buy Me a Coffee (bmc.link)
- GitHub Sponsors (if applicable)
- Stripe / PayPal (requires credit card, deferred if unavailable)

### Placement
- Dedicated `/support/` or `/sponsor/` page
- Footer link on every page
- Keep visual style consistent with site theme

## Pitfalls to Watch For

| Pitfall | Solution |
|---------|----------|
| `.xyz` domain → AdSense stricter on free/cheap TLDs | Add more content, wait longer before applying |
| Site too new | Run 2-4 weeks before applying |
| No privacy policy → auto-reject | Create one before submitting |
| Insufficient content → auto-reject | 10+ pages minimum |
| Clicking own ads → permanent ban | Never click ads on your own site |
| Ads showing on empty/chrome-extension pages | Make sure ads only render on content pages |
| Pending payment stuck at $100 threshold | Minimum payout $100, rolls over if under |

## Verification

After all changes:
- Check all footer links work
- Verify privacy policy renders correctly on mobile
- Test multi-language paths if applicable
- Confirm sitemap.xml includes all new pages
