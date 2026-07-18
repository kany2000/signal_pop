# Promotional Asset Creation with Pillow

> Reference: Full Python script for zero-budget promotional image & GIF creation.
> Requirements: `pip install pillow`

## Asset Set (create all at once)

```python
from PIL import Image, ImageDraw, ImageFont
import os

OUT = "./promo-assets"
os.makedirs(OUT, exist_ok=True)

# ---- Font Helpers ----
def get_font(size):
    """Try CJK fonts first, fall back to default."""
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()


# ============================================================
# 1. HERO BANNER (1280×800)
# ============================================================
def create_banner(project_name, tagline, features, accent_color, store_url):
    """Create main hero banner for README/website."""
    W, H = 1280, 800
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Gradient background (interpolate between two colors)
    for y in range(H):
        r = int(accent_color[0] + (accent_color[3] - accent_color[0]) * y / H)
        g = int(accent_color[1] + (accent_color[4] - accent_color[1]) * y / H)
        b = int(accent_color[2] + (accent_color[5] - accent_color[2]) * y / H)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # Title + Tagline
    draw.text((80, 120), project_name, fill=(255, 255, 255), font=get_font(72))
    draw.text((80, 210), tagline, fill=(255, 255, 255, 200), font=get_font(36))

    # Feature bullets
    for i, feat in enumerate(features):
        draw.text((80, 320 + i * 50), f"✅  {feat}", fill=(255, 255, 255, 200), font=get_font(22))

    # CTA Button
    draw.rounded_rectangle([80, 620, 480, 680], radius=30, fill=(255, 255, 255, 230))
    draw.text((100, 635), "🧩  Install from Chrome Store", fill=accent_color[:3], font=get_font(24))

    img.save(f"{OUT}/hero-banner-1280x800.png")
    return img


# ============================================================
# 2. SOCIAL CARD (1200×630) — for OG:image / Twitter
# ============================================================
def create_social_card(project_name, tagline, accent_color, store_url):
    """Create shareable social media card."""
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        r = int(accent_color[0] + (accent_color[3] - accent_color[0]) * y / H)
        g = int(accent_color[1] + (accent_color[4] - accent_color[1]) * y / H)
        b = int(accent_color[2] + (accent_color[5] - accent_color[2]) * y / H)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    draw.text((60, 80), project_name, fill=(255, 255, 255), font=get_font(64))
    draw.text((60, 160), tagline, fill=(255, 255, 255, 200), font=get_font(28))
    draw.text((60, 220), "Open Source · Free · Chrome Extension", fill=(255, 255, 255, 150), font=get_font(20))

    # CTA
    draw.rounded_rectangle([60, 480, 400, 540], radius=30, fill=(255, 255, 255, 230))
    draw.text((80, 496), "Install from Chrome Store", fill=accent_color[:3], font=get_font(20))

    img.save(f"{OUT}/social-card-1200x630.png")
    return img


# ============================================================
# 3. FEATURE CARD (600×700) — one per feature
# ============================================================
def create_feature_card(title, subtitle, description, accent_color, filename):
    """Create individual feature showcase card."""
    W, H = 600, 700
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Subtle gradient background
    for y in range(H):
        a = int(15 * (1 - y / H))
        draw.line([(0, y), (W, y)], fill=accent_color[:3] + (a,))

    # Card body
    draw.rounded_rectangle([15, 15, W - 15, H - 15], radius=20, fill=(255, 255, 255, 240))
    draw.rounded_rectangle([15, 15, W - 15, H - 15], radius=20, outline=accent_color[:3] + (60,), width=2)

    # Accent header
    draw.rounded_rectangle([15, 15, W - 15, 85], radius=20, fill=accent_color[:3] + (25,))

    # Title/Subtitle
    draw.text((40, 30), title, fill=(40, 40, 40), font=get_font(28))
    draw.text((40, 68), subtitle, fill=(120, 120, 120), font=get_font(16))

    # Description lines
    f_body = get_font(18)
    y = 120
    for line in description.split('\n'):
        if line.startswith('>'):
            draw.text((40, y), line[1:], fill=accent_color[:3], font=get_font(17))
        elif line.startswith('  -'):
            draw.text((55, y), line, fill=(80, 80, 80), font=f_body)
        else:
            draw.text((40, y), line, fill=(100, 100, 100), font=f_body)
        y += 30

    # Bottom callout
    highlight_y = H - 120
    draw.rounded_rectangle([40, highlight_y, W - 40, highlight_y + 80], radius=12,
                           fill=accent_color[:3] + (12,))
    draw.text((55, highlight_y + 15), "✨  Operation Comparison", fill=accent_color[:3], font=get_font(15))
    draw.text((55, highlight_y + 48), "Traditional 5 steps → This 2 steps", fill=(100, 100, 100), font=get_font(14))

    img.save(f"{OUT}/{filename}.png")
    return img


# ============================================================
# 4. COMPARISON CHART (700×500) — vs competitors
# ============================================================
def create_comparison(title, rows, accent_color, filename):
    """Create comparison table vs competitors. rows=[(feature, competitor, yours), ...]"""
    W, H = 700, 500
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([10, 10, W - 10, H - 10], radius=16,
                           fill=(248, 249, 252), outline=accent_color[:3] + (40,), width=2)
    draw.text((40, 30), title, fill=(40, 40, 40), font=get_font(22))

    # Headers
    headers = ["Feature", "Others", "This Project"]
    col_x = [40, 180, 400]
    for i, h in enumerate(headers):
        draw.text((col_x[i], 80), h, fill=accent_color[:3], font=get_font(14))
    draw.line([(30, 108), (W - 30, 108)], fill=accent_color[:3] + (30,), width=1)

    for i, (feature, competitor, ours) in enumerate(rows):
        y = 128 + i * 40
        bg = (240, 242, 248) if i % 2 == 0 else (255, 255, 255)
        draw.rectangle([20, y, W - 20, y + 36], fill=bg)
        draw.text((col_x[0], y + 6), feature, fill=(60, 60, 60), font=get_font(13))
        draw.text((col_x[1], y + 6), competitor, fill=(180, 80, 80), font=get_font(13))
        draw.text((col_x[2], y + 6), ours, fill=(60, 160, 80), font=get_font(13))

    img.save(f"{OUT}/{filename}.png")
    return img


# ============================================================
# 5. DEMO GIF (800×520) — animated workflow
# ============================================================
def create_demo_frames(steps_config):
    """Create animated GIF frames for a browser workflow demo.

    steps_config: list of dicts with 'step_name' + 'duration_multiplier'
    Each step renders progressively: browse → select → button → result → done
    """
    W, H = 800, 520
    purple = (102, 126, 234)

    def draw_frame(step):
        img = Image.new("RGBA", (W, H), (240, 240, 245, 255))
        draw = ImageDraw.Draw(img)

        # Browser chrome
        draw.rectangle([0, 0, W, 45], fill=(220, 220, 225))
        draw.rectangle([0, 0, W - 1, H - 1], outline=(200, 200, 205), width=1)

        # URL bar
        draw.rounded_rectangle([15, 8, 500, 37], radius=15, fill=(255, 255, 255))
        draw.text((25, 13), "https://example.com/article", fill=(80, 80, 80), font=get_font(12))

        # Window buttons
        for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
            draw.ellipse([W - 30 + i * 25, 14, W - 18 + i * 25, 26], fill=c)

        # Page content (fake text)
        content = [
            "Article Title (source language)",
            "The development of technology has dramatically changed",
            "how we interact with the world around us. From the",
            "invention of the wheel to modern artificial intelligence,",
            "each breakthrough has opened new possibilities.",
            "",
            "Key areas of innovation include:",
            "  - Artificial Intelligence and Machine Learning",
            "  - Quantum Computing",
            "  - Biotechnology and Genetic Engineering",
        ]
        cy = 60
        for line in content:
            draw.text((30, cy), line, fill=(120, 120, 120), font=get_font(12))
            cy += 18

        f14 = get_font(14)
        f12 = get_font(12)

        # Step-specific overlays
        if step == 1:  # Text selected
            draw.rectangle([28, 58, 340, 78], fill=purple + (40,))
            draw.text((30, 59), "Article Title (source language)", fill=purple, font=f14)

        elif step == 2:  # Translate button appears
            draw.rectangle([28, 58, 340, 78], fill=purple + (40,))
            draw.text((30, 59), "Article Title (source language)", fill=purple, font=f14)
            draw.rounded_rectangle([350, 56, 450, 80], radius=12, fill=purple + (230,))
            draw.text((362, 61), "Translate", fill=(255, 255, 255), font=f12)

        elif step == 3:  # Translation popup
            draw.rectangle([28, 58, 340, 78], fill=purple + (40,))
            draw.text((30, 59), "Article Title (source language)", fill=purple, font=f14)
            bx, by = 100, 95
            draw.rounded_rectangle([bx, by, bx + 380, by + 105], radius=16,
                                   fill=(255, 255, 255, 250), outline=purple + (100,), width=2)
            draw.rectangle([bx, by, bx + 380, by + 28], fill=purple + (20,))
            draw.text((bx + 15, by + 6), "Project Name", fill=purple, font=f14)
            draw.text((bx + 15, by + 36), "Original: Article Title (source)", fill=(100, 100, 100), font=f12)
            draw.text((bx + 15, by + 58), "Translation: 文章标题（译文）", fill=(60, 60, 60), font=f14)
            draw.rounded_rectangle([bx + 15, by + 80, bx + 95, by + 96], radius=8, fill=purple + (200,))
            draw.text((bx + 22, by + 81), "Copy  Save", fill=(255, 255, 255), font=f12)

        elif step == 4:  # Done
            draw.rectangle([28, 58, 340, 78], fill=purple + (40,))
            draw.text((30, 59), "Article Title (source language)", fill=purple, font=f14)
            draw.rounded_rectangle([100, 95, 450, 130], radius=16,
                                   fill=(255, 255, 255, 250), outline=(76, 175, 80, 100), width=2)
            draw.text((115, 102), "Translation done! Copied to clipboard", fill=(76, 175, 80), font=f14)

        # Step indicator at bottom
        steps_text = ["Browse", "Select", "Translate", "Result", "Done"]
        for i, s in enumerate(steps_text):
            sx = 60 + i * 148
            color = purple if i <= step else (180, 180, 180)
            draw.ellipse([sx, H - 40, sx + 20, H - 20],
                         fill=purple + (30,) if i <= step else (255, 255, 255),
                         outline=color, width=2)
            draw.text((sx + 5, H - 37), str(i + 1), fill=color, font=get_font(11))
            if i < len(steps_text) - 1:
                draw.line([(sx + 22, H - 30), (sx + 138, H - 30)], fill=(200, 200, 200), width=1)

        return img

    # Build frames with multipliers
    frames = []
    duration_map = {0: 4, 1: 2, 2: 2, 3: 4, 4: 3}  # Hold browse & result longer
    for step in range(5):
        for _ in range(duration_map[step]):
            frames.append(draw_frame(step))

    return frames


def save_gif(frames, output_path, duration=1000):
    frames[0].save(output_path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=False)
    print(f"GIF saved: {output_path} ({len(frames)} frames)")


# ============================================================
# EXAMPLE USAGE
# ============================================================
if __name__ == "__main__":
    accent = (102, 126, 234, 118, 75, 162)  # (start_r, start_g, start_b, end_r, end_g, end_b)

    # Banner
    create_banner(
        "QuickTranslate",
        "选中文字，即刻翻译",
        ["Select-to-translate <500ms", "Screenshot OCR (Alt+1)", "Hover to translate (Alt key)",
         "Multi-engine: Google/Microsoft/GLM/LLM", "Vocabulary book (500 entries)"],
        accent,
        "https://chromewebstore.google.com/detail/EXAMPLE_ID"
    )

    # Social card
    create_social_card("QuickTranslate", "选中文字，即刻翻译 · 3种模式 · 10+语言", accent, "")

    # Feature cards
    create_feature_card("Select Translate", "Select text → instant result",
                        "> Core workflow\n  Select text → translate button → result\n\n> Tech\n  DOM extraction, no OCR needed\n  98%+ accuracy\n\n> Use cases\n  Reading foreign web pages\n  Instant word lookup",
                        accent[:3], "feature-select")
    create_feature_card("Screenshot OCR", "Alt+1 to capture",
                        "> Core workflow\n  Press Alt+1 → drag area → auto translate\n\n> Tech\n  Smart region detection\n  95%+ success rate\n\n> Use cases\n  PDF documents\n  Image text",
                        (118, 75, 162), "feature-ocr")

    # Comparison
    create_comparison("Why choose this project?", [
        ("Instant translate", "Manual copy-paste", "Select → done <500ms"),
        ("Screenshot OCR", "Not supported", "Alt+1 capture"),
        ("Multi-engine", "Single engine", "Google/MS/GLM/LLM"),
        ("Open source", "Proprietary", "MIT"),
    ], accent[:3], "comparison")

    # Demo GIF
    frames = create_demo_frames([])
    save_gif(frames, f"{OUT}/demo-workflow.gif")

    print(f"\nAll assets created in {OUT}/")
```

