---
title: Signal Pop 新闻配图生成
description: 用 Sensenova-u1-fast 为 Signal Pop 新闻稿生成配图，Pollinations(flux) 备选
name: signal-pop-news-images
---

## 触发条件

需要为 Signal Pop 新闻稿生成配图时使用。

## 流程

### 1. 配图引擎

**Sensenova-u1-fast 优先**（2752×1536，16:9），失败自动降级到 Pollinations（`model=flux`，1024×576）。

```python
SENSENOVA_URL = "https://token.sensenova.cn/v1/images/generations"
SENSENOVA_KEY = "sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ"
SENSENOVA_MODEL = "sensenova-u1-fast"
SENSENOVA_SIZE = "2752x1536"
```

### 2. Prompt 构建规则

先按关键词匹配，失败用通用模板：

| 关键词 | 模板 |
|--------|------|
| 哲学家 | Silicon Valley recruiting philosophers, AI era judgment essential, digital brain and ancient Greek scroll, cinematic lighting |
| AI | AI technology concept, neural network, glowing data streams, futuristic |
| 科技 | modern technology concept, digital innovation, blue glow, cinematic |
| 经济 | economic data chart, financial growth, business illustration, modern |
| 国内 | China national news, modern flat illustration, professional |
| 国际/人形机器人/油价/新势力/台风/抖音/鸿蒙/讯飞/上市/618/Hyper3D/AReaL | 见 `scripts/gen_news_images.py` |

**通用回退**：`news illustration, modern technology concept, {title[:50]}, cinematic, photorealistic`

**规则**：
- 提示词必须加 `no people, no logos, no brand text, no text`（除非场景明确需要人物）
- 地理/时政类必须加地理方位（如 `London street, Big Ben clock tower`）
- 每张配图场景类型必须不同，不可复用

### 3. 脚本

`/home/kan/shared/signal_pop/scripts/gen_news_images.py`

用法：
```bash
cd /home/kan/signal_pop && python3 scripts/gen_news_images.py
```

自动从 `archive/signal_pop_daily_{Ymd}.txt` 读取新闻稿内容，提取标题，生成配图到 `archive/img_{Ymd}/`。

### 4. 手动生成单张配图

```python
import urllib.request, json, io
from PIL import Image

SENSENOVA_URL = "https://token.sensenova.cn/v1/images/generations"
SENSENOVA_KEY = "sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ"
SENSENOVA_MODEL = "sensenova-u1-fast"
SENSENOVA_SIZE = "2752x1536"

payload = json.dumps({
    "model": SENSENOVA_MODEL,
    "prompt": "your prompt, no people, no logos, photorealistic",
    "size": SENSENOVA_SIZE,
    "n": 1,
}).encode()

req = urllib.request.Request(
    SENSENOVA_URL, data=payload,
    headers={
        "Authorization": f"Bearer {SENSENOVA_KEY}",
        "Content-Type": "application/json",
    },
    method="POST"
)
with urllib.request.urlopen(req, timeout=120) as r:
    resp = json.loads(r.read())
url = resp.get("data", [{}])[0].get("url")
img_req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(img_req, timeout=120) as ir:
    img = Image.open(io.BytesIO(ir.read()))
out = io.BytesIO()
img.convert("RGB").save(out, "JPEG", quality=88)
with open("/path/to/output.jpg", "wb") as f:
    f.write(out.getvalue())
```

### 5. 备选：Pollinations（仅当 Sensenova 不可用）

```python
import urllib.parse, urllib.request
url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote('prompt')}?width=1920&height=1080&model=flux&nofeed=true&seed=123"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=180) as resp:
    data = resp.read()
```

**关键**：必须加 `model=flux`，否则默认模型会乱出人像。

## 坑

- **Pollinations 不加 `model=flux`** → 出人像/科幻人物，完全不按提示词
- **Pollinations 不加 `width`/`height`** → 默认 1024×576 小图
- **Sensenova 图片 URL 有时效**（1小时），必须下载到本地
- **Sensenova 返回 PNG** → 需转 JPEG（`Image.convert("RGB").save(out, "JPEG", quality=88)`）
- **场景类型必须每期不同**（不可复用上一期同一场景），用日期种子让 Sensenova 每次出不同图
- **地理配图必须精确**（加卫星鸟瞰/具体地标/海岸线等方位描述）

## 验证

- 检查生成的图片尺寸：Sensenova = 2752×1536，Pollinations(flux) = 1920×1080
- 检查图片内容：无人物/无英文文字/无品牌标志
- 检查平均色：暗淡偏蓝=夜景/科技，暖色=经济/国内，彩色=港口/城市