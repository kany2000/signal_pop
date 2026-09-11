#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末版 · 混合来源配图拉取

- source=="real" 且提供 real_url：直接 curl 下载网络真实高清图
- source=="metaphor"/"ai"：走 Sensenova（win_pipeline_images.gen_sensenova）生成
  metaphor 项 prompt 已约定「无真人、无 celebrity 名」，属擦边球隐喻
输出：IMAGES_DIR 下 breaking.jpg / news_01.jpg ... / summary.jpg / watch.jpg / interactive.jpg
"""
import os
import sys
import io
import time
import urllib.request

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from win_pipeline_images import gen_sensenova, _save_image  # noqa: E402

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 每期复用的模板图（summary/interactive/pick）：从 shared/ 复制，避免每期重复生图
SHARED_DIR = os.path.join(PROJECT_ROOT, "output", "weekly", "shared")
SHARED_IDS = ("summary", "interactive", "pick")


def download_real(url, out_path, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.google.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if len(data) < 5000:
        raise ValueError(f"real image too small ({len(data)} bytes)")
    _save_image(data, out_path)
    return True


def _gen_with_retry(prompt, max_retries=7, base=15):
    """Sensenova 限流(429)退避重试：指数等待，避免连发被打。"""
    last = None
    for attempt in range(max_retries):
        try:
            return gen_sensenova(prompt)
        except Exception as e:  # 含 HTTP 429 / 网络抖动
            last = e
            wait = base * (2 ** attempt)
            print(f"    ⚠️ gen 失败({e})，{wait}s 后重试({attempt+1}/{max_retries})")
            time.sleep(wait)
    raise last


def fetch_weekly_images(items, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for it in items:
        out = os.path.join(out_dir, it["img"])
        if os.path.exists(out) and os.path.getsize(out) > 5000:
            print(f"  skip {it['img']} (exists)")
            continue
        # 每期复用模板图：summary/interactive/pick 直接从 shared/ 复制，不再生图（省工作量）
        if it["img_id"] in SHARED_IDS:
            sp = os.path.join(SHARED_DIR, it["img"])
            if os.path.exists(sp) and os.path.getsize(sp) > 5000:
                import shutil
                shutil.copy(sp, out)
                print(f"  ♻️ reuse {it['img']} <- shared")
                continue
        src = it.get("source")
        if src == "real" and it.get("real_url"):
            try:
                download_real(it["real_url"], out)
                print(f"  ✅ real {it['img']} <- {it['real_url'][:60]}")
                continue
            except Exception as e:
                print(f"  ⚠️ real 下载失败 {it['img']}: {e}，回退 Sensenova")
        # metaphor / ai / real无url -> Sensenova（带限流退避）
        # 定律：图片绝不加文字（AI 图一加文字就出乱码），统一后缀强制去文字
        base_prompt = it.get("prompt") or "news scene, documentary photography"
        prompt = base_prompt + ", no readable text, no words, no letters, no typography, no labels, no signage, no captions"
        try:
            time.sleep(5)  # 请求间节流，降低 429 概率
            data = _gen_with_retry(prompt)
            _save_image(data, out)
            print(f"  ✅ sensenova {it['img']} ({src})")
        except Exception as e:
            print(f"  ❌ {it['img']} 生成失败: {e}")
    print(f"[images] 完成 -> {out_dir}")


if __name__ == "__main__":
    import json
    parsed = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJECT_ROOT, "output", "weekly", "20260828", "images")
    items = json.load(open(parsed, encoding="utf-8"))
    fetch_weekly_images(items, out_dir)
