#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末版 · 混合来源配图拉取

⚠️ 2026-11-02 实测警告：**Pollinations 匿名层的 `nologo=true` 已失效**，仍会在右下角打
`pollinations.ai` 花体 logo（~210×80px），不带 nologo 则直接 402；Sensenova 兜底则带「日日新」水印。
即本脚本**无法产出无水印图**。当前推荐做法：
  ① 用 WorkBuddy 内置生图工具（ImageGen）逐张生成 → 交付 `images/`（原图带「AI生成 WORKBUDDY」标记）
     + `images_nomark/`（纯底部裁切 135px 无标记版），由用户拍板；
  ② 本脚本保留作批量兜底与真实网图下载（source=="real" 且有 real_url 时完全可用、无水印）。
**任何新后端上线前，先人工看一眼右下角，别默认无水印。**

- source=="real" 且提供 real_url：直接 curl 下载网络真实高清图（天然无水印）
- source=="ai"/"metaphor"：走 Pollinations（flux + nologo=true）→ Sensenova 兜底
- source=="shared"（summary/interactive/pick）：从 output/weekly/shared/ 复制，不每期重画
输出：IMAGES_DIR 下 breaking.jpg / news_01.jpg ... / summary.jpg / interactive.jpg / pick.jpg

铁律：配图阶段**禁止任何水印处理**（Sensenova 水印由用户自清，AI 只交原图）——
所以主后端必须是天生无水印的 Pollinations；一旦落到 Sensenova 兜底，原样交付不处理。
铁律：图片中不要加文字（AI 生图一出现可读文字就大概率出乱码）——去文字后缀程序化强制追加。
"""
import os
import sys
import io
import time
import urllib.parse
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from win_pipeline_images import gen_sensenova, _save_image  # noqa: E402

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 2026-11-06 改造：AI 图主后端从 Sensenova 改为 Pollinations（flux + nologo=true）。
# 理由：① Sensenova 右下角带「日日新」水印，而项目铁律是「配图阶段禁止任何水印处理」
#      （水印由用户自清，AI 只交原图）——不做处理就该选一个天生无水印的后端；
#   ② Pollinations 免鉴权、实测 ~2s/张、nologo=true 直出无水印；
#   ③ Sensenova 降级为兜底：网络抖动/限流时才走，且**原样交付不处理**。
# 尺寸统一 1920x1080（与 Remotion 16:9 画布一致），不再由 _save_image 拉伸非 16:9 源图。
POLLINATIONS_URL = (
    "https://image.pollinations.ai/prompt/{q}"
    "?width=1920&height=1080&seed={seed}&model=flux&nologo=true"
)

# 定律：图片中绝不出现可读文字（AI 生图一加文字就出乱码），统一后缀强制去文字。
NO_TEXT_SUFFIX = (
    ", no readable text, no words, no letters, no typography, no labels, "
    "no signage, no captions"
)

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


def gen_pollinations(prompt, seed, timeout=180):
    """Pollinations flux + nologo=true，直出无水印 1920x1080。"""
    q = urllib.parse.quote(prompt)
    url = POLLINATIONS_URL.format(q=q, seed=seed)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if len(data) < 20000:
        raise ValueError(f"pollinations image too small ({len(data)} bytes)")
    return data


def _seed_for(it, idx):
    """按条目内容派生稳定 seed —— 同一期重复生成时出图一致，便于复现与重做。"""
    import hashlib

    h = hashlib.md5(f"{it.get('img', '')}|{it.get('title', '')}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 100000 + idx


def _gen_with_retry(prompt, seed, max_retries=4, base=8):
    """主后端 Pollinations 失败退避重试；仍失败则回退 Sensenova（原样交付，不做水印处理）。"""
    last = None
    for attempt in range(max_retries):
        try:
            return gen_pollinations(prompt, seed + attempt), "pollinations"
        except Exception as e:  # 网络抖动 / 限流
            last = e
            wait = base * (2 ** attempt)
            print(f"    ⚠️ pollinations 失败({e})，{wait}s 后重试({attempt+1}/{max_retries})")
            time.sleep(wait)
    print(f"    ⚠️ pollinations 全失败，回退 Sensenova（原图带水印，由用户自清）")
    return gen_sensenova(prompt), "sensenova"


def fetch_weekly_images(items, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for idx, it in enumerate(items):
        out = os.path.join(out_dir, it["img"])
        if os.path.exists(out) and os.path.getsize(out) > 5000:
            print(f"  skip {it['img']} (exists)")
            continue
        # 每期复用模板图：summary/interactive/pick 直接从 shared/ 复制，不再生图（省工作量）
        if it.get("img_id") in SHARED_IDS:
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
                print(f"  ⚠️ real 下载失败 {it['img']}: {e}，回退 AI 生图")
        # ai / metaphor / real无url -> AI 生图（Pollinations 主 / Sensenova 兜底）
        base_prompt = it.get("prompt") or "news scene, documentary photography"
        prompt = base_prompt + NO_TEXT_SUFFIX
        try:
            data, backend = _gen_with_retry(prompt, _seed_for(it, idx))
            _save_image(data, out)
            print(f"  ✅ {backend} {it['img']} ({src})")
        except Exception as e:
            print(f"  ❌ {it['img']} 生成失败: {e}")
    print(f"[images] 完成 -> {out_dir}")


if __name__ == "__main__":
    import json
    parsed = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJECT_ROOT, "output", "weekly", "20260828", "images")
    items = json.load(open(parsed, encoding="utf-8"))
    fetch_weekly_images(items, out_dir)
