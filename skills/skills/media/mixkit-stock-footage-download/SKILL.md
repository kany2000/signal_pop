---
name: mixkit-stock-footage-download
description: Download free stock footage from Mixkit via direct CDN (no API key needed) and use in OpenMontage Remotion pipeline.
---

# Mixkit Stock Footage Download & OpenMontage Integration

## When to Use
Need stock footage (people, nature, city, lifestyle) for OpenMontage video compositions but no stock API keys available.

## How Mixkit CDN Works
- Mixkit videos hosted at `https://assets.mixkit.co/videos/{id}/{id}-720.mp4`
- Replace `720` with `1080` or `4k` for higher quality
- No API key, no cookies, no rate limiting
- Scrape search page to find clip IDs:
  ```
  curl -sL "https://mixkit.co/free-stock-video/{search-slug}/" | grep -oP 'src="https://assets\.mixkit\.co/videos/\d+/\d+-720\.mp4"'
  ```

## Workflow

### 1. Search for clips
Go to `https://mixkit.co/free-stock-video/{keyword}/` (e.g., `woman-rain` for woman rain clips).
Or grep page source:
```bash
curl -sL "https://mixkit.co/free-stock-video/woman-rain/" -H "User-Agent: Mozilla/5.0" | grep -oP 'href="[^"]*\.mp4[^"]*"|src="[^"]*\.mp4[^"]*"'
```

### 2. Download clip by ID
```bash
# 720p (default)
curl -sL "https://assets.mixkit.co/videos/46707/46707-720.mp4" -o mixkit_46707.mp4

# 1080p (if available)
curl -sL "https://assets.mixkit.co/videos/46707/46707-1080.mp4" -o mixkit_46707.mp4
```

### 3. Verify content
Generate thumbnail and inspect:
```bash
ffmpeg -y -v error -ss 1 -i mixkit_46707.mp4 -frames:v 1 thumb.jpg
```

### 4. Prepare for Remotion
Convert any non-h264 clips:
```bash
ffmpeg -i input.webm -c:v libx264 -crf 23 -preset fast output.mp4
```
Copy to Remotion public dir:
```bash
cp clip.mp4 /path/to/remotion-composer/public/clips_xxx/
```

### 5. Create JSON config
```json
{
  "scenes": [
    {
      "id": "scene_01",
      "kind": "video",
      "startSeconds": 0,
      "durationSeconds": 8,
      "src": "clips_xxx/mixkit_46707.mp4",
      "tone": "cold",
      "fadeInFrames": 0,
      "fadeOutFrames": 10
    },
    {
      "id": "title_scene",
      "kind": "title",
      "startSeconds": 33,
      "durationSeconds": 5,
      "text": "Scene Title",
      "accent": "#00D4FF",
      "intensity": 0.85,
      "variant": "overlay"
    }
  ],
  "titleFontSize": 88,
  "titleWidth": 1450,
  "signalLineCount": 22,
  "music": {
    "src": "music_pixabay.mp3",
    "volume": 0.18,
    "fadeInSeconds": 2,
    "fadeOutSeconds": 3
  }
}
```

### 6. Render with Remotion
```bash
cd /path/to/remotion-composer/
npx remotion render CinematicRenderer output.mp4 --props=config.json --concurrency=1 --overwrite
```

## Common Clip IDs (woman in rain)
| ID | Description | Duration |
|----|-------------|----------|
| 46707 | Woman walking in cold rain on city street | ~19s |
| 46706 | Woman close-up in cold rain, park setting | ~22s |
| 49582 | Woman crouching in dramatic night rain | ~19s |
| 11681 | Woman with umbrella in rain, daytime park | ~7s |

## Pitfalls
- **Download timeout**: Mixkit CDN slow for large files, use `--max-time 30` with curl
- **Broken downloads**: Check file size > 100KB, delete 0-byte/truncated files
- **720p only**: Most clips only have 720p variant available
- **Search slug**: URL slug format is lowercase-hyphenated (e.g., "woman rain" → "woman-rain")
- **No night footage**: Most are dusk/overcast, not true night; combine with night atmosphere B-roll for effect
