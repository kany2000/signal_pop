#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signal Pop · 预取 whisperX 中文强制对齐模型（分片并行 + 断点续传）

本机 huggingface.co 直连不通，10808 代理单连接 ~370KB/s；
实测 24 线程 Range 并发 ~1.1MB/s。用分片下载把 1.2GB 模型拉到本地目录，
之后 whisperX 的 load_align_model(..., model_name=<本地目录>) 完全离线加载。
"""
import concurrent.futures as F
import json
import os
import sys
import time
import urllib.request as U

REPO = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
BASE = f"https://huggingface.co/{REPO}/resolve/main/"
API = f"https://huggingface.co/api/models/{REPO}/tree/main?recursive=true"
PROXY = {"http": "http://127.0.0.1:10808", "https": "http://127.0.0.1:10808"}
OUT = os.path.join("G:", os.sep, "temp", "signal_pop_models", "wav2vec2-zh-cn")
SMALL_FILES = ["config.json", "preprocessor_config.json", "vocab.json",
               "special_tokens_map.json", "tokenizer_config.json"]
CHUNK = 8 * 1024 * 1024
WORKERS = 24

OPENER = U.build_opener(U.ProxyHandler(PROXY))


def fetch(url, headers=None, timeout=60):
    req = U.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with OPENER.open(req, timeout=timeout) as r:
        return r.read()


def get_size():
    data = json.loads(fetch(API, timeout=40).decode("utf-8"))
    for item in data:
        if item.get("path") == "pytorch_model.bin":
            return int(item["size"])
    raise RuntimeError("pytorch_model.bin not found in model tree")


def small_files():
    for name in SMALL_FILES:
        dst = os.path.join(OUT, name)
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            print(f"[small] {name} cached", flush=True)
            continue
        try:
            blob = fetch(BASE + name, timeout=60)
        except Exception as e:
            print(f"[small] {name} unavailable ({e})", flush=True)
            continue
        with open(dst, "wb") as f:
            f.write(blob)
        print(f"[small] {name} {len(blob)}B", flush=True)


def one_part(args):
    idx, start, end, total = args
    pdir = os.path.join(OUT, "_parts")
    dst = os.path.join(pdir, f"{idx:05d}.part")
    expect = end - start + 1
    if os.path.exists(dst) and os.path.getsize(dst) == expect:
        return idx, expect, "cached"
    last = None
    for attempt in range(4):
        try:
            blob = fetch(BASE + "pytorch_model.bin",
                         headers={"Range": f"bytes={start}-{end}", "User-Agent": "Mozilla/5.0"},
                         timeout=120)
            if len(blob) != expect:
                raise IOError(f"short read {len(blob)} != {expect}")
            tmp = dst + ".tmp"
            with open(tmp, "wb") as f:
                f.write(blob)
            os.replace(tmp, dst)
            return idx, expect, "ok"
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    return idx, 0, f"FAIL: {last}"


def main():
    os.makedirs(os.path.join(OUT, "_parts"), exist_ok=True)
    print(f"[model] {REPO} -> {OUT}", flush=True)
    small_files()
    total = get_size()
    print(f"[model] pytorch_model.bin {total/1048576:.1f}MB", flush=True)
    jobs = []
    for i, start in enumerate(range(0, total, CHUNK)):
        jobs.append((i, start, min(start + CHUNK, total) - 1, total))
    print(f"[model] {len(jobs)} chunks x {CHUNK//1048576}MB / {WORKERS} workers", flush=True)
    t0 = time.time()
    done_bytes, failed = 0, []
    with F.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for n, (idx, size, status) in enumerate(ex.map(one_part, jobs), 1):
            done_bytes += size
            if status.startswith("FAIL"):
                failed.append((idx, status))
            if n % 12 == 0 or status.startswith("FAIL"):
                el = time.time() - t0
                print(f"[model] {n}/{len(jobs)} {done_bytes/1048576:.0f}MB "
                      f"{done_bytes/el/1048576:.2f}MB/s {status}", flush=True)
    if failed:
        print(f"[model] FAILED chunks: {failed[:5]} ... ({len(failed)})", flush=True)
        return 1
    out_bin = os.path.join(OUT, "pytorch_model.bin")
    with open(out_bin, "wb") as w:
        for idx, *_ in jobs:
            with open(os.path.join(OUT, "_parts", f"{idx:05d}.part"), "rb") as f:
                w.write(f.read())
    size = os.path.getsize(out_bin)
    print(f"[model] assembled {size/1048576:.1f}MB in {time.time()-t0:.1f}s", flush=True)
    if size != total:
        print("[model] SIZE MISMATCH", flush=True)
        return 1
    # 校验通过后清掉分片，保持清爽
    for idx, *_ in jobs:
        os.remove(os.path.join(OUT, "_parts", f"{idx:05d}.part"))
    os.rmdir(os.path.join(OUT, "_parts"))
    print("[model] DONE (offline-ready)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
