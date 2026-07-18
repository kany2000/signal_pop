#!/usr/bin/env python3
"""Sensenova-u1-fast 生图，失败自动降级到 Pollinations"""
import urllib.request, urllib.parse, json, io, os, time

API_URL = "https://token.sensenova.cn/v1/images/generations"
API_KEY = "sk-Orks5KCFxdjhRSm7EEFY57UdykEWzWIQ"
MODEL = "sensenova-u1-fast"
SIZE = "2752x1536"  # 16:9

def gen_image(prompt, seed=42, timeout=120):
    """Sensenova 优先 → Pollinations 备选。返回 (jpeg_bytes, source)."""
    # 1) Sensenova
    try:
        payload = json.dumps({
            "model": MODEL,
            "prompt": prompt,
            "size": SIZE,
            "n": 1,
        }).encode()
        req = urllib.request.Request(
            API_URL, data=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read())

        url = resp.get("data", [{}])[0].get("url")
        if url:
            # 下载图片并转 JPEG
            img_req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req, timeout=timeout) as ir:
                data = ir.read()
            # 检查是否是 PNG/JPEG
            if len(data) > 10000:
                # 尝试转 JPEG（PNG 太大）
                from PIL import Image
                img = Image.open(io.BytesIO(data))
                out = io.BytesIO()
                img.convert("RGB").save(out, "JPEG", quality=88)
                return out.getvalue(), "sensenova"
    except Exception as e:
        print(f"  Sensenova 失败: {e}")

    # 2) Pollinations 降级
    try:
        q = urllib.parse.quote(f"{prompt}?width=1280&height=720&nologo=true&seed={seed}")
        url = f"https://image.pollinations.ai/prompt/{q}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Referer": "https://pollinations.ai/",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if len(data) > 10000:
            return data, "pollinations"
    except Exception as e:
        print(f"  Pollinations 降级也失败: {e}")

    return None, "failed"


def gen_image_file(prompt, out_path, seed=42, timeout=120):
    """生成图片并保存到文件。返回 (path, source) 或 (None, 'failed')."""
    data, source = gen_image(prompt, seed, timeout)
    if data:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(data)
        return out_path, source
    return None, "failed"


if __name__ == "__main__":
    # 测试
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else "a cute cat sitting at a desk working, office background, warm lighting"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/sensenova_test.jpg"
    path, source = gen_image_file(prompt, out)
    if path:
        print(f"✅ {source} → {path} ({os.path.getsize(path)//1024}KB)")
    else:
        print("❌ 全部失败")