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
import urllib.request

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from win_pipeline_images import gen_sensenova, _save_image  # noqa: E402

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def download_real(url, out_path, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.google.com/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if len(data) < 5000:
        raise ValueError(f"real image too small ({len(data)} bytes)")
    _save_image(data, out_path)
    return True


def fetch_weekly_images(items, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for it in items:
        out = os.path.join(out_dir, it["img"])
        if os.path.exists(out) and os.path.getsize(out) > 5000:
            print(f"  skip {it['img']} (exists)")
            continue
        src = it.get("source")
        if src == "real" and it.get("real_url"):
            try:
                download_real(it["real_url"], out)
                print(f"  ✅ real {it['img']} <- {it['real_url'][:60]}")
                continue
            except Exception as e:
                print(f"  ⚠️ real 下载失败 {it['img']}: {e}，回退 Sensenova")
        # metaphor / ai / real无url -> Sensenova
        prompt = it.get("prompt") or "news scene, documentary photography, no text"
        try:
            data = gen_sensenova(prompt)
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
