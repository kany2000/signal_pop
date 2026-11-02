#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_real_images_moli.py — Signal Pop · 新闻页高清原图探测（Moli 渲染版）

用途：
    输入一个或多个新闻 URL，用 Moli 无头浏览器渲染页面（执行 JS、
    触发懒加载），提取高分辨率原图 URL 清单（og:image + document.images
    + srcset，带真实 naturalWidth/Height 尺寸过滤）。
    供配图环节挑选「真实网络高清图」——对应 README 配图政策：
    硬新闻/突发/科技产品优先真实网络高分辨率图。

与 fetch_real_images.py 的分工（兄弟工具，勿混用）：
    fetch_real_images.py      urllib+正则，无 JS 渲染 → 适合静态页，
                              自带 CDN 白名单，直接下载 1920 宽落地
    fetch_real_images_moli.py 本工具。Moli 完整 JS 引擎 → 专攻
                              JS 渲染页 / 懒加载页（实测百度新闻等），
                              只产 URL 清单不下载；下载落地可把选中 URL
                              交给 fetch_real_images.py 的 _save_image 或 curl

依赖：
    - Moli 无头浏览器：默认 %LOCALAPPDATA%\\Moli\\bin\\moli.exe（v1.1.17 实测）
      可用 --moli 参数或 MOLI_BIN 环境变量覆盖
    - Python 3.10+，纯标准库，零第三方依赖（不 import config，保持独立可迁移）

项目内用法（在 signal_pop 根目录执行）：
    # 单个文章页
    python tools/fetch_real_images_moli.py https://www.thepaper.cn/newsDetail_forward_xxx

    # 从 raw_feed.json 提取 link 批量探测（审稿通过后的选图弹药）
    python -c "import json;[print(e['link']) for e in json.load(open('output/daily/<制作日>/raw_feed.json'))]" \
      | python tools/fetch_real_images_moli.py --flat --min-width 800 \
          --output output/daily/<制作日>/news_images.json

    # 尺寸 / 数量 / 格式过滤
    python tools/fetch_real_images_moli.py --min-width 800 --min-height 600 --max-images 5 <url>

    # URL 列表文件（一行一个，# 注释）/ stdin 管道同样支持
    python tools/fetch_real_images_moli.py --input urls.txt

输出（stdout 为纯 JSON，人类可读摘要走 stderr，方便管道）：
    {
      "tool": "moli_fetch_images", "version": "1.0.0",
      "params": {...},
      "results": [ { "url", "ok", "title", "challenge_suspected",
                     "images": [ {src,width,height,alt,origin,loaded,page_url} ],
                     "error", "dropped" } ],
      "summary": { "total_urls", "ok", "failed", "total_images" }
    }
    origin: meta=og/twitter 图（首选）、img=页面 img 标签、srcset=响应式变体
    loaded: true=浏览器真实加载并量到尺寸；false=懒加载未触发/候选

注意：
    - 反爬挑战页（如 36氪间歇性盾）会标记 challenge_suspected，选源时排雷
    - 本工具只探测不下载；CDN 可达性白名单见 fetch_real_images.py 的 ALLOWED_HOSTS

退出码：
    0  全部处理完成（单个 URL 失败不中断，见 results[].ok / error）
    1  参数错误或无输入
    2  Moli 二进制不存在
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

VERSION = "1.0.0"

DEFAULT_MOLI = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Moli", "bin", "moli.exe")

# 默认允许的图片格式（CDN 无扩展名 URL 始终保留，如 bcebos.com/cmspic/xxx）
DEFAULT_FORMATS = {"jpg", "jpeg", "png", "webp"}

# 反爬 / 挑战页特征（标题命中且无图 → challenge_suspected）
CHALLENGE_RE = re.compile(
    r"(安全检测|安全验证|验证中心|访问限制|访问受限|access denied|just a moment"
    r"|attention required|403 forbidden|ray id|captcha)",
    re.IGNORECASE,
)

# 保守的垃圾图 URL 特征（图标/追踪像素/占位符；og:image 豁免）
JUNK_RE = re.compile(r"(logo|icon|sprite|pixel|beacon|track|spacer|avatar|loading|placeholder)", re.IGNORECASE)