## Design Tips

- **Brand color**: Use extension's accent color consistently across all assets
- **CJK fonts**: Always try `/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc` first
- **Alpha**: RGBA mode with alpha values for overlays and hover states
- **Gradient**: Line-by-line drawing for smooth transitions
- **GIF timing**: Hold key frames longer (browse: 4x, result: 4x, transitions: 2x)
- **Consistency**: Same font sizes, same card layout across all feature cards

## ⚠️ Pillow Version Compatibility

- **`rounded_rectangle` radius format**: Older Pillow versions (pre-10.x) accept `radius` only as a **single int**, e.g. `radius=16`. Passing a list like `radius=[16, 16, 0, 0]` raises `TypeError: '>=' not supported between instances of 'list' and 'int'`. Always use a single int radius. If you need selective corner rounding, draw a full rounded rect and overlay a regular rectangle on top of the un-rounded corners.
- **CJK font discovery**: Don't hardcode a single font path. Use a try/except loop over multiple common paths (`NotoSansCJK-Regular.ttc`, `wqy-zenhei.ttc`, `DroidSansFallbackFull.ttf`) before falling back to `ImageFont.load_default()`.
- **GIF optimization**: Set `optimize=False` when creating programmatic GIFs — optimization can strip critical frames or distort colors on simplex animations. Only set `optimize=True` for natural-image GIFs (screenshots).
