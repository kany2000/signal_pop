#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop 周末版 · 真实网图抓取助手

给定新闻文章页 URL，提取正文候选图片（og:image / <img> src / data-src），
按尺寸/过滤规则挑出最佳内容图下载为 1920 宽级高清图。
用途：weekly 配图 real 项（Wikimedia 被墙后改走国内新闻源 sina/thepaper/163/qq 等）。

用法：
  python tools/fetch_real_images.py <article_url> <out.jpg> [--min-w 800]
返回 exit 0 成功；失败打印原因。
"""
import os
import re
import sys
import urllib.request

PROJECT_ROOT = "E:/projects/signal_pop"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from win_pipeline_images import _save_image  # noqa: E402

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# 允许直连的图源 CDN（实测可达）；不在名单内的 host 跳过，避免长时间超时
ALLOWED_HOSTS = (
    "sinaimg.cn", "itc.cn", "thepaper.cn", "img1.baidu.com", "gtimg.com",
    "163.com", "netease", "126.net", "ifengimg.com", "jiemian.com",
    "std.stcn.com", "yicai.com", "xinhuanet.com", "people.com.cn",
    "chinanews.com", "hkex.com.hk", "i.guancha.cn", "statics",
    "qpic.cn", "toutiaoimg.com", "sohu.com", "lixiang.com", "stnn.cc",
    "chinadaily", "zaobao.com",
)

BAD_PAT = re.compile(r"logo|icon|avatar|qr|sprite|blank|loading|placeholder|\.svg|\.gif", re.I)


def fetch_html(url, timeout=20):
    import ssl as _ssl
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": url})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read().decode("utf-8", "ignore")


def extract_img_urls(html):
    urls = []
    # og:image
    for m in re.finditer(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html):
        urls.append(m.group(1))
    for m in re.finditer(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html):
        urls.append(m.group(1))
    # img src / data-src / data-original
    for m in re.finditer(r'(?:data-src|data-original|src)=["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']', html, re.I):
        urls.append(m.group(1))
    # 协议相对
    extra = []
    for u in urls:
        if u.startswith("//"):
            extra.append("https:" + u)
    return urls + extra


def pick_best(urls, min_w=800):
    cands = []
    seen = set()
    for u in urls:
        u = u.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        if BAD_PAT.search(u):
            continue
        host_ok = any(h in u for h in ALLOWED_HOSTS)
        if not host_ok:
            continue
        # URL 内嵌尺寸提示优先
        mm = re.search(r"(?:w|width)[=/](\d{3,4})", u)
        w_hint = int(mm.group(1)) if mm else 0
        cands.append((w_hint, len(u), u))
    cands.sort(reverse=True)
    return [u for _, _, u in cands]


def url_variants(u):
    """生成防盗链/缩放参数变体：网易代理图去 thumbnail 参数取原图；gtimg 尝试 _0 原图。"""
    v = [u]
    if "nimg.ws.126.net" in u and "thumbnail=" in u:
        v.append(u.split("&thumbnail=")[0])
    if "inews.gtimg.com" in u and re.search(r"_\w+$", u):
        base = re.sub(r"_\w+$", "_0", u)
        v.insert(0, base)
    return v


def probe_and_download(cand_urls, out_path, min_w=800, timeout=25, referer="https://news.qq.com/"):
    """逐个尝试候选图（含 URL 变体），下载后用尺寸过滤（PIL）。带 Referer 防盗链。"""
    from PIL import Image
    import io as _io
    import ssl as _ssl
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    for i, u0 in enumerate(cand_urls[:14]):
        for u in url_variants(u0):
            try:
                req = urllib.request.Request(
                    u, headers={"User-Agent": UA, "Referer": referer, "Accept": "image/*,*/*;q=0.8"}
                )
                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                    data = r.read()
                if len(data) < 15000:
                    print(f"  skip[{i}] too small {len(data)}B: {u[:80]}")
                    continue
                im = Image.open(_io.BytesIO(data))
                w, h = im.size
                if w < min_w or h < min_w * 0.5:
                    print(f"  skip[{i}] {w}x{h} < min: {u[:80]}")
                    continue
                # 统一转 jpg
                rgb = im.convert("RGB")
                buf = _io.BytesIO()
                rgb.save(buf, "JPEG", quality=90)
                _save_image(buf.getvalue(), out_path)
                print(f"  ✅ {os.path.basename(out_path)} {w}x{h} <- {u[:90]}")
                return True
            except Exception as e:  # noqa: BLE001
                print(f"  skip[{i}] {type(e).__name__}: {u[:80]}")
    return False


def main():
    url, out = sys.argv[1], sys.argv[2]
    min_w = int(sys.argv[3]) if len(sys.argv) > 3 else 800
    html = fetch_html(url)
    urls = extract_img_urls(html)
    best = pick_best(urls, min_w)
    if not probe_and_download(best, out, min_w):
        print(f"  ❌ 无可用图: {url}")
        sys.exit(1)


if __name__ == "__main__":
    main()
