#!/usr/bin/env python3
"""
Signal Pop 批量生图脚本
从 visual_prompts_*.json 读取 prompt → Pollinations.ai 免费 API → 存到 tools/images/

用法:
  python3 batch_gen_images.py                     # 用今天日期
  python3 batch_gen_images.py 20260620            # 指定日期
  python3 batch_gen_images.py /path/to/visual_prompts.json
"""
import requests, json, sys, time, re
from pathlib import Path
from datetime import datetime

# ── 配置 ──
API_URL = "https://image.pollinations.ai/prompt"
IMAGES_DIR = Path("/home/kan/signal_pop/tools/images")
PROJECT_DIR = Path("/home/kan/signal_pop/daily")  # 默认 daily, 也可用 weekly

# ── 工具 ──

def find_prompts_file(date_or_path):
    """根据输入找到 visual_prompts 文件"""
    p = Path(date_or_path)
    if p.exists() and p.is_file():
        return p
    # 尝试 daily 目录
    for base in [PROJECT_DIR, Path("/home/kan/signal_pop/weekly")]:
        fp = base / "data" / f"visual_prompts_{date_or_path}.json"
        if fp.exists():
            return fp
    # 自动找最新的
    files = sorted(Path("/home/kan/signal_pop/daily/data").glob("visual_prompts_*.json"), reverse=True)
    if files:
        return files[0]
    raise FileNotFoundError(f"找不到 visual_prompts 文件: {date_or_path}")

def short_prompt(item, max_len=250):
    """从 prompt 或 title 缩略出适合 API 的文本"""
    raw = item.get("prompt") or f"{item.get('title','')} concept art, cinematic lighting, broadcast quality, 16:9"
    # 缩短但保留关键视觉描述
    raw = raw.replace("Commercial Tech Photography, sleek minimalist aesthetic, ", "")
    raw = raw.replace(", Cinematic volumetric lighting, cyberblue and white color grade, Center focus, hero shot, shot on 35mm lens, 8k resolution --ar 16:9", "")
    # URL 编码前截取避免太长
    return raw[:max_len]

def download_with_retry(url, out_path, max_retries=5):
    """下载图片，带限流重试"""
    headers = {"User-Agent": "Mozilla/5.0"}
    wait = 2
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, timeout=90)
            if r.status_code == 200 and len(r.content) > 2000:
                out_path.write_bytes(r.content)
                return True
            elif r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", wait))
                print(f"  429 限流, 等 {retry_after}s...")
                time.sleep(retry_after)
                wait *= 2
            else:
                print(f"  HTTP {r.status_code}, 重试 {attempt+1}/{max_retries}...")
                time.sleep(wait)
                wait *= 1.5
        except requests.exceptions.Timeout:
            print(f"  超时, 重试 {attempt+1}/{max_retries}...")
            time.sleep(wait)
            wait *= 2
        except Exception as e:
            print(f"  错误: {e}, 重试 {attempt+1}/{max_retries}...")
            time.sleep(wait)
    return False

def main():
    # 解析参数
    arg = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d")

    prompts_file = find_prompts_file(arg)
    print(f"[源文件] {prompts_file}")

    with open(prompts_file) as f:
        prompts = json.load(f)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    ok, fail = 0, 0
    for item in prompts:
        # 文件名
        seg_id = item.get("id") or str(item.get("index"))
        title = item.get("title", "untitled")[:40]
        out_path = IMAGES_DIR / f"{seg_id}.jpg"

        if out_path.exists():
            print(f"[跳过] {seg_id} ({title}) 已有")
            ok += 1
            continue

        # 构建 prompt URL
        sp = short_prompt(item)
        url = f"{API_URL}/{requests.utils.quote(sp)}&nologo=true"
        print(f"[生成] {seg_id} ({title})...", end=" ", flush=True)

        if download_with_retry(url, out_path):
            kb = out_path.stat().st_size // 1024
            print(f"✓ {kb}KB")
            ok += 1
        else:
            print("✗ 失败")
            fail += 1

        # 限流保护：每张间隔 1.5s
        if item != prompts[-1]:
            time.sleep(1.5)

    print(f"\n完成: {ok} 成功, {fail} 失败 → {IMAGES_DIR}")

if __name__ == "__main__":
    main()
