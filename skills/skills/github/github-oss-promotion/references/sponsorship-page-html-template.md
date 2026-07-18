# Support Page HTML Template Pattern

Pattern used to create a sponsorship/support page matching an existing project website's dark-theme design. Two language versions shown: Chinese and English.

## Directory Structure

```
project-website/
├── index.html             ← Landing page (Chinese)
├── landing-en.html        ← Landing page (English)
├── ...
└── support/
    ├── index.html         ← Support page (Chinese)
    ├── index-en.html      ← Support page (English)
    ├── bmc-cover.png      ← Buy Me a Coffee cover (1600×400)
    └── gen_cover.py       ← Cover generator script
```

## CSS Variables Used

```css
:root {
  --gradient-start: #667eea;
  --gradient-end: #764ba2;
  --bg-dark: #0a0a0f;
  --bg-dark-secondary: #12121a;
  --bg-dark-tertiary: #1a1a25;
  --text-dark: #ffffff;
  --text-dark-secondary: #a0a0b0;
  --card-bg-dark: rgba(255,255,255,0.03);
  --card-border-dark: rgba(255,255,255,0.08);
  --glow-dark: rgba(102,126,234,0.3);
  /* ... light theme variants ... */
}
```

## Page Sections (in order)

### 1. Hero
```html
<section class="hero">
  <h1><span class="gradient-text">赞助支持</span></h1>
  <p>QuickTranslate 是一款完全免费的开源 Chrome 扩展...</p>
  <div class="hero-buttons">
    <a href="https://buymeacoffee.com/username" class="btn btn-primary">☕ Buy Me a Coffee</a>
    <a href="https://paypal.me/username" class="btn btn-secondary">💳 PayPal</a>
  </div>
  <a href="../index.html" class="back-link">← 返回首页</a>
</section>
```

### 2. Why Support
```html
<section class="why-support">
  <div class="container">
    <h2 class="section-title reveal">为什么要赞助？</h2>
    <div class="why-text reveal">
      <p>Project description and cost explanation...</p>
      <p>🛠️ New features · ☁️ Infrastructure · 📚 Docs · 🌍 Localization</p>
    </div>
  </div>
</section>
```

### 3. Tiers (Payment Cards)
```html
<div class="tiers-grid">
  <!-- Alipay QR (QR placeholder) -->
  <div class="tier-card reveal">
    <div class="tier-icon">📱</div>
    <h3>支付宝收款码</h3>
    <div class="tier-price">随意金额</div>
    <div class="qr-placeholder">
      <div class="qr-box">
        <span class="qr-icon">📷</span>
        <span class="qr-text">扫码赞助</span>
        <span class="qr-hint">二维码准备中</span>
      </div>
    </div>
  </div>

  <!-- Buy Me a Coffee (featured) -->
  <div class="tier-card featured reveal">
    <div class="tier-badge">推荐</div>
    <div class="tier-icon">☕</div>
    <h3>Buy Me a Coffee</h3>
    <div class="tier-price">随意金额</div>
    <ul class="tier-perks">
      <li>赞助者名单展示</li>
      <li>优先功能反馈</li>
      <li>内测版体验资格</li>
    </ul>
    <a href="https://buymeacoffee.com/username" class="sponsor-btn primary">☕ 请我喝杯咖啡</a>
  </div>

  <!-- PayPal / GitHub Sponsors -->
  <div class="tier-card reveal">
    <div class="tier-icon">💳</div>
    <h3>PayPal</h3>
    <div class="tier-price">Any Amount</div>
    <ul class="tier-perks">
      <li>Sponsor wall recognition</li>
      <li>Priority feature feedback</li>
      <li>Early access to beta builds</li>
    </ul>
    <a href="https://paypal.me/username" class="sponsor-btn secondary">💳 PayPal.me</a>
  </div>
</div>
```

### 4. Other Ways (Free Support)
```html
<section class="why-support">
  <div class="container">
    <h2 class="section-title reveal">其他支持方式</h2>
    <div class="why-text reveal">
      <p>⭐ Chrome Store review</p>
      <p>🌟 GitHub Star</p>
      <p>📢 Share with friends</p>
      <p>🐛 Report bugs</p>
      <p>🌍 Help translate</p>
    </div>
  </div>
</section>
```

### 5. FAQ (Accordion)
```html
<section class="faq">
  <div class="container">
    <h2 class="section-title reveal">常见问题</h2>
    <div class="faq-list">
      <div class="faq-item reveal">
        <button class="faq-question">What do sponsors get?<span class="faq-icon">+</span></button>
        <div class="faq-answer">
          <div class="faq-answer-inner">Sponsors get name on wall, priority feedback, beta access...</div>
        </div>
      </div>
    </div>
  </div>
</section>
```

### 6. Footer
```html
<footer>
  <div class="footer-links">
    <a href="../index.html" class="footer-link">首页</a>
    <a href="https://github.com/user/project" class="footer-link">GitHub</a>
    <a href="chrome-web-store-url" class="footer-link">Chrome Web Store</a>
  </div>
  <p class="footer-copyright">Made with ❤️ by Project Team · vX.Y.Z</p>
</footer>
```

## QR Code Placeholder CSS

```css
.qr-placeholder { margin-bottom: 16px; }
.qr-box {
  width: 140px; height: 140px;
  margin: 0 auto;
  border: 2px dashed var(--card-border);
  border-radius: 16px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 6px;
  background: var(--bg-tertiary);
  transition: all 0.3s ease;
}
.qr-box:hover {
  border-color: var(--gradient-start);
  box-shadow: 0 0 20px var(--glow);
}
.qr-icon { font-size: 28px; }
.qr-text { font-size: 13px; font-weight: 600; color: var(--text); }
.qr-hint { font-size: 11px; color: var(--text-secondary); }
```

To replace with actual QR image:
```html
<div class="qr-placeholder">
  <img src="../assets/alipay-qr.png" alt="支付宝收款码" style="width:140px;height:140px;border-radius:12px;">
</div>
```

## Multi-Language Landing Page Footer Update

Add to each landing page's footer:
```html
<a href="support/index.html" class="footer-link">赞助支持</a>    <!-- Chinese -->
<a href="support/index-en.html" class="footer-link">Support</a> <!-- English -->
```

## Key Patterns

1. **Placeholder-first**: Create page with placeholder links (coming-soon), replace when user provides real URLs
2. **Design parity**: Copy CSS variables directly from existing site — same theme toggle, particles, fonts
3. **Language dropdown subset**: Only show existing support page variants in language switcher to avoid 404s
4. **Unused CSS is harmless**: Keep CSS for placeholder-notice, .btn styles from main site — no need to strip
5. **cover image**: Added as a standalone PNG, linked nowhere in HTML (it's only for the BMC profile page)
