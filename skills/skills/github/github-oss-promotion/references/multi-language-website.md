# Multi-Language Website Conversion Optimization

Reference for systematically fixing all language versions of a project landing page during launch/promotion.

## File Discovery Pattern

```bash
# Find all HTML files recursively (exclude node_modules, .git)
find . -name '*.html' -not -path './node_modules/*' -not -path './.git/*' | sort
```

Typical structure:
```
project.xyz/
├── en/
│   ├── index.html
│   ├── faq.html
│   └── translate.html
├── zh/
│   ├── index.html
│   ├── faq.html
│   └── translate.html
├── ja/
│   ├── index.html
│   ├── faq.html
│   └── translate.html
└── index.html  (root, usually EN)
```

## Fix Checklist (apply to EVERY language version)

### P0 — Must fix

| Fix | Search for | Replace with |
|-----|-----------|-------------|
| Install URL → specific store | `chrome.google.com/webstore` | `chromewebstore.google.com/detail/EXTENSION_ID` |
| Dev mode guide → 1-click | `git clone`, `开发者模式` | Simple 3-step install flow |
| Inflated user counts | `100,000+` or any number > actual store users | Remove or "Newly launched · 开源" |
| "Non-trader" claim in store | `non-trader` in store listing | Change to `trader` (required for devs promoting own projects) |

### P1 — Strongly recommended

| Fix | Details |
|-----|---------|
| OG meta tags per language | `og:title`, `og:description`, `og:image` in each HTML file's `<head>` |
| Google Analytics snippet | Same G-XXXXXXX ID in all language versions |
| Star CTA text | Translated banner: "如果好用请点 ⭐ Star" → "Give us a ⭐ on GitHub" (EN), "気に入ったら ⭐ をお願いします" (JA) |
| Language switcher preserve | Ensure the lang-switch dropdown still works after edits (don't remove nav) |

## Approach

1. **First pass**: Read all files across languages to find every instance of the bad pattern (e.g. grep for `100,000` or `generic store URL`)
2. **Fix per-language**: For each language file, apply all fixes. Each file is standalone — don't assume fixes propagate.
3. **Verify after each file**: Open the file and check:
   - Install link → specific store URL (not generic)
   - Install guide → 1-click (not dev mode)
   - User count → honest (not inflated)
   - Language-switch dropdown still works (nav intact)
   - Analytics present (if intentional)
4. **Test**: Push changes, visit each language version in browser, click the install link. It should go directly to `chromewebstore.google.com/detail/...`.

## Pillow Asset Pitfall

When creating promotional GIFs with Pillow:
- `frames[0].save("demo.gif", append_images=frames[1:])` can silently produce tiny output (e.g. 128×83)
- **Fix**: Save frames as individual PNGs → use ImageMagick `convert -delay 100 -loop 0 frame-*.png demo.gif`
- Always verify with `identify demo.gif` or `python3 -c "from PIL import Image; print(Image.open('demo.gif').size)"`