# 页面内执行的提取 JS：滚动触发懒加载 → 收集 og:image / img / srcset → 去重
EXTRACT_JS = r"""new Promise(function (resolve) {
  try { window.scrollTo(0, document.body ? document.body.scrollHeight : 0); } catch (e) {}
  setTimeout(resolve, 900);
}).then(function () {
  function abs(u) { try { return new URL(u, location.href).href; } catch (e) { return u || ''; } }
  var seen = {};
  var out = [];
  function push(src, w, h, alt, origin, loaded) {
    if (!src) return;
    src = abs(src);
    if (!src || src.indexOf('data:') === 0) return;
    if (seen[src]) return;
    seen[src] = 1;
    out.push({ src: src, width: w || 0, height: h || 0,
               alt: (alt || '').slice(0, 120), origin: origin, loaded: !!loaded });
  }
  // 1) og:image / twitter:image / itemprop=image（文章主图，首选）
  var metas = document.querySelectorAll(
    'meta[property^="og:image"], meta[name^="twitter:image"], meta[itemprop="image"]');
  for (var i = 0; i < metas.length; i++) {
    push(metas[i].content, 0, 0, '', 'meta', false);
  }
  // 2) 页面 img 标签（已加载的带真实 naturalWidth/Height）
  var imgs = document.images;
  for (var j = 0; j < imgs.length; j++) {
    var im = imgs[j];
    var src = im.currentSrc || im.src;
    if (src) {
      push(src, im.naturalWidth, im.naturalHeight, im.alt, 'img',
           im.naturalWidth > 0 && im.naturalHeight > 0);
    }
  }
  // 3) srcset 响应式变体（懒加载未触发时常含大图地址，解析 w 描述符）
  var ss = document.querySelectorAll('img[srcset], source[srcset]');
  for (var k = 0; k < ss.length; k++) {
    var parts = (ss[k].getAttribute('srcset') || '').split(',');
    for (var m = 0; m < parts.length; m++) {
      var p = parts[m].trim().split(/\s+/);
      if (p[0]) {
        var wm = (p[1] || '').match(/(\d+)w/);
        push(p[0], wm ? parseInt(wm[1], 10) : 0, 0, '', 'srcset', false);
      }
    }
  }
  return { url: location.href, title: document.title || '', images: out };
});"""


def log(msg):
    """人类可读信息一律走 stderr，保持 stdout 纯 JSON。"""
    print(msg, file=sys.stderr)


def normalize_url(u):
    u = u.strip()
    if not u:
        return ""
    if not re.match(r"^https?://", u, re.IGNORECASE):
        u = "https://" + u
    return u


def url_ext_ok(src, formats):
    """扩展名过滤；无扩展名（CDN 常见）放行。"""
    if formats == "all":
        return True
    m = re.search(r"\.([a-zA-Z0-9]{2,5})(?:[?#]|$)", src)
    if not m:
        return True  # 无扩展名 CDN 地址
    return m.group(1).lower() in formats


def run_moli(url, args, moli_bin):
    """对单个 URL 跑 moli fetch，返回 (data, error)。"""
    cmd = [
        moli_bin, "fetch",
        "--image",
        "--wait", args.wait,
        "-t", str(args.timeout),
        "--eval", EXTRACT_JS,
        url,
    ]
    last_err = ""
    for attempt in range(args.retries + 1):
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=args.timeout / 1000.0 + 30,
            )
        except subprocess.TimeoutExpired:
            last_err = f"moli 执行超时（>{args.timeout / 1000.0 + 30:.0f}s）"
        except Exception as ex:
            last_err = f"moli 启动失败: {ex}"
        else:
            if proc.returncode == 0 and proc.stdout.strip():
                try:
                    return json.loads(proc.stdout), ""
                except json.JSONDecodeError:
                    last_err = "moli 输出非合法 JSON: " + proc.stdout[:200].replace("\n", " ")
            else:
                tail = (proc.stderr.strip() or proc.stdout.strip() or "").replace("\n", " ")
                last_err = f"moli 退出码 {proc.returncode}: {tail[-300:]}"
        if attempt < args.retries:
            log(f"  [retry] {url}（{last_err[:80]}）")
    return None, last_err or "未知错误"


def build_result(url, args, data, error=""):
    """把 moli 原始输出过滤/排序成结构化结果。"""
    if data is None:
        return {"url": url, "ok": False, "title": "", "challenge_suspected": False,
                "images": [], "dropped": 0, "error": error}

    title = (data.get("title") or "").strip()
    kept, dropped = [], 0
    for im in data.get("images") or []:
        src = im.get("src") or ""
        w = int(im.get("width") or 0)
        h = int(im.get("height") or 0)
        origin = im.get("origin") or "img"
        loaded = bool(im.get("loaded"))
        if not src:
            dropped += 1
            continue
        if not url_ext_ok(src, args.formats):
            dropped += 1
            continue
        if origin != "meta" and JUNK_RE.search(src):
            dropped += 1
            continue
        if loaded:
            if w < args.min_width or h < args.min_height:
                dropped += 1
                continue
        elif w and w < args.min_width:
            # srcset 描述符宽度不足
            dropped += 1
            continue
        kept.append({"src": src, "width": w, "height": h,
                     "alt": (im.get("alt") or "").strip(), "origin": origin,
                     "loaded": loaded, "page_url": url})

    # 降噪：已有 >=3 张验证大图时，丢弃未加载且无尺寸的非 meta 候选
    if sum(1 for i in kept if i["loaded"]) >= 3:
        kept = [i for i in kept if i["loaded"] or i["origin"] == "meta" or i["width"] > 0]

    # 排序：已验证优先，其次面积降序，meta 图置顶
    kept.sort(key=lambda x: (0 if x["origin"] == "meta" else 1,
                             0 if x["loaded"] else 1,
                             -(x["width"] * x["height"])))
    kept = kept[: args.max_images]

    challenge = (not kept) and (not title or bool(CHALLENGE_RE.search(title)))
    return {"url": url, "ok": True, "title": title, "challenge_suspected": challenge,
            "images": kept, "dropped": dropped, "error": None}


