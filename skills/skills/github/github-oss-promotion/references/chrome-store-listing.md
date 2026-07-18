# Chrome Web Store Listing Reference

Quick reference for filling out the Chrome Web Store Developer Dashboard.

## Listing Fields

| Field | Character/Size Limit | Tips |
|-------|---------------------|------|
| **名称/Name** | ≤45 chars | Lead with keyword: `QuickTranslate - 网页划词翻译 + 截图翻译` |
| **简短描述/Short description** | ≤132 chars | Feature + benefit + numbers: `选中网页文字即翻译，0.5秒出结果，支持10+语言和截图OCR。` |
| **详细描述/Detailed description** | No hard limit | Use ✅ bullet points, `##` headers, natural keyword integration |
| **Category** | — | Productivity > Accessibility or Language |
| **Language** | — | At least: zh-CN, zh-TW, en-US, ja |
| **Screenshots** | 1280×800 or 640×400, PNG/JPG | 5-8 screenshots, first = core feature, uniform style |
| **图标/Icons** | 16, 48, 128 px PNG | Already in repo |

## Screenshots Checklist (5-8 total)

- [ ] First screenshot = the most valuable "wow" moment
- [ ] Uniform style (same border, font colors, purple gradient if brand matches)
- [ ] Chinese UI labeled in Chinese, English labeled in English
- [ ] Desktop screenshots only — no phone/tablet
- [ ] Each screenshot shows one clear action/outcome
- [ ] Suggested sequence:
  1. Select text → translate button appears
  2. Translation panel showing result
  3. Screenshot OCR mode
  4. Multi-language settings
  5. Vocabulary/history feature

## Suggested Short Description (English)

```
Select text to translate instantly. Screenshot OCR, 10+ languages, multi-engine backup. 0.5s response, 98% accuracy.
```

## Suggested Short Description (Chinese)

```
选中文字一键翻译，支持截图OCR、10+语言、多引擎备用。0.5秒极速响应，98%+识别准确率。
```

## ZIP Packaging

**Critical**: Only include files that actually exist. Run `ls` or `dir` on the project first.

```powershell
# Windows — verify files first
dir E:\projects\QuickTranslate\

# Then zip only the existing files
Compress-Archive -Path manifest.json, background.js, content.js, content.css, popup.html, popup.js, popup.css, float-panel.js, float-panel.css, quick-panel.js, quick-panel.css, i18n.js, icons, images, src -DestinationPath quicktranslate-v2.5.0.zip -Force
```

**Common mistake**: Including `float-panel.html`, `quick-panel.html`, `locales/` which don't exist. Always check file list first.

## Store Submission Timeline

1. Create listing → Fill all fields
2. Upload ZIP → System parses manifest.json
3. Privacy policy URL → Required if requesting host permissions (e.g. `<all_urls>`)
4. Submit for review → 3-7 day review
5. Approval → Live on Web Store

## Privacy Policy

Required for extensions with `<all_urls>` or any host permission. Simple static page:

- GitHub Pages: `https://kany2000.github.io/QuickTranslate/privacy`
- Keep it simple: what data you collect, what you don't, contact email

## Trader vs Non-Trader Account

- **Trader**: Developer promoting their own project (even if free/open-source). Correct for most OSS maintainers.
- **Non-trader**: Hobbyists with no business intent.

Google requires real ID verification for the developer account — fake info will cause suspension.

## Useful Links

- Dashboard: https://chrome.google.com/webstore/devconsole
- Policy doc: https://developer.chrome.com/docs/webstore/program-policies/
- Distribution: https://developer.chrome.com/docs/webstore/distribute/