def collect_urls(args):
    urls = [normalize_url(u) for u in args.urls]
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(normalize_url(line))
    if not urls and not sys.stdin.isatty():
        for line in sys.stdin:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(normalize_url(line))
    seen, out = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Signal Pop 新闻页高清原图探测（Moli 无头浏览器渲染版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例: python tools/fetch_real_images_moli.py --min-width 800 <文章URL>",
    )
    ap.add_argument("urls", nargs="*", help="一个或多个新闻 URL")
    ap.add_argument("--input", "-i", help="URL 列表文件（一行一个，# 注释）")
    ap.add_argument("--min-width", type=int, default=400, help="最小宽度（默认 400）")
    ap.add_argument("--min-height", type=int, default=300, help="最小高度（默认 300）")
    ap.add_argument("--max-images", type=int, default=10, help="每页最多输出几张（默认 10）")
    ap.add_argument("--formats", default="jpg,jpeg,png,webp",
                    help="允许的扩展名，逗号分隔；all=不过滤（默认 jpg,jpeg,png,webp）")
    ap.add_argument("--wait", default="networkidle",
                    choices=["domcontentloaded", "load", "networkidle", "domstable", "done"],
                    help="页面就绪策略（默认 networkidle）")
    ap.add_argument("--timeout", type=int, default=30000, help="就绪超时 ms（默认 30000）")
    ap.add_argument("--retries", type=int, default=1, help="失败重试次数（默认 1）")
    ap.add_argument("--flat", action="store_true",
                    help="扁平输出：合并所有页面图片为单一列表（按 已验证+面积 降序）")
    ap.add_argument("--output", "-o", help="同时写入 JSON 文件")
    ap.add_argument("--moli", default=os.environ.get("MOLI_BIN", DEFAULT_MOLI),
                    help="moli.exe 路径（默认 %%LOCALAPPDATA%%\\Moli\\bin\\moli.exe）")
    args = ap.parse_args()

    if args.formats.strip().lower() == "all":
        args.formats = "all"
    else:
        args.formats = {f.strip().lower().lstrip(".") for f in args.formats.split(",") if f.strip()}

    if not os.path.isfile(args.moli):
        log(f"[fatal] Moli 二进制不存在: {args.moli}")
        log("        请先安装 Moli，或用 --moli / MOLI_BIN 指定路径")
        return 2

    urls = collect_urls(args)
    if not urls:
        log("[fatal] 无输入 URL（位置参数 / --input 文件 / stdin 管道 三选一）")
        return 1

    log(f"[fetch_real_images_moli] {len(urls)} 个 URL，min={args.min_width}x{args.min_height}，"
        f"wait={args.wait}，moli={args.moli}")

    results = []
    for idx, url in enumerate(urls, 1):
        log(f"[{idx}/{len(urls)}] {url}")
        data, err = run_moli(url, args, args.moli)
        res = build_result(url, args, data, err)
        results.append(res)
        if res["ok"]:
            loaded_imgs = [i for i in res["images"] if i["loaded"]]
            top = max(loaded_imgs, key=lambda x: x["width"] * x["height"]) if loaded_imgs else (
                res["images"][0] if res["images"] else None)
            flag = " ⚠️疑似反爬挑战页" if res["challenge_suspected"] else ""
            if top:
                log(f"  -> {len(res['images'])} 张（最大 {top['width']}x{top['height']}，"
                    f"origin={top['origin']}）{flag}")
            else:
                log(f"  -> 0 张合格图（丢弃 {res['dropped']}）{flag}")
        else:
            log(f"  -> 失败: {res['error'][:120]}")

    flat_images = []
    for r in results:
        flat_images.extend(r["images"])
    flat_images.sort(key=lambda x: (0 if x["loaded"] else 1, -(x["width"] * x["height"])))

    ok_n = sum(1 for r in results if r["ok"])
    payload = {
        "tool": "moli_fetch_images",
        "version": VERSION,
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "params": {
            "min_width": args.min_width, "min_height": args.min_height,
            "max_images": args.max_images, "wait": args.wait,
            "formats": "all" if args.formats == "all" else sorted(args.formats),
        },
        "summary": {
            "total_urls": len(results), "ok": ok_n, "failed": len(results) - ok_n,
            "total_images": len(flat_images),
            "challenge_suspected": sum(1 for r in results if r["challenge_suspected"]),
        },
    }
    if args.flat:
        payload["images"] = flat_images
    else:
        payload["results"] = results

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"[output] 已写入 {args.output}")

    s = payload["summary"]
    log(f"[done] {s['ok']}/{s['total_urls']} 页成功，共 {s['total_images']} 张图"
        + (f"，{s['challenge_suspected']} 页疑似反爬" if s["challenge_suspected"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
